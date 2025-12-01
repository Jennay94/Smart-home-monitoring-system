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
# --- GLOBAL CONFIGURATION & STATE ---
# ==============================================================================

# --- AI CHAT CONFIG (OpenRouter / DeepSeek) ---
# IMPORTANT: Replace with your actual API KEY!
API_KEY = "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"
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat"

# --- THINGSPEAK CONFIG ---
THINGSPEAK_CHANNEL_ID = "3156213"
THINGSPEAK_READ_KEY = "WXM1B5P9O2XBKKMS"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json?api_key={THINGSPEAK_READ_KEY}"
POLL_INTERVAL_SECONDS = 15

# --- LOGGING ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GLOBAL STATE STORAGE ---
GALLERY_DATA = []
chat_history_for_api = [
    {"role": "system", "content": "You are a helpful assistant in a smart home monitor application. Answer concisely in English."}
]
# Storage for chart history for defined fields
GLOBAL_THINGSPEAK_HISTORY = {
    "Field1": [], "Field2": [], "Field3": [],
    "Field4": [], "Field5": [], "Field7": []
}
simulation_running = False
simulation_thread = None

# ==============================================================================
# --- UI DESIGN SYSTEM (Colors & Styles based on images) ---
# ==============================================================================

# Color Palette
BG_COLOR = "#F5F7FA"      # Light grey background
CARD_BG = "#FFFFFF"       # White card background
TEXT_PRIMARY = "#212121"  # Main text color (near black)
TEXT_SECONDARY = "#757575" # Secondary text color (grey)

# Accent Colors for Sensors
COLOR_TEMP = "#FF3B30"    # Red
COLOR_HUM = "#0056D2"     # Blue
COLOR_LIGHT = "#FF9500"   # Orange
COLOR_SOIL = "#8D6E63"    # Brown
COLOR_RAIN = "#546E7A"    # Blue-grey
COLOR_FAN = "#78909C"     # Greyish

# Status Colors
COLOR_SUCCESS = "#34C759" # Green (Status ON / OK)
COLOR_DANGER = "#FF3B30"  # Red (Status OFF / Error)
COLOR_WARNING = "#FF9500" # Orange (Polling / Busy) - VISSZATÉRT!

# Style Constants
CARD_ELEVATION = 2
CARD_BORDER_RADIUS = 16 # More rounded corners as seen in images
SECTION_PADDING = 24

# Chart Styles
CHART_BG_COLOR = CARD_BG
AXIS_TITLE_STYLE = ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY)
LABEL_STYLE = ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=TEXT_SECONDARY)

# ==============================================================================
# --- HELPER FUNCTIONS ---
# ==============================================================================
def generate_y_labels(min_val, max_val):
    """Generates dynamic Y-axis labels based on data range."""
    rng = max_val - min_val
    if rng <= 20: step = 5
    elif rng <= 50: step = 10
    elif rng <= 200: step = 25
    elif rng <= 1000: step = 200
    else: step = 500
    
    labels = []
    # Ensure min and max are included and rounded nicely
    start = (int(min_val) // step) * step
    end = (int(max_val) // step + 1) * step
    
    curr = start
    while curr <= end:
        labels.append(ft.ChartAxisLabel(value=curr, label=ft.Text(str(int(curr)), style=LABEL_STYLE)))
        curr += step
    return labels

# ==============================================================================
# --- SHARED UI COMPONENTS ---
# ==============================================================================

def create_styled_log_table():
    """Creates the base DataTable structure matching image_3.png."""
    return ft.DataTable(
        heading_row_color=BG_COLOR,
        heading_row_height=50,
        data_row_min_height=60,
        border=ft.border.all(1, "#E0E0E0"),
        border_radius=12,
        vertical_lines=ft.border.BorderSide(0, "transparent"),
        horizontal_lines=ft.border.BorderSide(1, "#EEEEEE"),
        columns=[
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY))
        ],
        rows=[],
    )

def create_log_row(time_str, sensor_name, value_str, unit_str, icon_data, color):
    """Creates a styled DataRow with an icon for the logs."""
    return ft.DataRow(cells=[
        ft.DataCell(ft.Text(time_str, size=13, color=TEXT_PRIMARY)),
        # Sensor cell with icon and name
        ft.DataCell(ft.Row([
            ft.Icon(icon_data, color=color, size=18),
            ft.Text(sensor_name, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
        ], spacing=12)),
        # Bold value
        ft.DataCell(ft.Text(value_str, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
        ft.DataCell(ft.Text(unit_str, size=13, color=TEXT_SECONDARY)),
    ])

# ==============================================================================
# --- PAGE 1: HOME DASHBOARD (VISSZATÉRTEK AZ ESZKÖZÖK) ---
# ==============================================================================
def home_view(page: ft.Page):
    
    # --- Event Handlers ---
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
        
    # --- VISSZATÉRT ESEMÉNYKEZELŐK ---
    def on_fan_click(e):
        if fan_button.text == "Turn ON":
            fan_status.value = "Status: ON"; fan_status.color = COLOR_SUCCESS
            fan_button.text = "Turn OFF"; fan_button.style.bgcolor = COLOR_DANGER
            fan_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_SUCCESS)
            fan_icon.color = COLOR_SUCCESS
        else:
            fan_status.value = "Status: OFF"; fan_status.color = COLOR_DANGER
            fan_button.text = "Turn ON"; fan_button.style.bgcolor = COLOR_SUCCESS
            fan_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_FAN)
            fan_icon.color = COLOR_FAN
        page.update()

    def on_rain_click(e):
        if rain_button.text == "Set YES":
            rain_status.value = "Rain: YES"; rain_status.color = COLOR_SUCCESS
            rain_button.text = "Set NO"; rain_button.style.bgcolor = COLOR_DANGER
            rain_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_SUCCESS)
            rain_icon.color = COLOR_SUCCESS
        else:
            rain_status.value = "Rain: NO"; rain_status.color = COLOR_DANGER
            rain_button.text = "Set YES"; rain_button.style.bgcolor = COLOR_SUCCESS
            rain_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_RAIN)
            rain_icon.color = COLOR_RAIN
        page.update()

    def on_window_click(e):
        if window_button.text == "Open":
            window_status.value = "Window: OPEN"; window_status.color = COLOR_SUCCESS
            window_button.text = "Close"; window_button.style.bgcolor = COLOR_DANGER
            window_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_SUCCESS)
            window_icon.color = COLOR_SUCCESS
        else:
            window_status.value = "Window: CLOSED"; window_status.color = COLOR_DANGER
            window_button.text = "Open"; window_button.style.bgcolor = COLOR_SUCCESS
            window_icon_container.bgcolor = ft.Colors.with_opacity(0.1, COLOR_HUM)
            window_icon.color = COLOR_HUM
        page.update()

    # --- UI Card Creators (Matches image_0.png, image_9.png style) ---
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
                    # Header with colored icon background
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
                    # Value and Unit
                    ft.Row([
                        ft.Text(value, size=36, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(unit, size=16, color=TEXT_SECONDARY),
                    ], vertical_alignment=ft.CrossAxisAlignment.END),
                     ft.Container(height=10),
                    # Details footer
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

    # --- Navigation Buttons ---
    nav_btn_style = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor=COLOR_HUM,
        padding=ft.padding.symmetric(horizontal=24, vertical=18),
        shape=ft.RoundedRectangleBorder(radius=12),
        elevation=2
    )
    
    go_to_sensors_btn = ft.ElevatedButton("Simulated Sensors 📊", on_click=lambda _: page.go("/sensors"), style=nav_btn_style)
    go_to_real_datas_btn = ft.ElevatedButton("Real Data (IoT) 📈", on_click=lambda _: page.go("/realdatas"), style=nav_btn_style)
    go_to_extras_btn = ft.ElevatedButton("Extras & AI Chat 🤖", on_click=lambda _: page.go("/extras"), style=nav_btn_style)

    # Header & Nav
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

    # --- Instantinate Cards ---
    temp_card = create_sensor_card("Temperature", "22.5", "°C", COLOR_TEMP, ft.Icons.THERMOSTAT, "BME280 Sensor | Range: -40 to 80°C")
    humidity_card = create_sensor_card("Humidity", "45", "% RH", COLOR_HUM, ft.Icons.WATER_DROP, "BME280 Sensor | Range: 0-100%")

    # Interactive controls setup
    light_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    light_button = ft.ElevatedButton("Turn ON", on_click=on_light_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    light_icon = ft.Icon(ft.Icons.LIGHTBULB, color=COLOR_LIGHT, size=24)
    light_icon_container = ft.Container(content=light_icon, padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_LIGHT), border_radius=12)
    light_card = create_interactive_card("Light", light_status, light_icon_container, "TSL2591 Sensor Controlled", light_button)

    door_status = ft.Text("Door: LOCKED", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    door_button = ft.ElevatedButton("Unlock", on_click=on_door_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_HUM, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    door_icon_container = ft.Container(content=ft.Icon(ft.Icons.LOCK, color=COLOR_HUM, size=24), padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_HUM), border_radius=12)
    door_card = create_interactive_card("Front Door", door_status, door_icon_container, "Smart Lock System", door_button)
    
    # --- VISSZATÉRT KÁRTYÁK ---
    fan_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    fan_button = ft.ElevatedButton("Turn ON", on_click=on_fan_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    fan_icon = ft.Icon(ft.Icons.WIND_POWER, color=COLOR_FAN, size=24)
    fan_icon_container = ft.Container(content=fan_icon, padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_FAN), border_radius=12)
    fan_card = create_interactive_card("Fan", fan_status, fan_icon_container, "DC Motor Control", fan_button)

    rain_status = ft.Text("Rain: NO", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    rain_button = ft.ElevatedButton("Set YES", on_click=on_rain_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    rain_icon = ft.Icon(ft.Icons.WATER, color=COLOR_RAIN, size=24)
    rain_icon_container = ft.Container(content=rain_icon, padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_RAIN), border_radius=12)
    rain_card = create_interactive_card("Rain Detection", rain_status, rain_icon_container, "Rain Sensor Module", rain_button)

    window_status = ft.Text("Window: CLOSED", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    window_button = ft.ElevatedButton("Open", on_click=on_window_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    window_icon = ft.Icon(ft.Icons.WINDOW, color=COLOR_HUM, size=24)
    window_icon_container = ft.Container(content=window_icon, padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_HUM), border_radius=12)
    window_card = create_interactive_card("Window", window_status, window_icon_container, "Smart Window Controller", window_button)


    # --- Final Layout (VISSZATÉRTEK AZ ESZKÖZÖK A LISTÁBA) ---
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
        # Itt adtam hozzá vissza a fan_card, rain_card, window_card elemeket
        ft.Row([light_card, fan_card, rain_card, window_card, door_card], spacing=20, wrap=True, alignment=ft.MainAxisAlignment.START),
    ], scroll=ft.ScrollMode.ADAPTIVE, spacing=0)

    return ft.View(route="/", controls=[content_column], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- PAGE 2: SIMULATED SENSORS (Redesigned Logs) ---
# ==============================================================================
def sensor_view(page: ft.Page):
    global simulation_running, simulation_thread

    # Data storage
    sensor_data_history = [] 
    current_values = {"temp": "22.70", "hum": "42.10", "light": "650"}
    
    # Configuration for layout and styling
    sensor_conf = {
        "temp": {"color": COLOR_TEMP, "icon": ft.Icons.THERMOSTAT, "name": "Temperature", "unit": "°C"},
        "hum": {"color": COLOR_HUM, "icon": ft.Icons.WATER_DROP, "name": "Humidity", "unit": "%RH"},
        "light": {"color": COLOR_LIGHT, "icon": ft.Icons.LIGHTBULB, "name": "Light", "unit": "lux"},
    }
    
    # --- UI Card Creator ---
    def create_metric_card(sensor_key):
        conf = sensor_conf[sensor_key]
        accent = conf["color"]
        
        ts_text = ft.Text("Updated: --:--:--", size=11, color=TEXT_SECONDARY)
        value_text = ft.Text("--", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        unit_text = ft.Text("", size=16, color=TEXT_SECONDARY)

        card = ft.Card(
            elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20, width=250,
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Icon(conf["icon"], color=accent, size=28), padding=10, bgcolor=ft.Colors.with_opacity(0.1, accent), border_radius=12),
                        ft.Column([ft.Text(conf["name"], size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY), ts_text], spacing=2),
                    ], spacing=15),
                    ft.Container(height=20),
                    ft.Row([value_text, unit_text], vertical_alignment=ft.CrossAxisAlignment.END)
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

    # --- Data Table (Redesigned to match image_3.png) ---
    data_table = create_styled_log_table()

    # --- Update Functions ---
    def update_card(sensor_key, value):
        conf = sensor_conf[sensor_key]
        refs = card_refs[sensor_key]
        refs["ts"].value = f"Updated: {datetime.now().strftime('%H:%M:%S')}"
        refs["val"].value = value
        refs["unit"].value = conf["unit"]

    def update_data_table():
        data_table.rows.clear()
        # Show last 10 readings, reversed
        for data in sensor_data_history[-10:][::-1]:
            conf = sensor_conf[data["sensor_key"]]
            # Use the new styled row creator
            row = create_log_row(
                data["time"], 
                conf["name"].upper(), # Name in caps as in image_3.png
                data["value"], 
                conf["unit"], 
                conf["icon"], 
                conf["color"]
            )
            data_table.rows.append(row)

    def update_ui_with_new_data():
        update_card("temp", current_values["temp"])
        update_card("hum", current_values["hum"])
        update_card("light", current_values["light"])
        update_data_table()
        if page: page.update()

    # --- Simulation Thread ---
    def simulate_sensor_data():
        while simulation_running:
            if status_text.value == "RUNNING":
                curr_time = datetime.now().strftime("%H:%M:%S")
                new_temp = f"{round(20 + random.uniform(1, 5), 2):.2f}"
                new_hum = f"{round(40 + random.uniform(1, 10), 2):.2f}"
                new_light = f"{random.randint(500, 800)}"
                
                current_values["temp"] = new_temp
                current_values["hum"] = new_hum
                current_values["light"] = new_light

                # Add to history for the log
                sensor_data_history.append({"time": curr_time, "sensor_key": "temp", "value": new_temp})
                sensor_data_history.append({"time": curr_time, "sensor_key": "hum", "value": new_hum})
                sensor_data_history.append({"time": curr_time, "sensor_key": "light", "value": new_light})
                
                if len(sensor_data_history) > 60: pass # Optional memory trim

                if page:
                    try: page.run_thread(update_ui_with_new_data)
                    except Exception: break
            time.sleep(3)

    # --- Controls ---
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
        ft.Column([ft.Text("Simulated Sensors", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), ft.Text("Real-time data simulation", size=14, color=TEXT_SECONDARY)], spacing=2),
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

    # Start Layout & Simulation
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
# --- PAGE 3: REAL DATA (ThingSpeak API) - REDESIGNED ---
# ==============================================================================
def realtime_data_view(page: ft.Page):
    logger.info("Real-time ThingSpeak view loading...")
    
    current_chart_field = "Field1"
    polling_state = {"is_running": False}
    
    # --- Sensor Configuration based on image_1.png ---
    field_configs = {
        "Field1": {"name": "Temperature", "color": COLOR_TEMP, "icon": ft.Icons.THERMOSTAT, "unit": "°C", "min_y": 10, "max_y": 40},
        "Field2": {"name": "Humidity", "color": COLOR_HUM, "icon": ft.Icons.WATER_DROP, "unit": "%RH", "min_y": 20, "max_y": 90},
        "Field3": {"name": "Soil Moisture", "color": COLOR_SOIL, "icon": ft.Icons.GRASS, "unit": "%", "min_y": 0, "max_y": 100},
        "Field4": {"name": "Rain", "color": COLOR_RAIN, "icon": ft.Icons.WATER, "unit": "mm", "min_y": 0, "max_y": 10},
        "Field5": {"name": "Fan", "color": COLOR_FAN, "icon": ft.Icons.WIND_POWER, "unit": "RPM", "min_y": 0, "max_y": 2000},
        "Field7": {"name": "Light", "color": COLOR_LIGHT, "icon": ft.Icons.LIGHTBULB, "unit": "lux", "min_y": 0, "max_y": 1000},
    }

    # --- UI Elements: Cards ---
    # Placeholders for text references
    txt_refs = {fId: {"val": ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), 
                      "ts": ft.Text("Waiting...", size=11, color=TEXT_SECONDARY)} 
                for fId in field_configs}

    def on_card_clicked(e, field_id):
        nonlocal current_chart_field; current_chart_field = field_id
        config = field_configs[field_id]
        chart_axis_title.value = f"{config['name']} History"
        
        # Update chart styling (color and fill)
        main_chart_series.color = config['color']
        # Add semi-transparent fill below the line
        main_chart_series.below_line_bgcolor = ft.Colors.with_opacity(0.2, config['color'])
        
        main_chart.min_y = config["min_y"]; main_chart.max_y = config["max_y"]
        main_chart.left_axis.labels = generate_y_labels(config["min_y"], config["max_y"])
        main_chart_series.data_points = list(GLOBAL_THINGSPEAK_HISTORY[field_id])
        page.update()

    def create_sensor_card_ui(field_id):
        config = field_configs[field_id]
        accent = config['color']
        val_txt = txt_refs[field_id]["val"]
        ts_txt = txt_refs[field_id]["ts"]

        return ft.Card(
            elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                on_click=lambda e: on_card_clicked(e, field_id),
                padding=20, ink=True, border_radius=CARD_BORDER_RADIUS,
                content=ft.Column([
                        ft.Row([
                            ft.Container(content=ft.Icon(config['icon'], color=accent, size=24), padding=8, bgcolor=ft.Colors.with_opacity(0.1, accent), border_radius=10),
                            ft.Text(f"{config['name']} ({field_id})", size=14, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)
                        ], spacing=10),
                        ft.Container(height=10),
                        ft.Row([val_txt, ft.Text(config["unit"], size=14, color=TEXT_SECONDARY)], vertical_alignment=ft.CrossAxisAlignment.END),
                        ft.Container(height=5),
                        ts_txt,
                    ], spacing=0),
            )
        )

    # --- UI Elements: Log Table (Redesigned to match image_15/16.png) ---
    table = create_styled_log_table()

    table_container = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(padding=20, content=ft.Column([
            ft.Text("Live Data Log", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), 
            ft.Container(height=10), 
            ft.Column([table], scroll=ft.ScrollMode.AUTO, height=300) # Fixed height for scroll
        ]))
    )

    # --- UI Elements: Chart (Redesigned with fill) ---
    initial_config = field_configs[current_chart_field]
    main_chart_series = ft.LineChartData(
        data_points=list(GLOBAL_THINGSPEAK_HISTORY[current_chart_field]),
        stroke_width=4, # Thicker line
        color=initial_config['color'],
        curved=True, # Smooth curves
        stroke_cap_round=True,
        below_line_bgcolor=ft.Colors.with_opacity(0.2, initial_config['color']), # Filled area underneath
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
        bgcolor=CHART_BG_COLOR, border=ft.border.all(0, ft.Colors.TRANSPARENT), tooltip_bgcolor=CARD_BG,
    )
    
    chart_card = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(content=main_chart, height=450, padding=20)
    )

    # --- UI Elements: Controls & Header ---
    def on_home_click(e): stop_polling(None); page.go("/")

    header = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY, on_click=on_home_click),
        ft.Column([ft.Text("IoT Monitor", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), ft.Text("Real-time data from ThingSpeak API", size=14, color=TEXT_SECONDARY)], spacing=2),
    ], alignment=ft.MainAxisAlignment.START)

    status_indicator = ft.Container(width=10, height=10, border_radius=5, bgcolor=TEXT_SECONDARY)
    status_text = ft.Text("Idle", color=TEXT_SECONDARY, size=12)
    
    ctrl_style = ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=15, vertical=10), shape=ft.RoundedRectangleBorder(radius=10))
    start_btn = ft.ElevatedButton("Start Polling API", icon=ft.Icons.CLOUD_DOWNLOAD, style=ctrl_style, bgcolor=COLOR_HUM, color=ft.Colors.WHITE)
    stop_btn = ft.ElevatedButton("Stop", icon=ft.Icons.STOP, disabled=True, style=ctrl_style, bgcolor=COLOR_DANGER, color=ft.Colors.WHITE)

    polling_controls = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(padding=15, content=ft.Row([ft.Row([start_btn, stop_btn]), ft.Row([status_indicator, status_text], spacing=5)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
    )

    # --- Layout (Horizontal: Overview Left, Chart Right, Top Aligned) ---
    overview_cards = [create_sensor_card_ui(fId) for fId in ["Field1", "Field2", "Field7", "Field3"]] # Showing subset initially

    overview_section = ft.Column([
        ft.Text("Dashboard Overview", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        ft.Column(overview_cards, spacing=15), # Stacked vertically
        ft.Container(height=20),
        polling_controls,
        ft.Container(height=20),
        table_container,
    ], spacing=0, expand=4)

    chart_section = ft.Column([
        ft.Text("Sensor History Analysis", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        chart_card,
    ], spacing=0, expand=6)

    main_layout = ft.Column([
        header, ft.Container(height=20),
        # Crucial: vertical_alignment=START ensures top alignment
        ft.Row([overview_section, ft.Container(width=30), chart_section], expand=True, vertical_alignment=ft.VerticalAlignment.START)
    ], expand=True)


    # --- Logic (Data Handling) ---
    def on_message(msg):
        if not isinstance(msg, dict) or msg.get("type") != "sensor": return
        field_id = msg["name"]; value = msg["value"]; ts_raw = msg["ts"]
        
        if field_id not in field_configs: return
        config = field_configs[field_id]

        try:
            dt_obj = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            ts_formatted = dt_obj.strftime("%H:%M:%S")
        except (ValueError, TypeError): ts_formatted = "N/A"

        # Update Card Text
        txt_refs[field_id]["val"].value = str(value)
        txt_refs[field_id]["ts"].value = f"Last update: {ts_formatted}"

        # Update Chart History
        try:
            float_val = float(value)
            target_history = GLOBAL_THINGSPEAK_HISTORY[field_id]
            target_history.append(ft.LineChartDataPoint(len(target_history), float_val))
            if len(target_history) > 10:
                target_history.pop(0)
                for i, p in enumerate(target_history): p.x = i
            if field_id == current_chart_field:
                main_chart_series.data_points = list(target_history)
        except (ValueError, TypeError): pass

        # Update Log Table (using styled row with icon and nice name)
        row = create_log_row(
            ts_formatted,
            config["name"], # Use nice name
            str(value),
            config["unit"],
            config["icon"],
            config["color"]
        )
        table.rows.insert(0, row)
        if len(table.rows) > 50: table.rows.pop()
        if page: page.update()

    page.pubsub.subscribe(on_message)

    async def thingspeak_poller_loop():
        # JAVÍTOTT SOR: Itt használja a visszatett COLOR_WARNING színt
        status_text.value = f"Polling API ({POLL_INTERVAL_SECONDS}s)..."; status_indicator.bgcolor = COLOR_WARNING; page.update()
        async with aiohttp.ClientSession() as session:
            while polling_state["is_running"]:
                try:
                    async with session.get(THINGSPEAK_URL, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            status_text.value = "API Connection: OK"; status_indicator.bgcolor = COLOR_SUCCESS; page.update()
                            ts = data.get("created_at")
                            # Send messages for all configured fields if data exists
                            for fId in field_configs:
                                val = data.get(fId.lower())
                                if val: page.pubsub.send_all({"type": "sensor", "name": fId, "value": val, "ts": ts})
                        else: status_text.value = f"API Error: {response.status}"; status_indicator.bgcolor = COLOR_DANGER; page.update()
                except Exception as e: status_text.value = f"Connection Error: {e}"; status_indicator.bgcolor = COLOR_DANGER; page.update()
                if polling_state["is_running"]: await asyncio.sleep(POLL_INTERVAL_SECONDS)

    def start_polling(_):
        if polling_state["is_running"]: return
        polling_state["is_running"] = True; page.run_task(thingspeak_poller_loop)
        start_btn.disabled = True; stop_btn.disabled = False; page.update()

    def stop_polling(_):
        polling_state["is_running"] = False; status_text.value = "API Poller: Idle"; status_indicator.bgcolor = TEXT_SECONDARY; start_btn.disabled = False; stop_btn.disabled = True; page.update()

    start_btn.on_click = start_polling; stop_btn.on_click = stop_polling

    return ft.View(route="/realdatas", controls=[main_layout], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- PAGE 4: EXTRAS VIEW (Gallery & AI) ---
# ==============================================================================
def extras_view(page: ft.Page):
    
    # --- Tab 1: Gallery ---
    gallery_grid = ft.GridView(expand=True, runs_count=3, max_extent=300, child_aspect_ratio=0.8, spacing=20, run_spacing=20)

    def delete_image(item):
        if item in GALLERY_DATA:
            GALLERY_DATA.remove(item)
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Image deleted!"), bgcolor=COLOR_DANGER))

    def update_gallery_ui():
        gallery_grid.controls.clear()
        for item in GALLERY_DATA:
            date_text = ft.Text(item["date"], size=12, color=TEXT_SECONDARY)
            delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLOR_DANGER, tooltip="Delete", on_click=lambda e, i=item: delete_image(i))
            footer = ft.Row([date_text, delete_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            
            card = ft.Card(elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
                content=ft.Container(padding=10, content=ft.Column([
                        ft.Image(src=item["path"], width=float("inf"), height=180, fit=ft.ImageFit.COVER, border_radius=12),
                        ft.Container(content=footer, padding=ft.padding.only(top=5, left=5, right=5))
                    ], spacing=5)))
            gallery_grid.controls.append(card)
        if not GALLERY_DATA:
            gallery_grid.controls.append(ft.Container(content=ft.Column([
                ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, size=48, color=TEXT_SECONDARY),
                ft.Text("No images uploaded yet.", color=TEXT_SECONDARY)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center, padding=50))
        if page: page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            GALLERY_DATA.insert(0, {"path": e.files[0].path, "date": datetime.now().strftime("%Y-%m-%d %H:%M")})
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Image added successfully!"), bgcolor=COLOR_SUCCESS))

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    upload_btn = ft.ElevatedButton("Upload New Photo", icon=ft.Icons.ADD_A_PHOTO, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=12), bgcolor=COLOR_HUM, color=ft.Colors.WHITE), on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE))

    gallery_tab = ft.Column([ft.Row([ft.Text("Plant Diary (Gallery)", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), upload_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), ft.Container(height=20), gallery_grid], expand=True)

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
        chat_history_for_api.append({"role": "user", "content": prompt})
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(API_URL, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json={"model": MODEL_NAME, "messages": chat_history_for_api, "temperature": 0.7}) as resp:
                    if resp.status == 200:
                        data = await resp.json(); content = data['choices'][0]['message']['content']
                        chat_history_for_api.append({"role": "assistant", "content": content})
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

    # --- Main Layout ---
    tabs = ft.Tabs(selected_index=0, animation_duration=300, indicator_color=COLOR_HUM, label_color=COLOR_HUM, unselected_label_color=TEXT_SECONDARY, divider_color="transparent", tabs=[ft.Tab(text="Gallery", icon=ft.Icons.PHOTO_LIBRARY_OUTLINED, content=ft.Container(content=gallery_tab, padding=ft.padding.only(top=20))), ft.Tab(text="AI Chat", icon=ft.Icons.CHAT_BUBBLE_OUTLINE, content=ft.Container(content=chat_tab, padding=ft.padding.only(top=20)))], expand=True)
    header = ft.Row([ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY, on_click=lambda _: page.go("/")), ft.Text("Extras", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)], alignment=ft.MainAxisAlignment.START)
    
    update_gallery_ui()
    return ft.View(route="/extras", controls=[ft.Column([header, ft.Container(height=10), tabs], expand=True)], bgcolor=BG_COLOR, padding=SECTION_PADDING)

# ==============================================================================
# --- MAIN APP ---
# ==============================================================================
def main(page: ft.Page):
    page.title = "Smart Home Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {"Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf", "RobotoBold": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"}
    page.theme = ft.Theme(font_family="Roboto")

    def route_change(route):
        page.views.clear()
        if page.route == "/": page.views.append(home_view(page))
        elif page.route == "/sensors": page.views.append(sensor_view(page))
        elif page.route == "/extras": page.views.append(extras_view(page))
        elif page.route == "/realdatas": page.views.append(realtime_data_view(page))
        page.update()

    page.on_route_change = route_change
    page.go("/")

ft.app(target=main)