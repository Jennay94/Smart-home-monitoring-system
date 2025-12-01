import flet as ft
from datetime import datetime
import aiohttp # Szükséges az API híváshoz
import asyncio
import json

# --- KONFIGURÁCIÓ ---
# FIGYELEM: Cseréld le ezt a saját, ÚJ generált kulcsodra!
# A kulcs formátuma alapján ez OpenRouter kulcsnak tűnik.
API_KEY = "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"
# OpenRouter endpoint (DeepSeek modellt használva)
API_URL = "https://openrouter.ai/api/v1/chat/completions"
# A használni kívánt modell neve OpenRouteren keresztül
MODEL_NAME = "deepseek/deepseek-chat"

# --- GLOBÁLIS ADATTÁROLÁS (Galéria) ---
GALLERY_DATA = []

# --- GLOBÁLIS ADATTÁROLÁS (Chat előzmények az API-nak) ---
# Ez tárolja a beszélgetés kontextust {"role": "user/assistant", "content": "..."} formában
chat_history_for_api = [
    {"role": "system", "content": "You are a helpful assistant in a smart home monitor application."}
]


def main(page: ft.Page):
    page.title = "Okosotthon Dashboard + AI Chat"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT

    # ==============================================================================
    # --- 1. FÜL: NÖVÉNY GALÉRIA (A korábbi kód) ---
    # ==============================================================================
    gallery_grid = ft.GridView(
        expand=True, runs_count=3, max_extent=300, child_aspect_ratio=0.8, spacing=20, run_spacing=20,
    )

    def delete_image(item_to_delete):
        if item_to_delete in GALLERY_DATA:
            GALLERY_DATA.remove(item_to_delete)
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Kép törölve!"), bgcolor=ft.Colors.RED_700))

    def update_gallery_ui():
        gallery_grid.controls.clear()
        for item in GALLERY_DATA:
            path = item["path"]
            date_str = item["date"]
            
            date_text = ft.Text(date_str, size=12, color=ft.Colors.GREY_700, weight="bold")
            delete_btn = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, tooltip="Kép törlése",
                on_click=lambda e, current_item=item: delete_image(current_item)
            )
            footer_row = ft.Row([date_text, delete_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)

            gallery_item = ft.Card(
                elevation=4,
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Image(src=path, width=float("inf"), height=200, fit=ft.ImageFit.COVER, border_radius=8),
                        ft.Container(content=footer_row, padding=ft.padding.only(top=5))
                    ], spacing=5)
                )
            )
            gallery_grid.controls.append(gallery_item)
        
        if not GALLERY_DATA:
            gallery_grid.controls.append(ft.Container(content=ft.Text("Még nincsenek feltöltött képek.", color=ft.Colors.GREY_400), alignment=ft.alignment.center, padding=50))
        page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            GALLERY_DATA.insert(0, {"path": file_path, "date": formatted_date})
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Kép sikeresen hozzáadva!"), bgcolor=ft.Colors.GREEN_700))

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    upload_btn = ft.ElevatedButton(
        "Új fotó", icon=ft.Icons.ADD_A_PHOTO,
        style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10), bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
    )

    gallery_tab_content = ft.Column([
        ft.Row([ft.Text("🌱 Növény Napló", size=24, weight="bold", color=ft.Colors.GREEN_800), upload_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        gallery_grid
    ], expand=True)


    # ==============================================================================
    # --- 2. FÜL: AI CHATBOX (Új funkció) ---
    # ==============================================================================
    
    # Konténer az üzenetek megjelenítésére (görgethető)
    chat_messages_list = ft.ListView(
        expand=True,
        spacing=10,
        padding=10,
        auto_scroll=True, # Mindig az aljára görget új üzenetnél
    )

    # Beviteli mező
    chat_input = ft.TextField(
        hint_text="Írj valamit az AI-nak...",
        expand=True,
        border_radius=20,
        # JAVÍTÁS: bg_color helyett bgcolor
        bgcolor=ft.Colors.WHITE,
        on_submit=lambda e: send_message_click(e) # Enter lenyomására is küld
    )

    # Küldés gomb
    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=ft.Colors.BLUE_600,
        tooltip="Küldés",
        on_click=lambda e: send_message_click(e)
    )

    # Segédfüggvény: Egy üzenet buborék létrehozása a UI-on
    def create_message_bubble(text, is_user):
        return ft.Row(
            alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START,
            controls=[
                ft.Container(
                    content=ft.Text(text, color=ft.Colors.WHITE if is_user else ft.Colors.BLACK),
                    padding=15,
                    border_radius=ft.border_radius.only(
                        top_left=15, top_right=15,
                        bottom_left=15 if is_user else 0,
                        bottom_right=0 if is_user else 15
                    ),
                    bgcolor=ft.Colors.BLUE_600 if is_user else ft.Colors.GREY_200,
                    width=page.width * 0.7, # Max szélesség
                )
            ]
        )

    # ASZINKRON Függvény: Kommunikáció az API-val
    async def get_ai_response_async(prompt):
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            # OpenRouter specifikus headerek (opcionális, de ajánlott)
            "HTTP-Referer": "https://flet.dev", 
            "X-Title": "Flet Smart Home App",
        }
        
        # Hozzáadjuk a felhasználó új üzenetét az API előzményekhez
        chat_history_for_api.append({"role": "user", "content": prompt})

        payload = {
            "model": MODEL_NAME,
            "messages": chat_history_for_api,
            "temperature": 0.7, # Kreativitás mértéke
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Kinyerjük a választ a JSON-ból
                        ai_message_content = data['choices'][0]['message']['content']
                        # Hozzáadjuk az AI válaszát is az előzményekhez
                        chat_history_for_api.append({"role": "assistant", "content": ai_message_content})
                        return ai_message_content
                    else:
                        error_text = await response.text()
                        return f"Hiba az API hívásnál: {response.status} - {error_text}"
        except Exception as e:
            return f"Kapcsolódási hiba: {str(e)}"


    # A küldés gomb eseménykezelője
    def send_message_click(e):
        user_message = chat_input.value
        if not user_message: return

        # 1. Felhasználó üzenetének megjelenítése
        chat_messages_list.controls.append(create_message_bubble(user_message, is_user=True))
        chat_input.value = "" #Input törlése
        chat_input.disabled = True # Input tiltása amíg várunk
        send_button.disabled = True
        page.update()

        # 2. "Ír éppen..." indikátor (opcionális)
        typing_indicator = ft.Text("Az AI gondolkodik...", italic=True, color=ft.Colors.GREY_500)
        chat_messages_list.controls.append(typing_indicator)
        page.update()

        # 3. Aszinkron feladat indítása az API híváshoz
        async def process_ai_response():
            response_text = await get_ai_response_async(user_message)
            
            # Indikátor eltávolítása
            chat_messages_list.controls.remove(typing_indicator)
            
            # AI válasz megjelenítése
            chat_messages_list.controls.append(create_message_bubble(response_text, is_user=False))
            
            # Input visszakapcsolása
            chat_input.disabled = False
            send_button.disabled = False
            chat_input.focus()
            page.update()

        # Flet aszinkron feladatfuttatója
        page.run_task(process_ai_response)

    # A Chat fül teljes tartalma
    chat_tab_content = ft.Column(
        controls=[
            ft.Text("💬 DeepSeek AI Chat", size=24, weight="bold", color=ft.Colors.BLUE_800),
            ft.Divider(),
            ft.Container( # A chat ablak kerete
                content=chat_messages_list,
                expand=True,
                bgcolor=ft.Colors.GREY_50,
                border_radius=10,
                border=ft.border.all(1, ft.Colors.GREY_200),
            ),
            ft.Row([chat_input, send_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ],
        expand=True,
    )


    # ==============================================================================
    # --- FŐ ELRENDEZÉS (TABS) ---
    # ==============================================================================
    
    # Kezdeti üdvözlő üzenet a chaten
    chat_messages_list.controls.append(create_message_bubble("Szia! Én vagyok az okosotthonod AI asszisztense. Miben segíthetek?", is_user=False))

    # Fülek létrehozása
    tabs = ft.Tabs(
        selected_index=0, # Melyik fül legyen aktív induláskor
        animation_duration=300,
        tabs=[
            ft.Tab(
                text="Növény Napló",
                icon=ft.Icons.IMAGE,
                content=ft.Container(content=gallery_tab_content, padding=10)
            ),
            ft.Tab(
                text="AI Chat",
                icon=ft.Icons.CHAT_BUBBLE,
                content=ft.Container(content=chat_tab_content, padding=10)
            ),
        ],
        expand=True,
    )

    # Inicializálás
    update_gallery_ui()
    page.add(tabs)

ft.app(target=main)