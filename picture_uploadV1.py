import flet as ft
from datetime import datetime

# --- GLOBÁLIS ADATTÁROLÁS ---
# (Memóriában tárolt lista, újraindításkor törlődik)
GALLERY_DATA = []

def main(page: ft.Page):
    page.title = "Növény Galéria Napló (+Törlés)"
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT

    # --- 1. A Galéria tároló (GridView) ---
    gallery_grid = ft.GridView(
        expand=True,
        runs_count=3,
        max_extent=300,
        child_aspect_ratio=0.8,
        spacing=20,
        run_spacing=20,
    )

    # --- ÚJ RÉSZ: Törlő függvény ---
    # Ez a függvény kapja meg azt az 'item' szótárat, amit törölni kell.
    def delete_image(item_to_delete):
        # Megnézzük, benne van-e még a listában (biztonság kedvéért)
        if item_to_delete in GALLERY_DATA:
            # Eltávolítjuk a listából
            GALLERY_DATA.remove(item_to_delete)
            
            # Frissítjük a felületet, hogy eltűnjön a kártya
            update_gallery_ui()
            
            # Visszajelzés a felhasználónak
            page.snack_bar = ft.SnackBar(ft.Text("Kép törölve!"), bgcolor=ft.Colors.RED_700)
            page.snack_bar.open = True
            page.update()


    # --- 2. Segédfüggvény a galéria frissítéséhez ---
    def update_gallery_ui():
        gallery_grid.controls.clear()
        
        # Végigmegyünk az adatokon
        for item in GALLERY_DATA:
            path = item["path"]
            date_str = item["date"]

            # --- MÓDOSÍTÁS: Kártya lábléc (Dátum + Törlés gomb) ---
            
            # 1. Létrehozzuk a dátum szöveget
            date_text = ft.Text(date_str, size=12, color=ft.Colors.GREY_700, weight="bold")
            
            # 2. Létrehozzuk a törlés gombot (kuka ikon)
            # FONTOS: A lambda függvénynél a `current_item=item` rögzíti, 
            # hogy EZ a gomb EHHEZ a konkrét képhez tartozik.
            delete_btn = ft.IconButton(
                icon=ft.Icons.DELETE_OUTLINE,
                icon_color=ft.Colors.RED_400,
                tooltip="Kép törlése",
                on_click=lambda e, current_item=item: delete_image(current_item)
            )

            # 3. Egy sorba rendezzük őket (Dátum balra, kuka jobbra)
            footer_row = ft.Row(
                [date_text, delete_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN, # Széthúzzuk őket
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            )


            # --- A teljes kártya összeállítása ---
            gallery_item = ft.Card(
                elevation=4,
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        # Kép
                        ft.Image(
                            src=path,
                            width=float("inf"),
                            height=200,
                            fit=ft.ImageFit.COVER,
                            border_radius=8
                        ),
                        # Lábléc (Dátum és Törlés gomb)
                        ft.Container(
                            content=footer_row,
                            padding=ft.padding.only(top=5)
                        )
                    ], spacing=5)
                )
            )
            gallery_grid.controls.append(gallery_item)
        
        # Üres állapot kezelése
        if not GALLERY_DATA:
            gallery_grid.controls.append(
                 ft.Container(content=ft.Text("Még nincsenek feltöltött képek.", color=ft.Colors.GREY_400), alignment=ft.alignment.center, padding=50)
            )

        page.update()


    # --- 3. FilePicker és a feltöltés logikája (Változatlan) ---
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            now = datetime.now()
            formatted_date = now.strftime("%Y-%m-%d %H:%M")
            
            # Új adat beszúrása az elejére
            GALLERY_DATA.insert(0, {"path": file_path, "date": formatted_date})
            
            update_gallery_ui()
            
            page.snack_bar = ft.SnackBar(ft.Text(f"Kép sikeresen hozzáadva!"), bgcolor=ft.Colors.GREEN_700)
            page.snack_bar.open = True
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # Feltöltés gomb
    upload_btn = ft.ElevatedButton(
        "Új fotó",
        icon=ft.Icons.ADD_A_PHOTO,
        style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10), bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE),
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
    )

    # --- 4. Az oldal összeállítása ---
    header = ft.Text("🌱 Növény Napló", size=24, weight="bold", color=ft.Colors.GREEN_800)

    page.add(
        ft.Column([
            ft.Row([header, upload_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(),
            gallery_grid
        ], expand=True)
    )

    # Inicializálás
    update_gallery_ui()

ft.app(target=main)