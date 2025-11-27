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
API_KEY = "YOUR_OWN_API_KEY_HERE"
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
    {"role": "system", "content": "You are a helpful assistant in a smart home monitor application. Answer concisely in English."}
]
# Storage for chart history for defined fields
GLOBAL_THINGSPEAK_HISTORY = {
    "Field1": [], "Field2": [], "Field3": [],
    "Field4": [], "Field5": [], "Field7": []
}
simulation_running = False
simulation_thread = None

# --- DÁTUM ÉS IDŐ FORMÁTUMOK (RÖVIDÍTVE) ---
# A naplókhoz csak időt használunk, hogy kiférjen
LOG_TIME_FORMAT = "%H:%M:%S"
# A kártyák frissítéséhez egy kompaktabb dátum+idő
CARD_DATE_FORMAT = "%Y-%m-%d %H:%M"


# ==============================================================================
# --- PROFI UI DESIGN RENDSZER (Modernizált Színek és Stílusok) ---
# ==============================================================================

# Color Palette - Modernized
BG_COLOR = "#F5F7FA"      # Light grey background
CARD_BG = "#FFFFFF"       # White card background
TEXT_PRIMARY = "#1A1A1A"  # Softer black
TEXT_SECONDARY = "#8F9BB3" # Modern cool grey

# Accent Colors for Sensors (Keeping these consistent)
COLOR_TEMP = "#FF3B30"
COLOR_HUM = "#0056D2"
COLOR_LIGHT_SENSOR = "#FF9500"
COLOR_SOIL = "#8D6E63"

# --- PRO DEVICE UI SZÍNEK ---
# Inaktív állapot: Semleges szürke háttér, szürke ikon
COLOR_INACTIVE_BG = "#EDF1F7"
COLOR_INACTIVE_ICON = "#8F9BB3"

# Aktív állapotok (Modern színek)
COLOR_ACTIVE_LIGHT = "#FFC107" # Meleg sárga
COLOR_ACTIVE_DOOR = "#00C853"  # Élénk zöld (Unlocked)
COLOR_ACTIVE_FAN = "#00B0FF"   # Élénk kék
COLOR_ACTIVE_RAIN = "#2962FF"  # Mély kék
COLOR_ACTIVE_WINDOW = "#00E676" # Türkiz zöld

COLOR_DANGER_MODERN = "#FF4757" # Modern piros (pl. Locked, Closed)
COLOR_WARNING = "#FF9500" # Orange (Polling / Busy)

# Style Constants
CARD_ELEVATION = 4 # Kicsit több mélység
CARD_BORDER_RADIUS = 20 # Kerekítettebb sarkok a modernebb hatásért
SECTION_PADDING = 24

# Chart Styles
CHART_BG_COLOR = CARD_BG
AXIS_TITLE_STYLE = ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY)
LABEL_STYLE = ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=TEXT_SECONDARY)

# ==============================================================================
# --- HELPER FUNCTIONS ---
# ==============================================================================
def generate_y_labels(min_val, max_val):
    rng = max_val - min_val
    if rng <= 20: step = 5
    elif rng <= 50: step = 10
    elif rng <= 200: step = 25
    elif rng <= 1000: step = 200
    else: step = 500
    labels = []
    start = (int(min_val) // step) * step
    end = (int(max_val) // step + 1) * step
    curr = start
    while curr <= end:
        labels.append(ft.ChartAxisLabel(value=curr, label=ft.Text(str(int(curr)), style=LABEL_STYLE)))
        curr += step
    return labels

# ==============================================================================
# --- SHARED UI COMPONENTS (MODERN PRO STYLE) ---
# ==============================================================================

def create_styled_log_table():
    """Creates the base DataTable structure matching the modern Pro style."""
    return ft.DataTable(
        heading_row_color=BG_COLOR,
        heading_row_height=50,
        data_row_min_height=60, # Magasabb sorok a modernebb hatáshoz
        border=ft.border.all(1, "#E0E0E0"),
        border_radius=12,
        # Tisztább kinézet, kevesebb vonal
        vertical_lines=ft.border.BorderSide(0, "transparent"),
        horizontal_lines=ft.border.BorderSide(1, "#EEEEEE"),
        columns=[
            # Félkövér fejlécek
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY))
        ],
        rows=[],
    )

def create_log_row(time_str, sensor_name, value_str, unit_str, icon_data, color):
    """Creates a styled DataRow with an icon and bold values for the Pro look."""
    return ft.DataRow(cells=[
        ft.DataCell(ft.Text(time_str, size=13, color=TEXT_PRIMARY)),
        # Sensor cell with icon and bold name
        ft.DataCell(ft.Row([
            ft.Icon(icon_data, color=color, size=18),
            ft.Text(sensor_name, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
        ], spacing=12)),
        # Bold value
        ft.DataCell(ft.Text(value_str, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
        ft.DataCell(ft.Text(unit_str, size=13, color=TEXT_SECONDARY)),
    ])

# ==============================================================================
# --- PAGE 1: HOME DASHBOARD (PROFESSIONAL REDESIGN) ---
# ==============================================================================
def home_view(page: ft.Page):

    # --- UI Card Creator: Sensor ---
    def create_sensor_card(title, value, unit, accent_color, icon_data, details, width=300):
        return ft.Card(
            elevation=CARD_ELEVATION,
            shadow_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=24,
                width=width,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(icon_data, color=accent_color, size=26),
                            padding=12,
                            bgcolor=ft.Colors.with_opacity(0.1, accent_color),
                            border_radius=14,
                        ),
                        ft.Column([
                            ft.Text(title, size=17, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
                            ft.Text("Real-time sensor", size=13, color=TEXT_SECONDARY)
                        ], spacing=2),
                    ], spacing=16),
                    ft.Container(height=18),
                    ft.Row([
                        ft.Text(value, size=38, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY),
                        ft.Text(unit, size=16, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY),
                    ], vertical_alignment=ft.CrossAxisAlignment.END),
                     ft.Container(height=12),
                    ft.Container(
                        content=ft.Text(details, size=12, color=TEXT_SECONDARY, weight=ft.FontWeight.W_500),
                        padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        bgcolor=BG_COLOR,
                        border_radius=10,
                        width=float("inf")
                    ),
                ])
            )
        )

    # --- ÚJ: PROFI INTERAKTÍV KÁRTYA KÉSZÍTŐ (Kapcsolóval és Animációval) ---
    def create_pro_interactive_card(
        title,
        subtitle,
        icon_data,
        initial_state_bool, # True/False
        on_toggle_callback, # A függvény, amit a kapcsoló hív
        active_color, # Az a szín, ami aktív állapotban megjelenik
        status_text_control, # A szöveg control referenciája
        icon_control, # Az ikon control referenciája
        icon_container_control, # Az ikon konténer referenciája
        width=300
    ):
        initial_switch_value = initial_state_bool
        
        toggle_switch = ft.Switch(
            value=initial_switch_value,
            on_change=on_toggle_callback,
            active_color=active_color,
            inactive_thumb_color=TEXT_SECONDARY,
            inactive_track_color=COLOR_INACTIVE_BG,
        )

        return ft.Card(
            elevation=CARD_ELEVATION,
            shadow_color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=24,
                width=width,
                content=ft.Column([
                    ft.Row([
                        icon_container_control,
                        ft.Column([
                            ft.Text(title, size=17, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY),
                            ft.Text(subtitle, size=13, color=TEXT_SECONDARY)
                        ], spacing=2, expand=True),
                    ], spacing=16),
                    
                    ft.Container(height=20),
                    
                    ft.Row([
                        ft.Column([
                             ft.Text("STATUS", size=11, weight=ft.FontWeight.BOLD, color=TEXT_SECONDARY),
                             status_text_control
                        ]),
                        toggle_switch
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ])
            )
        )

    # --- Eseménykezelők ---
    
    SMOOTH_ANIMATION = ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)

    def on_light_toggle(e):
        is_on = e.control.value
        if is_on:
            light_status_text.value = "ON"
            light_status_text.color = COLOR_ACTIVE_LIGHT
            light_icon_container.bgcolor = ft.Colors.with_opacity(0.2, COLOR_ACTIVE_LIGHT)
            light_icon.color = COLOR_ACTIVE_LIGHT
        else:
            light_status_text.value = "OFF"
            light_status_text.color = TEXT_SECONDARY
            light_icon_container.bgcolor = COLOR_INACTIVE_BG
            light_icon.color = COLOR_INACTIVE_ICON
        page.update()

    def on_door_toggle(e):
        is_unlocked = e.control.value
        if is_unlocked:
            door_status_text.value = "UNLOCKED"
            door_status_text.color = COLOR_ACTIVE_DOOR
            door_icon_container.bgcolor = ft.Colors.with_opacity(0.2, COLOR_ACTIVE_DOOR)
            door_icon.color = COLOR_ACTIVE_DOOR
            door_icon.name = ft.Icons.LOCK_OPEN_ROUNDED
        else:
            door_status_text.value = "LOCKED"
            door_status_text.color = COLOR_DANGER_MODERN
            door_icon_container.bgcolor = COLOR_INACTIVE_BG
            door_icon.color = COLOR_DANGER_MODERN
            door_icon.name = ft.Icons.LOCK_ROUNDED
        page.update()

    def on_fan_toggle(e):
        is_on = e.control.value
        if is_on:
            fan_status_text.value = "ACTIVE"
            fan_status_text.color = COLOR_ACTIVE_FAN
            fan_icon_container.bgcolor = ft.Colors.with_opacity(0.2, COLOR_ACTIVE_FAN)
            fan_icon.color = COLOR_ACTIVE_FAN
        else:
            fan_status_text.value = "INACTIVE"
            fan_status_text.color = TEXT_SECONDARY
            fan_icon_container.bgcolor = COLOR_INACTIVE_BG
            fan_icon.color = COLOR_INACTIVE_ICON
        page.update()

    def on_rain_toggle(e):
        is_raining = e.control.value
        if is_raining:
            rain_status_text.value = "DETECTED"
            rain_status_text.color = COLOR_ACTIVE_RAIN
            rain_icon_container.bgcolor = ft.Colors.with_opacity(0.2, COLOR_ACTIVE_RAIN)
            rain_icon.color = COLOR_ACTIVE_RAIN
        else:
            rain_status_text.value = "CLEAR"
            rain_status_text.color = TEXT_SECONDARY
            rain_icon_container.bgcolor = COLOR_INACTIVE_BG
            rain_icon.color = COLOR_INACTIVE_ICON
        page.update()

    def on_window_toggle(e):
        is_open = e.control.value
        if is_open:
            window_status_text.value = "OPEN"
            window_status_text.color = COLOR_ACTIVE_WINDOW
            window_icon_container.bgcolor = ft.Colors.with_opacity(0.2, COLOR_ACTIVE_WINDOW)
            window_icon.color = COLOR_ACTIVE_WINDOW
        else:
            window_status_text.value = "CLOSED"
            window_status_text.color = COLOR_DANGER_MODERN
            window_icon_container.bgcolor = COLOR_INACTIVE_BG
            window_icon.color = COLOR_DANGER_MODERN
        page.update()


    # --- Controls Setup ---

    # Light Controls
    light_status_text = ft.Text("OFF", size=16, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY)
    light_icon = ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=COLOR_INACTIVE_ICON, size=28)
    light_icon_container = ft.Container(content=light_icon, padding=12, bgcolor=COLOR_INACTIVE_BG, border_radius=14, animate=SMOOTH_ANIMATION)
    
    light_card = create_pro_interactive_card(
        "Smart Light", "Living Room", ft.Icons.LIGHTBULB_ROUNDED, False, on_light_toggle, COLOR_ACTIVE_LIGHT,
        light_status_text, light_icon, light_icon_container
    )

    # Door Controls
    door_status_text = ft.Text("LOCKED", size=16, weight=ft.FontWeight.W_700, color=COLOR_DANGER_MODERN)
    door_icon = ft.Icon(ft.Icons.LOCK_ROUNDED, color=COLOR_DANGER_MODERN, size=28)
    door_icon_container = ft.Container(content=door_icon, padding=12, bgcolor=COLOR_INACTIVE_BG, border_radius=14, animate=SMOOTH_ANIMATION)

    door_card = create_pro_interactive_card(
        "Front Door", "Main Entrance", ft.Icons.LOCK_ROUNDED, False, on_door_toggle, COLOR_ACTIVE_DOOR,
        door_status_text, door_icon, door_icon_container
    )

    # Fan Controls
    fan_status_text = ft.Text("INACTIVE", size=16, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY)
    fan_icon = ft.Icon(ft.Icons.MODE_FAN_OFF_ROUNDED, color=COLOR_INACTIVE_ICON, size=28)
    fan_icon_container = ft.Container(content=fan_icon, padding=12, bgcolor=COLOR_INACTIVE_BG, border_radius=14, animate=SMOOTH_ANIMATION)
    
    fan_card = create_pro_interactive_card(
        "Air Purifier", "Bedroom", ft.Icons.MODE_FAN_OFF_ROUNDED, False, on_fan_toggle, COLOR_ACTIVE_FAN,
        fan_status_text, fan_icon, fan_icon_container
    )

    # Rain Controls
    rain_status_text = ft.Text("CLEAR", size=16, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY)
    rain_icon = ft.Icon(ft.Icons.WATER_DROP_ROUNDED, color=COLOR_INACTIVE_ICON, size=28)
    rain_icon_container = ft.Container(content=rain_icon, padding=12, bgcolor=COLOR_INACTIVE_BG, border_radius=14, animate=SMOOTH_ANIMATION)
    
    rain_card = create_pro_interactive_card(
        "Rain Sensor", "Garden Module", ft.Icons.WATER_DROP_ROUNDED, False, on_rain_toggle, COLOR_ACTIVE_RAIN,
        rain_status_text, rain_icon, rain_icon_container
    )

    # Window Controls
    window_status_text = ft.Text("CLOSED", size=16, weight=ft.FontWeight.W_700, color=COLOR_DANGER_MODERN)
    window_icon = ft.Icon(ft.Icons.WINDOW_ROUNDED, color=COLOR_DANGER_MODERN, size=28)
    window_icon_container = ft.Container(content=window_icon, padding=12, bgcolor=COLOR_INACTIVE_BG, border_radius=14, animate=SMOOTH_ANIMATION)
    
    window_card = create_pro_interactive_card(
        "Window Actuator", "Kitchen", ft.Icons.WINDOW_ROUNDED, False, on_window_toggle, COLOR_ACTIVE_WINDOW,
        window_status_text, window_icon, window_icon_container
    )

    # --- Sensor Cards ---
    temp_card = create_sensor_card("Temperature", "22.5", "°C", COLOR_TEMP, ft.Icons.THERMOSTAT_ROUNDED, "DHT22 Sensor | Avg: 22°C")
    humidity_card = create_sensor_card("Humidity", "45", "% RH", COLOR_HUM, ft.Icons.WATER_DROP_ROUNDED, "DHT22 Sensor | Optimal")

    # --- Navigation Buttons ---
    nav_btn_style = ft.ButtonStyle(
        color=ft.Colors.WHITE,
        bgcolor="#212121",
        padding=ft.padding.symmetric(horizontal=20, vertical=16),
        shape=ft.RoundedRectangleBorder(radius=12),
        elevation=0,
        overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
    )
    
    go_to_sensors_btn = ft.ElevatedButton("Simulation 📊", on_click=lambda _: page.go("/sensors"), style=nav_btn_style, icon=ft.Icons.ANALYTICS_ROUNDED)
    go_to_real_datas_btn = ft.ElevatedButton("Real Data 📈", on_click=lambda _: page.go("/realdatas"), style=nav_btn_style, icon=ft.Icons.CLOUD_SYNC_ROUNDED)
    go_to_extras_btn = ft.ElevatedButton("Extras & AI 🤖", on_click=lambda _: page.go("/extras"), style=nav_btn_style, icon=ft.Icons.SMART_TOY_ROUNDED)

    # Header & Nav
    header = ft.Container(
        content=ft.Column([
            ft.Text("Smart Home Pro", style=ft.TextStyle(size=34, weight=ft.FontWeight.W_900, color=TEXT_PRIMARY, letter_spacing=-0.5)),
            ft.Text("Control Panel & Overview", size=16, weight=ft.FontWeight.W_500, color=TEXT_SECONDARY),
        ], horizontal_alignment=ft.CrossAxisAlignment.START),
        margin=ft.margin.only(bottom=25, top=10),
        alignment=ft.alignment.center_left
    )

    nav_row = ft.Container(
        content=ft.Row([go_to_sensors_btn, go_to_real_datas_btn, go_to_extras_btn], spacing=12, alignment=ft.MainAxisAlignment.START),
        margin=ft.margin.only(bottom=35)
    )

    # --- Final Layout ---
    section_title_style = ft.TextStyle(size=22, weight=ft.FontWeight.W_800, color=TEXT_PRIMARY)
    
    content_column = ft.Column([
        header,
        nav_row,
        ft.Text("Environment", style=section_title_style),
        ft.Container(height=15),
        ft.Row([temp_card, humidity_card], spacing=20, wrap=True, alignment=ft.MainAxisAlignment.START),
        ft.Container(height=35),
        ft.Text("Devices & Security", style=section_title_style),
        ft.Container(height=15),
        ft.Row([light_card, door_card, window_card, fan_card, rain_card], spacing=20, run_spacing=20, wrap=True, alignment=ft.MainAxisAlignment.START),
    ], scroll=ft.ScrollMode.ADAPTIVE, spacing=0)

    return ft.View(route="/", controls=[content_column], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)


# ==============================================================================
# --- PAGE 2: SIMULATED SENSORS (Redesigned Logs with Short Date) ---
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
        "light": {"color": COLOR_LIGHT_SENSOR, "icon": ft.Icons.LIGHTBULB, "name": "Light", "unit": "lux"},
    }
    
    # --- UI Card Creator (Pro Style) ---
    def create_metric_card(sensor_key):
        conf = sensor_conf[sensor_key]
        accent = conf["color"]
        
        ts_text = ft.Text("Updated: --:--", size=11, color=TEXT_SECONDARY)
        value_text = ft.Text("--", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        unit_text = ft.Text("", size=16, color=TEXT_SECONDARY)

        card = ft.Card(
            elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=24, width=280, # Slightly wider for Pro look
                content=ft.Column([
                    ft.Row([
                        ft.Container(content=ft.Icon(conf["icon"], color=accent, size=28), padding=12, bgcolor=ft.Colors.with_opacity(0.1, accent), border_radius=14),
                        ft.Column([ft.Text(conf["name"], size=17, weight=ft.FontWeight.W_700, color=TEXT_PRIMARY), ts_text], spacing=2),
                    ], spacing=16),
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

    # --- Data Table (Using the Pro style) ---
    data_table = create_styled_log_table()

    # --- Update Functions ---
    def update_card(sensor_key, value):
        conf = sensor_conf[sensor_key]
        refs = card_refs[sensor_key]
        # MÓDOSÍTÁS: Kompakt dátum a kártyán
        refs["ts"].value = f"Updated: {datetime.now().strftime(CARD_DATE_FORMAT)}"
        refs["val"].value = value
        refs["unit"].value = conf["unit"]

    def update_data_table():
        data_table.rows.clear()
        # Show last 10 readings, reversed
        for data in sensor_data_history[-10:][::-1]:
            conf = sensor_conf[data["sensor_key"]]
            # Use the Pro styled row creator
            row = create_log_row(
                data["time"], 
                conf["name"].upper(), # Name in caps for Pro style
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
                # MÓDOSÍTÁS: Csak idő a naplóhoz (rövid)
                curr_time = datetime.now().strftime(LOG_TIME_FORMAT)
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
                
                if len(sensor_data_history) > 60: pass

                # JAVÍTOTT RÉSZ: Külön sorokba tördelve
                if page:
                    try:
                        page.run_thread(update_ui_with_new_data)
                    except Exception:
                        break
            time.sleep(3)

    # --- Controls (Pro Style) ---
    def on_start_click(e):
        start_btn.disabled = True; stop_btn.disabled = False; status_indicator.bgcolor = COLOR_ACTIVE_DOOR; status_text.value = "RUNNING"; status_text.color=COLOR_ACTIVE_DOOR; page.update()
    def on_stop_click(e):
        start_btn.disabled = False; stop_btn.disabled = True; status_indicator.bgcolor = COLOR_DANGER_MODERN; status_text.value = "STOPPED"; status_text.color=COLOR_DANGER_MODERN; page.update()
    def on_home_click(e):
        global simulation_running; simulation_running = False; page.go("/")

    status_indicator = ft.Container(width=12, height=12, border_radius=6, bgcolor=COLOR_ACTIVE_DOOR, animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT))
    status_text = ft.Text("RUNNING", size=14, weight=ft.FontWeight.BOLD, color=COLOR_ACTIVE_DOOR)
    
    ctrl_btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), padding=15)
    start_btn = ft.ElevatedButton("Start", icon=ft.Icons.PLAY_ARROW_ROUNDED, on_click=on_start_click, disabled=True, bgcolor=COLOR_ACTIVE_DOOR, color=ft.Colors.WHITE, style=ctrl_btn_style)
    stop_btn = ft.ElevatedButton("Stop", icon=ft.Icons.STOP_ROUNDED, on_click=on_stop_click, bgcolor=COLOR_DANGER_MODERN, color=ft.Colors.WHITE, style=ctrl_btn_style)
    
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
# --- PAGE 3: REAL DATA (ThingSpeak API) - REDESIGNED WITH PRO STYLE & SHORT DATES ---
# ==============================================================================
def realtime_data_view(page: ft.Page):
    logger.info("Real-time ThingSpeak view loading...")
    
    current_chart_field = "Field1"
    polling_state = {"is_running": False}
    
    # --- Sensor Configuration (Using Pro Active Colors) ---
    field_configs = {
        "Field1": {"name": "Temperature", "color": COLOR_TEMP, "icon": ft.Icons.THERMOSTAT_ROUNDED, "unit": "°C", "min_y": 10, "max_y": 40},
        "Field2": {"name": "Humidity", "color": COLOR_HUM, "icon": ft.Icons.WATER_DROP_ROUNDED, "unit": "%RH", "min_y": 20, "max_y": 90},
        "Field3": {"name": "Soil Moisture", "color": COLOR_SOIL, "icon": ft.Icons.GRASS_ROUNDED, "unit": "%", "min_y": 0, "max_y": 100},
        "Field4": {"name": "Rain", "color": COLOR_ACTIVE_RAIN, "icon": ft.Icons.WATER_DROP_ROUNDED, "unit": "mm", "min_y": 0, "max_y": 10},
        "Field5": {"name": "Fan", "color": COLOR_ACTIVE_FAN, "icon": ft.Icons.MODE_FAN_OFF_ROUNDED, "unit": "RPM", "min_y": 0, "max_y": 2000},
        "Field7": {"name": "Light", "color": COLOR_LIGHT_SENSOR, "icon": ft.Icons.LIGHTBULB_ROUNDED, "unit": "lux", "min_y": 0, "max_y": 1000},
    }

    # --- UI Elements: Cards (Pro Style) ---
    txt_refs = {fId: {"val": ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), 
                      "ts": ft.Text("Waiting...", size=11, color=TEXT_SECONDARY)} 
                for fId in field_configs}

    def on_card_clicked(e, field_id):
        nonlocal current_chart_field; current_chart_field = field_id
        config = field_configs[field_id]
        chart_axis_title.value = f"{config['name']} History"
        main_chart_series.color = config['color']
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
                padding=24, ink=True, border_radius=CARD_BORDER_RADIUS, # Wider padding for Pro style
                content=ft.Column([
                        ft.Row([
                            ft.Container(content=ft.Icon(config['icon'], color=accent, size=26), padding=12, bgcolor=ft.Colors.with_opacity(0.1, accent), border_radius=14),
                            ft.Text(f"{config['name']} ({field_id})", size=16, weight=ft.FontWeight.W_700, color=TEXT_SECONDARY) # Bold title
                        ], spacing=12),
                        ft.Container(height=12),
                        ft.Row([val_txt, ft.Text(config["unit"], size=16, color=TEXT_SECONDARY, weight=ft.FontWeight.W_600)], vertical_alignment=ft.CrossAxisAlignment.END),
                        ft.Container(height=8),
                        ts_txt,
                    ], spacing=0),
            )
        )

    # --- UI Elements: Log Table (Using the Pro style) ---
    table = create_styled_log_table()

    table_container = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(padding=20, content=ft.Column([
            ft.Text("Live Data Log", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), 
            ft.Container(height=10), 
            ft.Column([table], scroll=ft.ScrollMode.AUTO, height=300)
        ]))
    )

    # --- UI Elements: Chart ---
    initial_config = field_configs[current_chart_field]
    main_chart_series = ft.LineChartData(
        data_points=list(GLOBAL_THINGSPEAK_HISTORY[current_chart_field]),
        stroke_width=4,
        color=initial_config['color'],
        curved=True,
        stroke_cap_round=True,
        below_line_bgcolor=ft.Colors.with_opacity(0.2, initial_config['color']),
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

    status_indicator = ft.Container(width=12, height=12, border_radius=6, bgcolor=TEXT_SECONDARY, animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT))
    status_text = ft.Text("Idle", color=TEXT_SECONDARY, size=14, weight=ft.FontWeight.BOLD)
    
    ctrl_style = ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=20, vertical=12), shape=ft.RoundedRectangleBorder(radius=12))
    start_btn = ft.ElevatedButton("Start Polling API", icon=ft.Icons.CLOUD_DOWNLOAD_ROUNDED, style=ctrl_style, bgcolor=COLOR_ACTIVE_DOOR, color=ft.Colors.WHITE)
    stop_btn = ft.ElevatedButton("Stop", icon=ft.Icons.STOP_ROUNDED, disabled=True, style=ctrl_style, bgcolor=COLOR_DANGER_MODERN, color=ft.Colors.WHITE)

    polling_controls = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(padding=20, content=ft.Row([ft.Row([start_btn, stop_btn], spacing=10), ft.Row([status_indicator, status_text], spacing=8, alignment=ft.MainAxisAlignment.CENTER)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
    )

    # --- Layout ---
    overview_cards = [create_sensor_card_ui(fId) for fId in ["Field1", "Field2", "Field7", "Field3"]]

    overview_section = ft.Column([
        ft.Text("Dashboard Overview", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        ft.Column(overview_cards, spacing=15),
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
            # MÓDOSÍTÁS: Rövid idő a naplóhoz
            ts_log = dt_obj.strftime(LOG_TIME_FORMAT)
            # MÓDOSÍTÁS: Kompakt dátum a kártyához
            ts_card = dt_obj.strftime(CARD_DATE_FORMAT)
        except (ValueError, TypeError): ts_log = "N/A"; ts_card = "N/A"

        # Update Card Text
        txt_refs[field_id]["val"].value = str(value)
        txt_refs[field_id]["ts"].value = f"Last update: {ts_card}"

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

        # Update Log Table (using Pro row style)
        row = create_log_row(
            ts_log, # Using short time
            config["name"].upper(), # Name in caps for Pro style
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
        status_text.value = f"Polling API ({POLL_INTERVAL_SECONDS}s)..."; status_indicator.bgcolor = COLOR_WARNING; page.update()
        async with aiohttp.ClientSession() as session:
            while polling_state["is_running"]:
                try:
                    async with session.get(THINGSPEAK_URL, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            status_text.value = "API Connection: OK"; status_indicator.bgcolor = COLOR_ACTIVE_DOOR; page.update()
                            ts = data.get("created_at")
                            for fId in field_configs:
                                val = data.get(fId.lower())
                                if val: page.pubsub.send_all({"type": "sensor", "name": fId, "value": val, "ts": ts})
                        else: status_text.value = f"API Error: {response.status}"; status_indicator.bgcolor = COLOR_DANGER_MODERN; page.update()
                except Exception as e: status_text.value = f"Connection Error: {e}"; status_indicator.bgcolor = COLOR_DANGER_MODERN; page.update()
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
            page.show_snack_bar(ft.SnackBar(ft.Text("Image deleted!"), bgcolor=COLOR_DANGER_MODERN))

    def update_gallery_ui():
        gallery_grid.controls.clear()
        for item in GALLERY_DATA:
            date_text = ft.Text(item["date"], size=12, color=TEXT_SECONDARY)
            delete_btn = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color=COLOR_DANGER_MODERN, tooltip="Delete", on_click=lambda e, i=item: delete_image(i))
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
            # MÓDOSÍTÁS: Kompakt dátum a galériához
            GALLERY_DATA.insert(0, {"path": e.files[0].path, "date": datetime.now().strftime(CARD_DATE_FORMAT)})
            update_gallery_ui()
            page.show_snack_bar(ft.SnackBar(ft.Text("Image added successfully!"), bgcolor=COLOR_ACTIVE_DOOR))

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    upload_btn = ft.ElevatedButton("Upload New Photo", icon=ft.Icons.ADD_A_PHOTO_ROUNDED, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=12), bgcolor=COLOR_HUM, color=ft.Colors.WHITE), on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE))

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
    page.theme = ft.Theme(font_family="Roboto", visual_density=ft.VisualDensity.COMFORTABLE)

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