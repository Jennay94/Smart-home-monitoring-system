import flet as ft
from datetime import datetime
import aiohttp
from config import *
import state

def extras_view(page: ft.Page):
    
    # --- Tab 1: Gallery ---
    gallery_grid = ft.GridView(expand=True, runs_count=3, max_extent=300, child_aspect_ratio=0.8, spacing=20, run_spacing=20)

    def delete_image(item):
        if item in state.GALLERY_DATA:
            state.GALLERY_DATA.remove(item)
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Image deleted!"), bgcolor=COLOR_DANGER))

    def update_gallery_ui():
        gallery_grid.controls.clear()
        for item in state.GALLERY_DATA:
            date_text = ft.Text(item["date"], size=12, color=TEXT_SECONDARY)
            delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLOR_DANGER, tooltip="Delete", on_click=lambda e, i=item: delete_image(i))
            footer = ft.Row([date_text, delete_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
            card = ft.Card(elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
                content=ft.Container(padding=10, content=ft.Column([
                        ft.Image(src=item["path"], width=float("inf"), height=180, fit=ft.ImageFit.COVER, border_radius=12),
                        ft.Container(content=footer, padding=ft.padding.only(top=5, left=5, right=5))
                    ], spacing=5)))
            gallery_grid.controls.append(card)
        if not state.GALLERY_DATA:
            gallery_grid.controls.append(ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=48, color=TEXT_SECONDARY),
                ft.Text("No images uploaded yet.", color=TEXT_SECONDARY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, padding=50))
        if page: page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            state.GALLERY_DATA.insert(0, {"path": e.files[0].path, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Image added successfully!"), bgcolor=COLOR_SUCCESS))

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    upload_btn = ft.ElevatedButton("Upload New Photo", icon=ft.Icons.ADD_A_PHOTO, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=12), bgcolor=COLOR_HUM, color=ft.Colors.WHITE), on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE))

    gallery_tab = ft.Column([ft.Row([ft.Text("Gallery", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), upload_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(height=20), gallery_grid], expand=True)

    # --- Tab 2: AI Chat ---
    chat_list = ft.ListView(expand=True, spacing=15, padding=20, auto_scroll=True)
    chat_input = ft.TextField(hint_text="Type a message...", hint_style=ft.TextStyle(color=TEXT_SECONDARY), text_style=ft.TextStyle(color=TEXT_PRIMARY), expand=True, border_radius=25, bgcolor=BG_COLOR, border_color="transparent", focused_border_color=COLOR_HUM, content_padding=ft.padding.symmetric(horizontal=20, vertical=15), on_submit=lambda e: send_msg(e))
    send_btn = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_HUM, bgcolor=BG_COLOR, tooltip="Send", on_click=lambda e: send_msg(e))

    def create_bubble(text, is_user):
        bg = COLOR_HUM if is_user else "#E0E0E0"
        fg = ft.Colors.WHITE if is_user else TEXT_PRIMARY
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        radius = ft.border_radius.only(top_left=18, top_right=18, bottom_left=5 if is_user else 18, bottom_right=18 if is_user else 5)
        return ft.Row([ft.Container(content=ft.Text(text, color=fg, size=14), padding=ft.padding.symmetric(horizontal=16, vertical=12), border_radius=radius, bgcolor=bg, width=page.width*0.65 if len(text)>50 else None)], alignment=align)

    async def get_ai_response(prompt):
        state.chat_history_for_api.append({"role": "user", "content": prompt})
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json={"model": MODEL_NAME, "messages": state.chat_history_for_api, "temperature": 0.7}) as resp:
                    if resp.status == 200:
                        data = await resp.json(); content = data['choices'][0]['message']['content']
                        state.chat_history_for_api.append({"role": "assistant", "content": content})
                        return content
                    return f"Error: {resp.status} - {await resp.text()}"
        except Exception as e: return f"Error: {e}"

    def send_msg(e):
        msg = chat_input.value
        if not msg: return
        chat_list.controls.append(create_bubble(msg, True))
        chat_input.value = ""; chat_input.disabled = True; send_btn.disabled = True; page.update()
        indicator = ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2, color=COLOR_HUM), ft.Text("AI is thinking...", color=TEXT_SECONDARY, size=12)], spacing=10)
        chat_list.controls.append(indicator); page.update()
        async def process():
            resp = await get_ai_response(msg)
            chat_list.controls.remove(indicator)
            chat_list.controls.append(create_bubble(resp, False))
            chat_input.disabled = False; send_btn.disabled = False; chat_input.focus(); page.update()
        page.run_task(process)

    if not chat_list.controls: chat_list.controls.append(create_bubble("Hello! How can I help you with your smart home?", False))
    
    chat_tab = ft.Column([ft.Text("AI Assistant", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), ft.Container(height=10), ft.Card(elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS), expand=True, content=ft.Container(content=chat_list, padding=0)), ft.Container(height=10), ft.Row([chat_input, send_btn], spacing=10)], expand=True)

    tabs = ft.Tabs(selected_index=0, animation_duration=300, indicator_color=COLOR_HUM, label_color=COLOR_HUM, unselected_label_color=TEXT_SECONDARY, divider_color="transparent", tabs=[ft.Tab(text="Gallery", icon=ft.Icons.PHOTO_LIBRARY_OUTLINED, content=ft.Container(content=gallery_tab, padding=ft.padding.only(top=20))), ft.Tab(text="AI Chat", icon=ft.Icons.CHAT_BUBBLE_OUTLINE, content=ft.Container(content=chat_tab, padding=ft.padding.only(top=20)))], expand=True)
    header = ft.Row([ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY, on_click=lambda _: page.go("/")), ft.Text("Extras", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)], alignment=ft.MainAxisAlignment.START)
    
    update_gallery_ui()
    return ft.View(route="/extras", controls=[ft.Column([header, ft.Container(height=10), tabs], expand=True)], bgcolor=BG_COLOR, padding=SECTION_PADDING)