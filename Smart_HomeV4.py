import flet as ft
from datetime import datetime
import random
import time
import threading
import aiohttp
import asyncio
import json
import logging

# ==============================================================================
# --- GLOBÁLIS KONFIGURÁCIÓ ÉS ADATTÁROLÁS ---
# ==============================================================================

# --- AI CHAT KONFIGURÁCIÓ (OpenRouter / DeepSeek) ---
# FONTOS: Használd a saját kulcsodat!
API_KEY = "YOUR_OWN_API_KEY_HERE" # Cseréld le a saját kulcsodra!
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

# --- THINGSPEAK KONFIGURÁCIÓ ---
THINGSPEAK_CHANNEL_ID = "3156213"
THINGSPEAK_READ_KEY = "WXM1B5P9O2XBKKMS"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json?api_key={THINGSPEAK_READ_KEY}"
POLL_INTERVAL_SECONDS = 15

# --- LOGOLÁS ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GLOBÁLIS ADATTÁROLÁS ---
GALLERY_DATA = []
chat_history_for_api = [
    {"role": "system", "content": "You are a helpful assistant in a smart home monitor application."}
]
GLOBAL_THINGSPEAK_HISTORY = {
    "Field1": [], # Temp
    "Field2": [], # Humidity
    "Field7": []  # Light
}
simulation_running = False
simulation_thread = None

# ==============================================================================
# --- PROFI UI DESIGN RENDSZER (Színek és Stílusok a képek alapján) ---
# ==============================================================================

# Színpaletta
BG_COLOR = "#F5F7FA"      # Világos, semleges háttér (képek alapján)
CARD_BG = "#FFFFFF"       # Fehér kártya alap
TEXT_PRIMARY = "#212121"  # Fő szövegszín (majdnem fekete)
TEXT_SECONDARY = "#757575" # Másodlagos szövegszín (szürke)

# Akcentus színek (szenzorokhoz)
COLOR_PRIMARY = "#0056D2" # Professzionális kék (Brand color / Humidity)
COLOR_SUCCESS = "#34C759" # Modern zöld (Status ON)
COLOR_DANGER = "#FF3B30"  # Modern piros (Temp / Status OFF)
COLOR_WARNING = "#FF9500" # Modern narancs (Light)
COLOR_PURPLE = "#AF52DE"  # Modern lila (Air Quality - opcionális)

# Stílus konstansok
CARD_ELEVATION = 2
CARD_BORDER_RADIUS = 16
SECTION_PADDING = 24

# Chart stílusok
CHART_BG_COLOR = CARD_BG
GRID_COLOR = "#E0E0E0"
AXIS_TITLE_COLOR = TEXT_SECONDARY
LABEL_COLOR = TEXT_SECONDARY
LABEL_STYLE = ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=LABEL_COLOR)
AXIS_TITLE_STYLE = ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=AXIS_TITLE_COLOR)

# ==============================================================================
# --- SEGÉDFÜGGVÉNYEK ---
# ==============================================================================
def generate_y_labels(min_val, max_val):
    """Dinamikus Y-tengely címkék generálása a tartomány alapján."""
    rng = max_val - min_val
    if rng <= 20: step = 5
    elif rng <= 50: step = 10
    elif rng <= 1000: step = 200
    else: step = 500
    
    labels = []
    curr = min_val
    while curr <= max_val:
        labels.append(ft.ChartAxisLabel(value=curr, label=ft.Text(str(int(curr)), style=LABEL_STYLE)))
        curr += step
    return labels

# ==============================================================================
# --- 1. OLDAL: FŐMENÜ (Dashboard) - REDESIGNED ---
# ==============================================================================
def home_view(page: ft.Page):
    
    # --- Eseménykezelők (Interaktív gombokhoz) ---
    def on_light_click(e):
        if light_button.text == "Turn ON":
            light_status.value = "Status: ON"; light_status.color = COLOR_SUCCESS
            light_button.text = "Turn OFF"; light_button.style.bgcolor = COLOR_DANGER
            light_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_SUCCESS)
            light_icon.color = COLOR_SUCCESS
        else:
            light_status.value = "Status: OFF"; light_status.color = COLOR_DANGER
            light_button.text = "Turn ON"; light_button.style.bgcolor = COLOR_SUCCESS
            light_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_WARNING)
            light_icon.color = COLOR_WARNING
        page.update()

    def on_door_click(e):
        if door_button.text == "Unlock":
            door_status.value = "Door: UNLOCKED"; door_status.color = COLOR_SUCCESS
            door_button.text = "Lock"; door_button.style.bgcolor = COLOR_DANGER
        else:
            door_status.value = "Door: LOCKED"; door_status.color = COLOR_DANGER
            door_button.text = "Unlock"; door_button.style.bgcolor = COLOR_SUCCESS
        page.update()

    def on_fan_click(e):
        if fan_button.text == "Turn ON":
            fan_status.value = "Status: ON"; fan_status.color = COLOR_SUCCESS
            fan_button.text = "Turn OFF"; fan_button.style.bgcolor = COLOR_DANGER
        else:
            fan_status.value = "Status: OFF"; fan_status.color = COLOR_DANGER
            fan_button.text = "Turn ON"; fan_button.style.bgcolor = COLOR_SUCCESS
        page.update()

    def on_rain_click(e):
        if rain_button.text == "Set YES":
            rain_status.value = "Rain: YES"; rain_status.color = COLOR_PRIMARY
            rain_button.text = "Set NO"; rain_button.style.bgcolor = COLOR_WARNING
        else:
            rain_status.value = "Rain: NO"; rain_status.color = COLOR_WARNING
            rain_button.text = "Set YES"; rain_button.style.bgcolor = COLOR_PRIMARY
        page.update()

    def on_window_click(e):
        if window_button.text == "Open":
            window_status.value = "Window: OPEN"; window_status.color = COLOR_SUCCESS
            window_button.text = "Close"; window_button.style.bgcolor = COLOR_DANGER
        else:
            window_status.value = "Window: CLOSED"; window_status.color = COLOR_DANGER
            window_button.text = "Open"; window_button.style.bgcolor = COLOR_SUCCESS
        page.update()

    # --- UI Kártya Készítő Segédfüggvények (REDESIGNED) ---
    # Ez a stílus felel meg az image_9.png és image_0.png képeknek
    def create_sensor_card(title, value, unit, accent_color, icon_data, details, width=300):
        return ft.Card(
            elevation=CARD_ELEVATION,
            shadow_color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20,
                width=width,
                content=ft.Column([
                    # Header: Ikon színezett háttérrel + Cím
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(icon_data, color=accent_color, size=24),
                            padding=10,
                            bgcolor=ft.Colors.with_opacity(0.1, accent_color),
                            border_radius=12,
                        ),
                        ft.Column([
                            ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Text("Real-time sensor", size=12, color=TEXT_SECONDARY)
                        ], spacing=2),
                    ], spacing=15),
                    ft.Container(height=15),
                    # Érték és Mértékegység
                    ft.Row([
                        ft.Text(value, size=36, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(unit, size=16, color=TEXT_SECONDARY),
                    ], vertical_alignment=ft.CrossAxisAlignment.END),
                     ft.Container(height=10),
                    # Részletek lábléc
                    ft.Container(
                        content=ft.Text(details, size=11, color=TEXT_SECONDARY),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=BG_COLOR,
                        border_radius=8,
                        width=float("inf")
                    ),
                ])
            )
        )

    def create_interactive_card(title, status_control, icon_container_control, description, button_control, width=300):
        return ft.Card(
            elevation=CARD_ELEVATION,
            shadow_color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20,
                width=width,
                content=ft.Column([
                    ft.Row([
                        icon_container_control,
                        ft.Column([
                            ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Text("Smart device", size=12, color=TEXT_SECONDARY)
                        ], spacing=2),
                    ], spacing=15),
                    ft.Container(height=10),
                    status_control,
                    ft.Text(description, size=12, color=TEXT_SECONDARY),
                    ft.Container(height=15),
                    button_control,
                ])
            )
        )

    # --- NAVIGÁCIÓS GOMBOK (Stilizálva) ---
    nav_btn_style = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=COLOR_PRIMARY,
        padding=ft.padding.symmetric(horizontal=24, vertical=18),
        shape=ft.RoundedRectangleBorder(radius=12),
        elevation=2
    )
    
    go_to_sensors_btn = ft.ElevatedButton("Simulated Sensors 📊", on_click=lambda _: page.go("/sensors"), style=nav_btn_style)
    go_to_real_datas_btn = ft.ElevatedButton("Real Data (IoT) 📈", on_click=lambda _: page.go("/realdatas"), style=nav_btn_style)
    go_to_extras_btn = ft.ElevatedButton("Extras & AI Chat 🤖", on_click=lambda _: page.go("/extras"), style=nav_btn_style)

    # Fejléc
    header = ft.Container(
        content=ft.Column([
            ft.Text("Smart Home Dashboard", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Overview and control panel", size=16, color=TEXT_SECONDARY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=30, top=10),
        alignment=ft.alignment.center
    )

    nav_row = ft.Container(
        content=ft.Row([go_to_sensors_btn, go_to_real_datas_btn, go_to_extras_btn], spacing=15, alignment=ft.MainAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=40)
    )

    # --- Kártyák Példányosítása (Új stílussal) ---
    temp_card = create_sensor_card("Temperature", "22.5", "°C", COLOR_DANGER, ft.Icons.THERMOSTAT, "DHT22 Sensor | Range: -40 to 80°C")
    humidity_card = create_sensor_card("Humidity", "45", "% RH", COLOR_PRIMARY, ft.Icons.WATER_DROP, "DHT22 Sensor | Range: 0-100%")

    # Interactive controls setup
    light_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    light_button = ft.ElevatedButton("Turn ON", on_click=on_light_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    light_icon = ft.Icon(ft.Icons.LIGHTBULB, color=COLOR_WARNING, size=24)
    light_icon_container = ft.Container(content=light_icon, padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_WARNING), border_radius=12)
    light_card = create_interactive_card("Light", light_status, light_icon_container, "BH1750 Sensor Controlled", light_button)

    fan_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    fan_button = ft.ElevatedButton("Turn ON", on_click=on_fan_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    fan_icon_container = ft.Container(content=ft.Icon(ft.Icons.WIND_POWER, color=COLOR_PRIMARY, size=24), padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_PRIMARY), border_radius=12)
    fan_card = create_interactive_card("Fan", fan_status, fan_icon_container, "DC Motor Control", fan_button)

    rain_status = ft.Text("Rain: NO", size=18, weight=ft.FontWeight.W_600, color=COLOR_WARNING)
    rain_button = ft.ElevatedButton("Set YES", on_click=on_rain_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_PRIMARY, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    rain_icon_container = ft.Container(content=ft.Icon(ft.Icons.WATER, color=COLOR_PRIMARY, size=24), padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_PRIMARY), border_radius=12)
    rain_card = create_interactive_card("Rain Detection", rain_status, rain_icon_container, "Rain Sensor Module", rain_button)

    window_status = ft.Text("Window: CLOSED", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    window_button = ft.ElevatedButton("Open", on_click=on_window_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    window_icon_container = ft.Container(content=ft.Icon(ft.Icons.WINDOW, color=COLOR_WARNING, size=24), padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_WARNING), border_radius=12)
    window_card = create_interactive_card("Window", window_status, window_icon_container, "Smart Window Controller", window_button)

    door_status = ft.Text("Door: LOCKED", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    door_button = ft.ElevatedButton("Unlock", on_click=on_door_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_PRIMARY, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    door_icon_container = ft.Container(content=ft.Icon(ft.Icons.LOCK, color=COLOR_PRIMARY, size=24), padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_PRIMARY), border_radius=12)
    door_card = create_interactive_card("Front Door", door_status, door_icon_container, "Smart Lock System", door_button)

    # --- Elrendezés ---
    section_title_style = ft.TextStyle(size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    
    content_column = ft.Column([
        header,
        nav_row,
        ft.Text("Environmental Sensors", style=section_title_style),
        ft.Container(height=10),
        ft.Row([temp_card, humidity_card], spacing=20, wrap=True, alignment=ft.MainAxisAlignment.START),
        ft.Container(height=30),
        ft.Text("Device Control", style=section_title_style),
        ft.Container(height=10),
        ft.Row([light_card, fan_card, rain_card, window_card, door_card], spacing=20, wrap=True, alignment=ft.MainAxisAlignment.START),
    ], scroll=ft.ScrollMode.ADAPTIVE, spacing=0)

    return ft.View(route="/", controls=[content_column], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- 2. OLDAL: SENSOR MONITOR (Szimulált) - REDESIGNED ---
# ==============================================================================
def sensor_view(page: ft.Page):
    global simulation_running, simulation_thread

    # Adatok (maradnak)
    sensor_data = [] # Kezdetben üres, majd töltődik
    current_values = {"temp": "22.70", "hum": "42.10", "light": "650"}
    sensor_conf = {
        "temp": {"color": COLOR_DANGER, "icon": ft.Icons.THERMOSTAT, "name": "Temperature"},
        "hum": {"color": COLOR_PRIMARY, "icon": ft.Icons.WATER_DROP, "name": "Humidity"},
        "light": {"color": COLOR_WARNING, "icon": ft.Icons.LIGHTBULB, "name": "Light"},
    }
    
    # --- UI Kártya Készítő (REDESIGNED) ---
    # Frissíthető kártyák létrehozása referenciákkal
    def create_metric_card(sensor_type):
        conf = sensor_conf[sensor_type]
        accent = conf["color"]
        
        ts_text = ft.Text("Updated: --:--:--", size=11, color=TEXT_SECONDARY)
        value_text = ft.Text("--", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        unit_text = ft.Text("", size=16, color=TEXT_SECONDARY)

        card = ft.Card(
            elevation=CARD_ELEVATION,
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20,
                width=250,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(conf["icon"], color=accent, size=28),
                            padding=10, bgcolor=ft.Colors.with_opacity(0.1, accent), border_radius=12
                        ),
                        ft.Column([
                            ft.Text(conf["name"], size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ts_text
                        ], spacing=2),
                    ], spacing=15),
                    ft.Container(height=20),
                    ft.Row([
                         value_text,
                         unit_text
                    ], vertical_alignment=ft.CrossAxisAlignment.END)
                   
                ])
            )
        )
        return card, ts_text, value_text, unit_text
    
    temp_card, temp_ts, temp_val, temp_unit = create_metric_card("temp")
    humidity_card, hum_ts, hum_val, hum_unit = create_metric_card("hum")
    light_card, light_ts, light_val, light_unit = create_metric_card("light")

    card_refs = {
        "temp": {"ts": temp_ts, "val": temp_val, "unit": temp_unit},
        "hum": {"ts": hum_ts, "val": hum_val, "unit": hum_unit},
        "light": {"ts": light_ts, "val": light_val, "unit": light_unit},
    }

    # --- Data Table (REDESIGNED) ---
    # Megfelel az image_2.png és image_10.png stílusának
    data_table = ft.DataTable(
        heading_row_color=BG_COLOR,
        heading_row_height=40,
        data_row_min_height=50,
        border=ft.border.all(1, "#EEEEEE"),
        border_radius=12,
        columns=[
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY))
        ],
        rows=[],
    )

    # --- Update Funkciók ---
    def update_card(sensor_type, value, unit):
        refs = card_refs[sensor_type]
        refs["ts"].value = f"Updated: {datetime.now().strftime('%H:%M:%S')}"
        refs["val"].value = value
        refs["unit"].value = unit

    def update_data_table():
        data_table.rows.clear()
        # Legfrissebb 8 adat megjelenítése fordított sorrendben
        for data in sensor_data[-8:][::-1]:
            conf = sensor_conf[data["sensor"]]
            data_table.rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(data["time"], size=13, color=TEXT_PRIMARY)),
                ft.DataCell(ft.Row([
                    ft.Container(content=ft.Icon(conf["icon"], color=conf["color"], size=16), padding=4, bgcolor=ft.Colors.with_opacity(0.1, conf["color"]), border_radius=4),
                    ft.Text(conf["name"], size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
                ], spacing=8)),
                ft.DataCell(ft.Text(data["value"], size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
                ft.DataCell(ft.Text(data["unit"], size=13, color=TEXT_SECONDARY)),
            ]))

    def update_ui_with_new_data():
        update_card("temp", current_values["temp"], "°C")
        update_card("hum", current_values["hum"], "%RH")
        update_card("light", current_values["light"], "lux")
        update_data_table()
        if page: page.update()

    # --- Szimulációs Szál ---
    def simulate_sensor_data():
        while simulation_running:
            if status_text.value == "RUNNING":
                current_time = datetime.now().strftime("%H:%M:%S")
                new_temp = round(20 + random.uniform(1, 5), 2); current_values["temp"] = f"{new_temp:.2f}"
                new_hum = round(40 + random.uniform(1, 10), 2); current_values["hum"] = f"{new_hum:.2f}"
                new_light = random.randint(500, 800); current_values["light"] = f"{new_light}"
                sensor_data.append({"time": current_time, "sensor": "temp", "value": f"{new_temp:.2f}", "unit": "°C"})
                sensor_data.append({"time": current_time, "sensor": "hum", "value": f"{new_hum:.2f}", "unit": "%RH"})
                sensor_data.append({"time": current_time, "sensor": "light", "value": f"{new_light}", "unit": "lux"})
                
                if len(sensor_data) > 50: pass # Opcionális: memóriakezelés

                if page:
                    try:
                        page.run_thread(update_ui_with_new_data)
                    except Exception: break
            time.sleep(3)

    # --- Controls (REDESIGNED) ---
    def on_start_click(e):
        start_btn.disabled = True; stop_btn.disabled = False; status_indicator.bgcolor = COLOR_SUCCESS; status_text.value = "RUNNING"; status_text.color=COLOR_SUCCESS; page.update()
    def on_stop_click(e):
        start_btn.disabled = False; stop_btn.disabled = True; status_indicator.bgcolor = COLOR_DANGER; status_text.value = "STOPPED"; status_text.color=COLOR_DANGER; page.update()
    
    def on_home_click(e):
        global simulation_running; simulation_running = False; page.go("/")

    status_indicator = ft.Container(width=12, height=12, border_radius=6, bgcolor=COLOR_SUCCESS)
    status_text = ft.Text("RUNNING", size=14, weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS)
    
    ctrl_btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), padding=15)
    start_btn = ft.ElevatedButton("Start", icon=ft.Icons.PLAY_ARROW, on_click=on_start_click, disabled=True, bgcolor=COLOR_SUCCESS, color=ft.Colors.WHITE, style=ctrl_btn_style)
    stop_btn = ft.ElevatedButton("Stop", icon=ft.Icons.STOP, on_click=on_stop_click, bgcolor=COLOR_DANGER, color=ft.Colors.WHITE, style=ctrl_btn_style)
    
    controls_card = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(
            padding=20,
            content=ft.Row([
                ft.Text("Simulation Controls", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Row([start_btn, stop_btn], spacing=10),
                ft.Row([status_indicator, status_text], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )
    )

    header = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY, on_click=on_home_click),
        ft.Column([
            ft.Text("Simulated Sensors", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Real-time data simulation", size=14, color=TEXT_SECONDARY)
        ], spacing=2),
    ], alignment=ft.MainAxisAlignment.START)

    metrics_row = ft.Row([temp_card, humidity_card, light_card], spacing=20, alignment=ft.MainAxisAlignment.START, wrap=True)
    
    data_table_container = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(
            padding=20,
            content=ft.Column([
                 ft.Text("Live Data Log", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                 ft.Container(height=10),
                 data_table
            ])
        )
    )

    # Kezdeti UI frissítés és szimuláció indítása
    update_ui_with_new_data()
    if not simulation_running:
        simulation_running = True
        simulation_thread = threading.Thread(target=simulate_sensor_data, daemon=True)
        simulation_thread.start()

    main_column = ft.Column([
        header, ft.Container(height=20),
        metrics_row, ft.Container(height=20),
        controls_card, ft.Container(height=20),
        data_table_container, ft.Container(height=20),
    ], scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=0)

    return ft.View(route="/sensors", controls=[main_column], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)

# ==============================================================================
# --- 3. OLDAL: REAL DATAS VIEW (ThingSpeak) - REDESIGNED ---
# ==============================================================================
def realtime_data_view(page: ft.Page):
    logger.info("Real-time ThingSpeak view loading...")
    
    current_chart_field = "Field1"
    polling_state = {"is_running": False}
    
    field_configs = {
        "Field1": { "name": "Temperature", "color": COLOR_DANGER, "icon": ft.Icons.THERMOSTAT, "min_y": 15, "max_y": 35 },
        "Field2": { "name": "Humidity", "color": COLOR_PRIMARY, "icon": ft.Icons.WATER_DROP, "min_y": 30, "max_y": 80 },
        "Field7": { "name": "Light", "color": COLOR_WARNING, "icon": ft.Icons.LIGHTBULB, "min_y": 0, "max_y": 1000 },
    }

    # --- UI Elemek: Kártyák (REDESIGNED - image_9.png stílus) ---
    temp_val_txt = ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    temp_ts_txt = ft.Text("Waiting...", size=11, color=TEXT_SECONDARY)
    hum_val_txt = ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    hum_ts_txt = ft.Text("Waiting...", size=11, color=TEXT_SECONDARY)
    light_val_txt = ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    light_ts_txt = ft.Text("Waiting...", size=11, color=TEXT_SECONDARY)

    def on_card_clicked(e, field_id):
        nonlocal current_chart_field; current_chart_field = field_id
        config = field_configs[field_id]
        chart_axis_title.value = f"{config['name']} History"
        # Frissítjük a chart színeit és a kitöltést
        main_chart_series.color = config['color']
        main_chart_series.below_line_bgcolor = ft.Colors.with_opacity(0.1, config['color'])
        main_chart.min_y = config["min_y"]; main_chart.max_y = config["max_y"]
        main_chart.left_axis.labels = generate_y_labels(config["min_y"], config["max_y"])
        main_chart_series.data_points = list(GLOBAL_THINGSPEAK_HISTORY[field_id])
        page.update()

    def sensor_card(title: str, val_txt: ft.Text, ts_txt: ft.Text, unit_hint: str, field_id: str):
        config = field_configs[field_id]
        accent = config['color']
        return ft.Card(
            elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                on_click=lambda e: on_card_clicked(e, field_id),
                padding=20, ink=True, border_radius=CARD_BORDER_RADIUS,
                content=ft.Column([
                        ft.Row([
                            ft.Container(content=ft.Icon(config['icon'], color=accent, size=24), padding=8, bgcolor=ft.Colors.with_opacity(0.1, accent), border_radius=10),
                            ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)
                        ], spacing=10),
                        ft.Container(height=10),
                        ft.Row([
                             val_txt,
                             ft.Text(unit_hint, size=14, color=TEXT_SECONDARY)
                        ], vertical_alignment=ft.CrossAxisAlignment.END),
                        ft.Container(height=5),
                        ts_txt,
                    ], spacing=0),
            )
        )

    # --- UI Elemek: Adattábla (REDESIGNED - image_10.png stílus) ---
    table = ft.DataTable(
        heading_row_color=BG_COLOR, heading_row_height=40, data_row_min_height=40,
        border=ft.border.all(1, "#EEEEEE"), border_radius=12,
        columns=[
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY))
        ], rows=[],
    )
    table_container = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(padding=20, content=ft.Column([ft.Text("Log", size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), ft.Container(height=10), ft.Column([table], scroll=ft.ScrollMode.AUTO, height=250)]))
    )

    # --- UI Elemek: Grafikon (REDESIGNED - image_5.png / image_13.png stílus) ---
    initial_config = field_configs[current_chart_field]
    main_chart_series = ft.LineChartData(
        data_points=list(GLOBAL_THINGSPEAK_HISTORY[current_chart_field]),
        stroke_width=3, # Vastagabb vonal
        color=initial_config['color'],
        curved=True, # Simított vonal
        stroke_cap_round=True,
        below_line_bgcolor=ft.Colors.with_opacity(0.1, initial_config['color']), # Kitöltés a vonal alatt!
    )
    chart_axis_title = ft.Text(f"{initial_config['name']} History", style=AXIS_TITLE_STYLE)
    initial_y_labels = generate_y_labels(initial_config["min_y"], initial_config["max_y"])
    x_labels = [ft.ChartAxisLabel(value=i, label=ft.Text(str(i), style=LABEL_STYLE)) for i in range(10)]

    main_chart = ft.LineChart(
        data_series=[main_chart_series], min_x=0, max_x=9,
        min_y=initial_config["min_y"], max_y=initial_config["max_y"],
        interactive=True, expand=True,
        left_axis=ft.ChartAxis(title=chart_axis_title, labels=initial_y_labels, labels_size=40),
        bottom_axis=ft.ChartAxis(title=ft.Text("Index", style=AXIS_TITLE_STYLE), labels=x_labels, labels_interval=1),
        bgcolor=CHART_BG_COLOR,
        border=ft.border.all(0, ft.Colors.TRANSPARENT), # Nincs keret
        tooltip_bgcolor=CARD_BG,
    )
    
    chart_card = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(content=main_chart, height=400, padding=20)
    )

    # --- UI Elemek: Gombok és Header (REDESIGNED) ---
    def on_home_click(e): stop_polling(None); page.go("/")

    header = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY, on_click=on_home_click),
        ft.Column([
            ft.Text("IoT Monitor", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Real-time data from ThingSpeak", size=14, color=TEXT_SECONDARY)
        ], spacing=2),
    ], alignment=ft.MainAxisAlignment.START)

    status_indicator = ft.Container(width=10, height=10, border_radius=5, bgcolor=TEXT_SECONDARY)
    status_text = ft.Text("Idle", color=TEXT_SECONDARY, size=12)
    
    ctrl_style = ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=15, vertical=10), shape=ft.RoundedRectangleBorder(radius=10))
    start_btn = ft.ElevatedButton("Start Polling", icon=ft.Icons.CLOUD_DOWNLOAD, style=ctrl_style, bgcolor=COLOR_PRIMARY, color=ft.Colors.WHITE)
    stop_btn = ft.ElevatedButton("Stop", icon=ft.Icons.STOP, disabled=True, style=ctrl_style, bgcolor=COLOR_DANGER, color=ft.Colors.WHITE)

    polling_controls = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(
            padding=15,
            content=ft.Row([
                ft.Row([start_btn, stop_btn]),
                ft.Row([status_indicator, status_text], spacing=5)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        )
    )

    # --- Layout ---
    overview_col = ft.Column([
        ft.Text("Overview", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        ft.Row([
            sensor_card("Temp", temp_val_txt, temp_ts_txt, "°C", "Field1"),
            sensor_card("Humidity", hum_val_txt, hum_ts_txt, "%", "Field2"),
            sensor_card("Light", light_val_txt, light_ts_txt, "Lx", "Field7"),
        ], spacing=15, wrap=True),
        ft.Container(height=20),
        polling_controls,
        ft.Container(height=20),
        table_container,
    ], spacing=0, expand=4)

    chart_col = ft.Column([
        ft.Text("Analysis", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        chart_card,
    ], spacing=0, expand=6)

    main_layout = ft.Column([
        header, ft.Container(height=20),
        ft.Row([overview_col, ft.Container(width=20), chart_col], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.VerticalAlignment.START, expand=True)
    ], expand=True)


    # --- LOGIKA (Marad a régi) ---
    def on_message(msg):
        if not isinstance(msg, dict) or msg.get("type") != "sensor": return
        name = msg["name"]; value = msg["value"]; unit = msg["unit"]; ts_raw = msg["ts"]
        try:
            dt_obj = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            ts_formatted = dt_obj.strftime("%H:%M:%S")
        except (ValueError, TypeError): ts_formatted = "N/A"

        # UI frissítés (szövegek)
        if name == "Field1": temp_val_txt.value = str(value); temp_ts_txt.value = ts_formatted
        elif name == "Field2": hum_val_txt.value = str(value); hum_ts_txt.value = ts_formatted
        elif name == "Field7": light_val_txt.value = str(value); light_ts_txt.value = ts_formatted

        # Adat mentése és grafikon frissítése
        try:
            float_val = float(value)
            if name in GLOBAL_THINGSPEAK_HISTORY:
                target_history = GLOBAL_THINGSPEAK_HISTORY[name]
                target_history.append(ft.LineChartDataPoint(len(target_history), float_val))
                if len(target_history) > 10:
                    target_history.pop(0)
                    for i, p in enumerate(target_history): p.x = i
                if name == current_chart_field:
                    main_chart_series.data_points = list(target_history)
        except (ValueError, TypeError): pass

        # Napló frissítése (Szép névvel)
        sensor_nice_name = field_configs[name]["name"] if name in field_configs else name
        table.rows.insert(0, ft.DataRow(cells=[
            ft.DataCell(ft.Text(ts_formatted, size=12, color=TEXT_PRIMARY)),
            ft.DataCell(ft.Text(sensor_nice_name, size=12, color=TEXT_SECONDARY)),
            ft.DataCell(ft.Text(str(value), size=12, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
            ft.DataCell(ft.Text(unit, size=12, color=TEXT_SECONDARY))
        ]))
        if len(table.rows) > 50: table.rows.pop()
        if page: page.update()

    page.pubsub.subscribe(on_message)

    async def thingspeak_poller_loop():
        status_text.value = f"Polling ({POLL_INTERVAL_SECONDS}s)..."; status_indicator.bgcolor = COLOR_WARNING; page.update()
        async with aiohttp.ClientSession() as session:
            while polling_state["is_running"]:
                try:
                    async with session.get(THINGSPEAK_URL, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            status_text.value = "Online"; status_indicator.bgcolor = COLOR_SUCCESS; page.update()
                            ts = data.get("created_at"); f1 = data.get("field1"); f2 = data.get("field2"); f7 = data.get("field7")
                            if f1: page.pubsub.send_all({"type": "sensor", "name": "Field1", "value": f1, "unit": "°C", "ts": ts})
                            if f2: page.pubsub.send_all({"type": "sensor", "name": "Field2", "value": f2, "unit": "%RH", "ts": ts})
                            if f7: page.pubsub.send_all({"type": "sensor", "name": "Field7", "value": f7, "unit": "Lux", "ts": ts})
                        else: status_text.value = f"Error: {response.status}"; status_indicator.bgcolor = COLOR_DANGER; page.update()
                except Exception: status_text.value = "Connection Error"; status_indicator.bgcolor = COLOR_DANGER; page.update()
                if polling_state["is_running"]: await asyncio.sleep(POLL_INTERVAL_SECONDS)

    def start_polling(_):
        if polling_state["is_running"]: return
        polling_state["is_running"] = True; page.run_task(thingspeak_poller_loop)
        start_btn.disabled = True; stop_btn.disabled = False; page.update()

    def stop_polling(_):
        polling_state["is_running"] = False; status_text.value = "Stopped"; status_indicator.bgcolor = TEXT_SECONDARY; start_btn.disabled = False; stop_btn.disabled = True; page.update()

    start_btn.on_click = start_polling; stop_btn.on_click = stop_polling

    return ft.View(route="/realdatas", controls=[main_layout], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- 4. OLDAL: EXTRAS VIEW (Galéria & AI Chat) - REDESIGNED ---
# ==============================================================================
def extras_view(page: ft.Page):
    
    # --- 1. FÜL: NÖVÉNY GALÉRIA (REDESIGNED) ---
    gallery_grid = ft.GridView(expand=True, runs_count=3, max_extent=300, child_aspect_ratio=0.8, spacing=20, run_spacing=20)

    def delete_image(item_to_delete):
        if item_to_delete in GALLERY_DATA:
            GALLERY_DATA.remove(item_to_delete)
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Kép törölve!"), bgcolor=COLOR_DANGER))

    def update_gallery_ui():
        gallery_grid.controls.clear()
        for item in GALLERY_DATA:
            path = item["path"]; date_str = item["date"]
            date_text = ft.Text(date_str, size=12, color=TEXT_SECONDARY)
            delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLOR_DANGER, tooltip="Törlés", on_click=lambda e, current_item=item: delete_image(current_item))
            footer_row = ft.Row([date_text, delete_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            
            gallery_item = ft.Card(
                elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
                content=ft.Container(
                    padding=10,
                    content=ft.Column([
                        ft.Image(src=path, width=float("inf"), height=180, fit=ft.ImageFit.COVER, border_radius=12),
                        ft.Container(content=footer_row, padding=ft.padding.only(top=5, left=5, right=5))
                    ], spacing=5)
                )
            )
            gallery_grid.controls.append(gallery_item)
        if not GALLERY_DATA:
            gallery_grid.controls.append(ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=48, color=TEXT_SECONDARY),
                ft.Text("Nincsenek képek.", color=TEXT_SECONDARY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, padding=50))
        if page: page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path; formatted_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            GALLERY_DATA.insert(0, {"path": file_path, "date": formatted_date})
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text(f"Kép hozzáadva!"), bgcolor=COLOR_SUCCESS))

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    upload_btn = ft.ElevatedButton("Feltöltés", icon=ft.Icons.ADD_A_PHOTO, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=12), bgcolor=COLOR_PRIMARY, color=ft.Colors.WHITE), on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE))

    gallery_tab_content = ft.Column([
        ft.Row([
            ft.Text("Plant Gallery", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            upload_btn
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(height=20),
        gallery_grid
    ], expand=True)

    # --- 2. FÜL: AI CHATBOX (REDESIGNED) ---
    chat_messages_list = ft.ListView(expand=True, spacing=15, padding=20, auto_scroll=True)
    
    chat_input = ft.TextField(
        hint_text="Írj üzenetet...",
        hint_style=ft.TextStyle(color=TEXT_SECONDARY),
        text_style=ft.TextStyle(color=TEXT_PRIMARY),
        expand=True,
        border_radius=25,
        bgcolor=BG_COLOR,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=COLOR_PRIMARY,
        content_padding=ft.padding.symmetric(horizontal=20, vertical=15),
        on_submit=lambda e: send_message_click(e)
    )
    send_button = ft.IconButton(icon=ft.Icons.SEND_ROUNDED, icon_color=COLOR_PRIMARY, bgcolor=BG_COLOR, tooltip="Küldés", on_click=lambda e: send_message_click(e))

    def create_message_bubble(text, is_user):
        bubble_color = COLOR_PRIMARY if is_user else "#E0E0E0"
        text_color = ft.Colors.WHITE if is_user else TEXT_PRIMARY
        align = ft.MainAxisAlignment.END if is_user else ft.MainAxisAlignment.START
        
        return ft.Row(
            alignment=align,
            controls=[
                ft.Container(
                    content=ft.Text(text, color=text_color, size=14),
                    padding=ft.padding.symmetric(horizontal=16, vertical=12),
                    border_radius=ft.border_radius.only(
                        top_left=18, top_right=18,
                        bottom_left=5 if is_user else 18,
                        bottom_right=18 if is_user else 5
                    ),
                    bgcolor=bubble_color,
                    width=page.width * 0.65 if len(text) > 50 else None, # Max szélesség
                )
            ]
        )

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
                    else: error_text = await response.text(); return f"Hiba: {response.status}"
        except Exception as e: return f"Hiba: {str(e)}"

    def send_message_click(e):
        user_message = chat_input.value
        if not user_message: return
        chat_messages_list.controls.append(create_message_bubble(user_message, is_user=True))
        chat_input.value = ""; chat_input.disabled = True; send_button.disabled = True; page.update()
        typing_indicator = ft.Row([ft.ProgressRing(width=16, height=16, stroke_width=2, color=COLOR_PRIMARY), ft.Text("AI ír...", color=TEXT_SECONDARY, size=12)], spacing=10)
        chat_messages_list.controls.append(typing_indicator); page.update()
        async def process_ai_response():
            response_text = await get_ai_response_async(user_message)
            chat_messages_list.controls.remove(typing_indicator)
            chat_messages_list.controls.append(create_message_bubble(response_text, is_user=False))
            chat_input.disabled = False; send_button.disabled = False; chat_input.focus(); page.update()
        page.run_task(process_ai_response)

    chat_container = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        expand=True,
        content=ft.Container(
            content=chat_messages_list,
            padding=0
        )
    )

    chat_tab_content = ft.Column(controls=[
        ft.Text("AI Assistant", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        chat_container,
        ft.Container(height=10),
        ft.Row([chat_input, send_button], spacing=10)
    ], expand=True)

    # --- FÜLEK ÖSSZEÁLLÍTÁSA (REDESIGNED) ---
    if len(chat_messages_list.controls) == 0:
         chat_messages_list.controls.append(create_message_bubble("Szia! Miben segíthetek?", is_user=False))

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        indicator_color=COLOR_PRIMARY,
        label_color=COLOR_PRIMARY,
        unselected_label_color=TEXT_SECONDARY,
        divider_color="transparent",
        tabs=[
            ft.Tab(text="Gallery", icon=ft.Icons.PHOTO_LIBRARY_OUTLINED, content=ft.Container(content=gallery_tab_content, padding=ft.padding.only(top=20))),
            ft.Tab(text="AI Chat", icon=ft.Icons.CHAT_BUBBLE_OUTLINE, content=ft.Container(content=chat_tab_content, padding=ft.padding.only(top=20))),
        ],
        expand=True
    )

    header = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY, on_click=lambda _: page.go("/")),
        ft.Text("Extras", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
    ], alignment=ft.MainAxisAlignment.START)
    
    main_column = ft.Column([header, ft.Container(height=10), tabs], expand=True)

    update_gallery_ui()
    return ft.View(route="/extras", controls=[main_column], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)

# ==============================================================================
# --- FŐ ALKALMAZÁS LOGIKA ---
# ==============================================================================
def main(page: ft.Page):
    page.title = "Smart Home Pro"
    page.theme_mode = ft.ThemeMode.LIGHT # Fontos a világos témához
    page.fonts = {
        "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "RobotoBold": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    }
    page.theme = ft.Theme(font_family="Roboto")

    def route_change(route):
        page.views.clear()
        if page.route == "/": page.views.append(home_view(page))
        elif page.route == "/sensors": page.views.append(sensor_view(page))
        elif page.route == "/extras": page.views.append(extras_view(page))
        elif page.route == "/realdatas": page.views.append(realtime_data_view(page))
        page.update()

    def view_pop(view):
        page.views.pop(); top_view = page.views[-1]; page.go(top_view.route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")

ft.app(target=main)