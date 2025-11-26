import flet as ft
from datetime import datetime
import random
import time
import threading
import aiohttp
import asyncio
import json

# ==============================================================================
# --- GLOBÁLIS KONFIGURÁCIÓ ÉS ADATOK ---
# ==============================================================================

# --- AI CHAT KONFIGURÁCIÓ ---
# FIGYELEM: CSERÉLD LE A SAJÁT ÚJ KULCSODRA!
API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

# --- GLOBÁLIS ADATTÁROLÁS (Galéria) ---
GALLERY_DATA = []

# --- GLOBÁLIS ADATTÁROLÁS (Chat előzmények) ---
chat_history_for_api = [
    {"role": "system", "content": "You are a helpful assistant in a smart home monitor application."}
]

# --- SZENZOR SZIMULÁCIÓ ÁLLAPOT ---
simulation_running = False
simulation_thread = None

# ==============================================================================
# --- 1. OLDAL: FŐOLDAL (Smart Home Controller) ---
# ==============================================================================
def home_view(page: ft.Page):
    bgcolor = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"

    # --- Eseménykezelők ---
    def on_light_click(e):
        if light_button.text == "Turn ON":
            light_status.value = "Status: ON"; light_status.color = ft.Colors.GREEN
            light_button.text = "Turn OFF"; light_button.bgcolor = "#FF6B6B"
            light_card.bgcolor = "#4ECDC4"; light_icon.content = ft.Text("💡", size=28)
        else:
            light_status.value = "Status: OFF"; light_status.color = ft.Colors.RED
            light_button.text = "Turn ON"; light_button.bgcolor = "#4ECDC4"
            light_card.bgcolor = "#FFD93D"; light_icon.content = ft.Text("💡", size=28)
        page.update()

    def on_door_click(e):
        if door_button.text == "Unlock":
            door_status.value = "Door: UNLOCKED"; door_status.color = ft.Colors.GREEN
            door_button.text = "Lock"; door_button.bgcolor = "#FF6B6B"
            door_icon.content = ft.Text("🚪", size=28)
        else:
            door_status.value = "Door: LOCKED"; door_status.color = ft.Colors.RED
            door_button.text = "Unlock"; door_button.bgcolor = "#4ECDC4"
            door_icon.content = ft.Text("🔒", size=28)
        page.update()

    def on_fan_click(e):
        if fan_button.text == "Turn ON":
            fan_status.value = "Status: ON"; fan_status.color = ft.Colors.GREEN
            fan_button.text = "Turn OFF"; fan_button.bgcolor = "#FF6B6B"
            fan_icon.content = ft.Text("🌀", size=28)
        else:
            fan_status.value = "Status: OFF"; fan_status.color = ft.Colors.RED
            fan_button.text = "Turn ON"; fan_button.bgcolor = "#4ECDC4"
            fan_icon.content = ft.Text("💨", size=28)
        page.update()

    def on_rain_click(e):
        if rain_button.text == "Set YES":
            rain_status.value = "Rain: YES"; rain_status.color = "#4ECDC4"
            rain_button.text = "Set NO"; rain_button.bgcolor = "#FFD93D"
            rain_icon.content = ft.Text("🌧️", size=28)
        else:
            rain_status.value = "Rain: NO"; rain_status.color = "#FFD93D"
            rain_button.text = "Set YES"; rain_button.bgcolor = "#4ECDC4"
            rain_icon.content = ft.Text("☀️", size=28)
        page.update()

    def on_window_click(e):
        if window_button.text == "Open":
            window_status.value = "Window: OPEN"; window_status.color = ft.Colors.GREEN
            window_button.text = "Close"; window_button.bgcolor = "#FF6B6B"
            window_icon.content = ft.Text("🪟", size=28)
        else:
            window_status.value = "Window: CLOSED"; window_status.color = ft.Colors.RED
            window_button.text = "Open"; window_button.bgcolor = "#4ECDC4"
            window_icon.content = ft.Text("🚫", size=28)
        page.update()

    # --- Kártya létrehozó függvények ---
    def create_sensor_card(title, value, unit, value_color, icon, bg_color, details, width=280, height=200):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(icon, size=24), width=45, height=45, bgcolor=ft.Colors.WHITE, border_radius=10, alignment=ft.alignment.center),
                    ft.Column([ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text("Real-time sensor", size=10, color=ft.Colors.WHITE70)], spacing=2),
                ], spacing=12),
                ft.Container(content=ft.Column([ft.Text(value, size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text(unit, size=14, color=ft.Colors.WHITE70)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, margin=ft.margin.only(top=10, bottom=10)),
                ft.Container(content=ft.Column([ft.Text("Sensor Details", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text(details, size=10, color=ft.Colors.WHITE70)]), bgcolor=ft.Colors.WHITE24, padding=8, border_radius=8),
            ]), bgcolor=bg_color, padding=15, border_radius=20, width=width, height=height,
        )

    def create_interactive_card(title, status, status_color, icon, bg_color, description, button, width=280, height=200):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(icon, size=24), width=45, height=45, bgcolor=ft.Colors.WHITE, border_radius=10, alignment=ft.alignment.center),
                    ft.Column([ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text("Smart device", size=10, color=ft.Colors.WHITE70)], spacing=2),
                ], spacing=12),
                ft.Column([ft.Text(status, size=18, weight=ft.FontWeight.BOLD, color=status_color), ft.Text(description, size=12, color=ft.Colors.WHITE70)], spacing=5),
                ft.Container(content=button, alignment=ft.alignment.center, margin=ft.margin.only(top=10)),
                ft.Container(content=ft.Row([ft.Text("🔄 Auto", size=10, color=ft.Colors.WHITE70), ft.Text("⚡ Low Power", size=10, color=ft.Colors.WHITE70), ft.Text("📱 Connected", size=10, color=ft.Colors.WHITE70)], spacing=8), alignment=ft.alignment.center),
            ]), bgcolor=bg_color, padding=15, border_radius=20, width=width, height=height,
        )

    # --- Navigációs gombok ---
    go_to_sensors_btn = ft.ElevatedButton("Go to Sensors 📊", on_click=lambda _: page.go("/sensors"), style=ft.ButtonStyle(color=ft.Colors.BLUE_900, bgcolor=ft.Colors.WHITE, padding=20))
    go_to_extras_btn = ft.ElevatedButton("Go to Extras (Chat/Galéria) 🤖", on_click=lambda _: page.go("/extras"), style=ft.ButtonStyle(color=ft.Colors.PURPLE_900, bgcolor=ft.Colors.WHITE, padding=20))

    header = ft.Container(
        content=ft.Column([
            ft.Text("🏠 Smart Home Dashboard", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("Real-time monitoring & control system", size=14, color=ft.Colors.WHITE70),
            ft.Container(height=20),
            ft.Row([go_to_sensors_btn, go_to_extras_btn], spacing=20, alignment=ft.MainAxisAlignment.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=30),
    )

    # --- Kártyák ---
    temp_card = create_sensor_card("Temperature", "22.5", "°C", ft.Colors.WHITE, "🌡️", "#FF6B6B", "DHT22 Sensor\nRange: -40°C to 80°C")
    humidity_card = create_sensor_card("Humidity", "45", "% RH", ft.Colors.WHITE, "💧", "#4ECDC4", "DHT22 Sensor\nRange: 0-100% RH")

    light_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    light_button = ft.ElevatedButton("Turn ON", on_click=on_light_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN, padding=15, shape=ft.RoundedRectangleBorder(radius=12)), width=120)
    light_icon = ft.Container(content=ft.Text("💡", size=24), width=45, height=45, bgcolor=ft.Colors.WHITE, border_radius=10, alignment=ft.alignment.center)
    light_card = create_interactive_card("Light", "650 Lux", ft.Colors.AMBER, "💡", "#FFD93D", "BH1750 Light Sensor", light_button)

    fan_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    fan_button = ft.ElevatedButton("Turn ON", on_click=on_fan_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN, padding=15, shape=ft.RoundedRectangleBorder(radius=12)), width=120)
    fan_icon = ft.Container(content=ft.Text("💨", size=24), width=45, height=45, bgcolor=ft.Colors.WHITE, border_radius=10, alignment=ft.alignment.center)
    fan_card = create_interactive_card("Fan", "Status: OFF", ft.Colors.RED, "💨", "#FF9FF3", "DC Motor Fan Control", fan_button)

    rain_status = ft.Text("Rain: NO", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE)
    rain_button = ft.ElevatedButton("Set YES", on_click=on_rain_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE, padding=15, shape=ft.RoundedRectangleBorder(radius=12)), width=120)
    rain_icon = ft.Container(content=ft.Text("☀️", size=24), width=45, height=45, bgcolor=ft.Colors.WHITE, border_radius=10, alignment=ft.alignment.center)
    rain_card = create_interactive_card("Rain Detection", "Rain: NO", ft.Colors.ORANGE, "☀️", "#54A0FF", "Rain Sensor Module", rain_button)

    window_status = ft.Text("Window: CLOSED", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    window_button = ft.ElevatedButton("Open", on_click=on_window_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN, padding=15, shape=ft.RoundedRectangleBorder(radius=12)), width=120)
    window_icon = ft.Container(content=ft.Text("🚫", size=24), width=45, height=45, bgcolor=ft.Colors.WHITE, border_radius=10, alignment=ft.alignment.center)
    window_card = create_interactive_card("Window", "Window: CLOSED", ft.Colors.RED, "🚫", "#FF9F43", "Smart Window Controller", window_button)

    door_status = ft.Text("Door: LOCKED", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    door_button = ft.ElevatedButton("Unlock", on_click=on_door_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.BLUE, padding=15, shape=ft.RoundedRectangleBorder(radius=12)), width=120)
    door_icon = ft.Container(content=ft.Text("🔒", size=24), width=45, height=45, bgcolor=ft.Colors.WHITE, border_radius=10, alignment=ft.alignment.center)
    door_card = create_interactive_card("Front Door", "Door: LOCKED", ft.Colors.RED, "🔒", "#48DBFB", "Smart Lock System", door_button)

    # --- Elrendezés ---
    first_row = ft.Row([temp_card, humidity_card, light_card], spacing=20, wrap=True, alignment=ft.MainAxisAlignment.SPACE_EVENLY)
    second_row = ft.Row([fan_card, rain_card, window_card, door_card], spacing=20, wrap=True, alignment=ft.MainAxisAlignment.SPACE_EVENLY)

    content_column = ft.Column([header, ft.Container(height=10), first_row, ft.Container(height=20), second_row], scroll=ft.ScrollMode.ADAPTIVE, spacing=0, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    return ft.View(route="/", controls=[content_column], bgcolor=bgcolor, padding=25, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- 2. OLDAL: SZENZOR MONITOR ---
# ==============================================================================
def sensor_view(page: ft.Page):
    bgcolor = ft.Colors.BLUE_900
    global simulation_running, simulation_thread

    # --- Adatok és Konfiguráció ---
    sensor_data = [
        {"time": datetime.now().strftime("%H:%M:%S"), "sensor": "temp", "value": "22.70", "unit": "°C"},
        {"time": datetime.now().strftime("%H:%M:%S"), "sensor": "hum", "value": "42.10", "unit": "%RH"},
        {"time": datetime.now().strftime("%H:%M:%S"), "sensor": "light", "value": "650", "unit": "lux"},
    ]
    current_values = {"temp": "22.70", "hum": "42.10", "light": "650"}
    sensor_colors = {
        "temp": {"color": "#FF6B6B", "icon": "🌡️", "name": "Temperature"},
        "hum": {"color": "#4ECDC4", "icon": "💧", "name": "Humidity"},
        "light": {"color": "#FFD93D", "icon": "💡", "name": "Light"},
    }
    
    # --- Kártya létrehozó ---
    def create_metric_card(sensor_type):
        color_info = sensor_colors[sensor_type]
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Text(color_info["icon"], size=32), width=60, height=60, bgcolor=ft.Colors.WHITE, border_radius=15, alignment=ft.alignment.center),
                    ft.Column([ft.Text(color_info["name"], size=18, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD), ft.Text(f"Updated: --:--:--", size=12, color=ft.Colors.WHITE54)], spacing=3),
                ], spacing=15),
                ft.Container(height=15),
                ft.Text("--", size=42, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Text("", size=16, color=ft.Colors.WHITE54),
            ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=10),
            bgcolor=color_info["color"], padding=25, border_radius=25, width=220, height=220,
        )
    
    temp_card = create_metric_card("temp"); humidity_card = create_metric_card("hum"); light_card = create_metric_card("light")
    cards = {"temp": temp_card, "hum": humidity_card, "light": light_card}

    # --- Adattábla ---
    data_table = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.BOLD)), ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.BOLD)), ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.BOLD)), ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.BOLD))],
        rows=[], border=ft.border.all(1, ft.Colors.GREY_300), border_radius=10,
    )

    # --- Frissítő függvények ---
    def update_card(sensor_type, value, unit):
        card = cards[sensor_type]
        card.content.controls[2].value = value
        card.content.controls[3].value = unit
        card.content.controls[0].controls[1].controls[1].value = f"Updated: {datetime.now().strftime('%H:%M:%S')}"

    def update_data_table():
        data_table.rows.clear()
        for data in sensor_data[-8:][::-1]:
            color_info = sensor_colors[data["sensor"]]
            data_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(data["time"], size=13, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Container(content=ft.Row([ft.Text(color_info["icon"], size=16), ft.Text(data["sensor"].upper(), size=13, weight=ft.FontWeight.BOLD)], spacing=8), padding=8)),
                ft.DataCell(ft.Text(data["value"], size=15, weight=ft.FontWeight.BOLD)),
                ft.DataCell(ft.Text(data["unit"], size=13, color=ft.Colors.GREY_600)),
            ]))

    def update_ui_with_new_data():
        update_card("temp", current_values["temp"], "°C")
        update_card("hum", current_values["hum"], "%RH")
        update_card("light", current_values["light"], "lux")
        update_data_table()
        if page: page.update()

    # --- Szimuláció ---
    def simulate_sensor_data():
        while simulation_running:
            if status_text.value == "Simulator: RUNNING":
                current_time = datetime.now().strftime("%H:%M:%S")
                new_temp = round(20 + random.uniform(1, 5), 2); current_values["temp"] = f"{new_temp:.2f}"
                new_hum = round(40 + random.uniform(1, 10), 2); current_values["hum"] = f"{new_hum:.2f}"
                new_light = random.randint(500, 800); current_values["light"] = f"{new_light}"
                sensor_data.extend([
                    {"time": current_time, "sensor": "temp", "value": f"{new_temp:.2f}", "unit": "°C"},
                    {"time": current_time, "sensor": "hum", "value": f"{new_hum:.2f}", "unit": "%RH"},
                    {"time": current_time, "sensor": "light", "value": f"{new_light}", "unit": "lux"},
                ])
                if page:
                    try: page.run_thread(lambda: update_ui_with_new_data())
                    except Exception: break
            time.sleep(3)

    # --- Gombkezelők ---
    def on_start_click(e):
        start_btn.disabled = True; stop_btn.disabled = False; status_indicator.bgcolor = ft.Colors.GREEN; status_text.value = "Simulator: RUNNING"; page.update()
    def on_stop_click(e):
        start_btn.disabled = False; stop_btn.disabled = True; status_indicator.bgcolor = ft.Colors.RED; status_text.value = "Simulator: STOPPED"; page.update()
    def on_home_click(e):
        global simulation_running
        simulation_running = False # Szimuláció leállítása navigáció előtt
        page.go("/")

    # --- UI Elemek ---
    status_indicator = ft.Container(width=15, height=15, border_radius=8, bgcolor=ft.Colors.GREEN)
    status_text = ft.Text("Simulator: RUNNING", size=16, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
    start_btn = ft.ElevatedButton("▶ Start Publishing", icon=ft.Icons.PLAY_ARROW, on_click=on_start_click, disabled=True, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.GREEN, padding=25, shape=ft.RoundedRectangleBorder(radius=15)), height=55)
    stop_btn = ft.ElevatedButton("⏹ Stop Simulator", icon=ft.Icons.STOP, on_click=on_stop_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=ft.Colors.RED, padding=25, shape=ft.RoundedRectangleBorder(radius=15)), height=55)
    
    controls_card = ft.Container(
        content=ft.Column([
            ft.Text("Simulation Controls", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Container(height=20),
            ft.Row([start_btn, stop_btn], spacing=20, alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=20),
            ft.Row([status_indicator, status_text], spacing=12, alignment=ft.MainAxisAlignment.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=ft.Colors.BLUE_700, padding=30, border_radius=25, margin=ft.margin.symmetric(vertical=25),
    )

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=ft.Colors.WHITE, icon_size=28, on_click=on_home_click),
            ft.Column([ft.Text("Real-Time Sensor Monitor", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE), ft.Text("Live IoT Sensor Data Stream", size=16, color=ft.Colors.WHITE54)], spacing=5),
            ft.Container(expand=True),
        ], alignment=ft.MainAxisAlignment.START),
        margin=ft.margin.only(bottom=35),
    )

    metrics_row = ft.Row([temp_card, humidity_card, light_card], spacing=25, alignment=ft.MainAxisAlignment.CENTER, wrap=True)
    data_table_container = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.TABLE_CHART, color=ft.Colors.WHITE, size=28), ft.Text("Live Sensor Data Stream", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)], spacing=12),
            ft.Container(height=15),
            ft.Container(content=data_table, bgcolor=ft.Colors.WHITE, padding=20, border_radius=20),
        ]), margin=ft.margin.only(bottom=25),
    )

    home_btn = ft.ElevatedButton("🏠 HOME", on_click=on_home_click, bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE, width=220, height=55, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)))

    # --- Inicializálás és Indítás ---
    update_ui_with_new_data()
    if not simulation_running:
        simulation_running = True
        simulation_thread = threading.Thread(target=simulate_sensor_data, daemon=True)
        simulation_thread.start()

    main_column = ft.Column([header, metrics_row, controls_card, data_table_container, ft.Container(content=home_btn, alignment=ft.alignment.center, margin=ft.margin.only(bottom=20))], scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=0)

    return ft.View(route="/sensors", controls=[ft.Container(content=main_column, expand=True)], bgcolor=bgcolor, padding=25, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- 3. OLDAL: EXTRÁK (Galéria + AI Chat) ---
# ==============================================================================
def extras_view(page: ft.Page):
    bgcolor = ft.Colors.WHITE

    # --- 1. FÜL: NÖVÉNY GALÉRIA ---
    gallery_grid = ft.GridView(expand=True, runs_count=3, max_extent=300, child_aspect_ratio=0.8, spacing=20, run_spacing=20)

    def delete_image(item_to_delete):
        if item_to_delete in GALLERY_DATA:
            GALLERY_DATA.remove(item_to_delete)
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Kép törölve!"), bgcolor=ft.Colors.RED_700))

    def update_gallery_ui():
        gallery_grid.controls.clear()
        for item in GALLERY_DATA:
            path = item["path"]; date_str = item["date"]
            date_text = ft.Text(date_str, size=12, color=ft.Colors.GREY_700, weight="bold")
            delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=ft.Colors.RED_400, tooltip="Kép törlése", on_click=lambda e, current_item=item: delete_image(current_item))
            footer_row = ft.Row([date_text, delete_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            gallery_item = ft.Card(elevation=4, content=ft.Container(padding=10, content=ft.Column([ft.Image(src=path, width=float("inf"), height=200, fit=ft.ImageFit.COVER, border_radius=8), ft.Container(content=footer_row, padding=ft.padding.only(top=5))], spacing=5)))
            gallery_grid.controls.append(gallery_item)
        if not GALLERY_DATA:
            gallery_grid.controls.append(ft.Container(content=ft.Text("Még nincsenek feltöltött képek.", color=ft.Colors.GREY_400), alignment=ft.alignment.center, padding=50))
        if page: page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path; formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            GALLERY_DATA.insert(0, {"path": file_path, "date": formatted_date})
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Kép sikeresen hozzáadva!"), bgcolor=ft.Colors.GREEN_700))

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    upload_btn = ft.ElevatedButton("Új fotó", icon=ft.Icons.ADD_A_PHOTO, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10), bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE), on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE))

    gallery_tab_content = ft.Column([ft.Row([ft.Text("🌱 Növény Napló", size=24, weight="bold", color=ft.Colors.GREEN_800), upload_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Divider(), gallery_grid], expand=True)

    # --- 2. FÜL: AI CHATBOX ---
    chat_messages_list = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
    chat_input = ft.TextField(hint_text="Írj valamit az AI-nak...", expand=True, border_radius=20, bgcolor=ft.Colors.WHITE, on_submit=lambda e: send_message_click(e))
    send_button = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=ft.Colors.BLUE_600, tooltip="Küldés", on_click=lambda e: send_message_click(e))

    def create_message_bubble(text, is_user):
        return ft.Row(alignment=ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START, controls=[ft.Container(content=ft.Text(text, color=ft.Colors.WHITE if is_user else ft.Colors.BLACK), padding=15, border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_left=15 if is_user else 0, bottom_right=0 if is_user else 15), bgcolor=ft.Colors.BLUE_600 if is_user else ft.Colors.GREY_200, width=page.width * 0.7)])

    async def get_ai_response_async(prompt):
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json", "HTTP-Referer": "https://flet.dev", "X-Title": "Flet Smart Home App"}
        chat_history_for_api.append({"role": "user", "content": prompt})
        payload = {"model": MODEL_NAME, "messages": chat_history_for_api, "temperature": 0.7}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json(); ai_message_content = data['choices'][0]['message']['content']
                        chat_history_for_api.append({"role": "assistant", "content": ai_message_content})
                        return ai_message_content
                    else: error_text = await response.text(); return f"Hiba az API hívásnál: {response.status} - {error_text}"
        except Exception as e: return f"Kapcsolódási hiba: {str(e)}"

    def send_message_click(e):
        user_message = chat_input.value
        if not user_message: return
        chat_messages_list.controls.append(create_message_bubble(user_message, is_user=True))
        chat_input.value = ""; chat_input.disabled = True; send_button.disabled = True; page.update()
        typing_indicator = ft.Text("Az AI gondolkodik...", italic=True, color=ft.Colors.GREY_500)
        chat_messages_list.controls.append(typing_indicator); page.update()
        async def process_ai_response():
            response_text = await get_ai_response_async(user_message)
            chat_messages_list.controls.remove(typing_indicator)
            chat_messages_list.controls.append(create_message_bubble(response_text, is_user=False))
            chat_input.disabled = False; send_button.disabled = False; chat_input.focus(); page.update()
        page.run_task(process_ai_response)

    chat_tab_content = ft.Column(controls=[ft.Text("💬 DeepSeek AI Chat", size=24, weight="bold", color=ft.Colors.BLUE_800), ft.Divider(), ft.Container(content=chat_messages_list, expand=True, bgcolor=ft.Colors.GREY_50, border_radius=10, border=ft.border.all(1, ft.Colors.GREY_200)), ft.Row([chat_input, send_button], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)], expand=True)

    # --- FÜLEK ÖSSZEÁLLÍTÁSA ---
    chat_messages_list.controls.append(create_message_bubble("Szia! Én vagyok az okosotthonod AI asszisztense. Miben segíthetek?", is_user=False))
    tabs = ft.Tabs(selected_index=0, animation_duration=300, tabs=[
        ft.Tab(text="Növény Napló", icon=ft.Icons.IMAGE, content=ft.Container(content=gallery_tab_content, padding=10)),
        ft.Tab(text="AI Chat", icon=ft.Icons.CHAT_BUBBLE, content=ft.Container(content=chat_tab_content, padding=10)),
    ], expand=True)

    # --- VISSZA GOMB ---
    home_btn = ft.ElevatedButton("🏠 HOME", on_click=lambda _: page.go("/"), bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE)
    
    main_column = ft.Column([ft.Row([home_btn], alignment=ft.MainAxisAlignment.START), tabs], expand=True)

    update_gallery_ui()
    return ft.View(route="/extras", controls=[main_column], bgcolor=bgcolor, padding=20, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- FŐ ALKALMAZÁS LOGIKA ÉS NAVIGÁCIÓ ---
# ==============================================================================
def main(page: ft.Page):
    page.title = "Smart Home Super App"
    
    # Útvonalváltás kezelése
    def route_change(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(home_view(page))
        elif page.route == "/sensors":
            page.views.append(sensor_view(page))
        elif page.route == "/extras":
            page.views.append(extras_view(page))
        page.update()

    # Vissza gomb kezelése
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Indítás a főoldalon
    page.go("/")

ft.app(target=main)