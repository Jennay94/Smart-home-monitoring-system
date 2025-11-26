# Flet Pub/Sub Sensor Dashboard - ThingSpeak Integration (V10b - ELEVATION NÉLKÜL)
# -----------------------------------------
# Features:
# - Async data fetching from ThingSpeak API (Fields 1, 2, 7)
# - Real-time UI updates using pubsub
# - Event log table
# - INTERACTIVE CHART: Click cards to switch history.
# - TUNED Y-AXIS RANGES: Optimized for typical smart home values.
# - *** COMPATIBILITY FIX ***: Removed 'elevation' from Container for older Flet versions.
# -----------------------------------------
import flet as ft
import asyncio
import aiohttp
from datetime import datetime
import logging

# --- THINGSPEAK CONFIGURATION ---
THINGSPEAK_CHANNEL_ID = "3156213"
THINGSPEAK_READ_KEY = "WXM1B5P9O2XBKKMS"
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json?api_key={THINGSPEAK_READ_KEY}"
POLL_INTERVAL_SECONDS = 15

# Logolás
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- STÍLUS KONSTANSOK ---
CHART_BG_COLOR = ft.Colors.WHITE
GRID_COLOR = ft.Colors.GREY_100
AXIS_TITLE_COLOR = ft.Colors.GREY_800
LABEL_COLOR = ft.Colors.GREY_600
LABEL_STYLE = ft.TextStyle(size=12, weight=ft.FontWeight.W_500, color=LABEL_COLOR)
AXIS_TITLE_STYLE = ft.TextStyle(size=14, weight=ft.FontWeight.BOLD, color=AXIS_TITLE_COLOR)

# --- SEGÉDFÜGGVÉNY: Y-tengely címkék generálása ---
def generate_y_labels(min_val, max_val):
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

def main(page: ft.Page):
    page.title = "Sensor Monitor (V10b Compatible)"
    page.padding = 24
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F5F7F9"

    logger.info("App starting...")

    # --- GRAFIKON ÁLLAPOT KEZELÉS ---
    current_chart_field = "Field1"

    # --- KONFIGURÁCIÓ ---
    field_configs = {
        "Field1": { "name": "Temperature", "color": ft.Colors.BLUE, "icon": ft.Icons.THERMOSTAT, "min_y": 15, "max_y": 35 },
        "Field2": { "name": "Humidity", "color": ft.Colors.TEAL, "icon": ft.Icons.WATER_DROP, "min_y": 30, "max_y": 80 },
        "Field7": { "name": "Light", "color": ft.Colors.AMBER, "icon": ft.Icons.LIGHT_MODE, "min_y": 0, "max_y": 1000 },
    }

    # ADAT ELŐZMÉNYEK
    history_data = { "Field1": [], "Field2": [], "Field7": [] }

    # ---------------------------------------------------------------------
    # 1. Sensor card widgets
    # ---------------------------------------------------------------------
    temp_value = ft.Text("—", size=28, weight=ft.FontWeight.BOLD)
    temp_ts = ft.Text("Waiting...", size=12, color=ft.Colors.GREY_500)
    hum_value = ft.Text("—", size=28, weight=ft.FontWeight.BOLD)
    hum_ts = ft.Text("", size=12, color=ft.Colors.GREY_500)
    light_value = ft.Text("—", size=28, weight=ft.FontWeight.BOLD)
    light_ts = ft.Text("", size=12, color=ft.Colors.GREY_500)

    # --- Kártya kattintás kezelő ---
    def on_card_clicked(e, field_id):
        nonlocal current_chart_field
        current_chart_field = field_id
        config = field_configs[field_id]
        
        chart_axis_title.value = f"{config['name']} History"
        main_chart_series.color = config['color']
        main_chart_series.below_line_bgcolor = ft.Colors.with_opacity(0.1, config['color'])
        
        main_chart.min_y = config["min_y"]
        main_chart.max_y = config["max_y"]
        main_chart.left_axis.labels = generate_y_labels(config["min_y"], config["max_y"])

        main_chart_series.data_points = list(history_data[field_id])
        page.update()

    # --- sensor_card függvény ---
    def sensor_card(title: str, big_text: ft.Text, ts_text: ft.Text, unit_hint: str, field_id: str):
        config = field_configs[field_id]
        # A Card-nak lehet elevation-ja
        return ft.Card(
            elevation=2,
            color=ft.Colors.WHITE,
            content=ft.Container(
                on_click=lambda e: on_card_clicked(e, field_id),
                padding=20,
                ink=True,
                border_radius=12,
                content=ft.Column(
                    [
                        ft.Row([
                            ft.Container(content=ft.Icon(config['icon'], color=config['color']), padding=8, bgcolor=ft.Colors.with_opacity(0.1, config['color']), border_radius=8),
                            ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=AXIS_TITLE_COLOR)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=10),
                        big_text,
                        ft.Row([ft.Text(unit_hint, size=12, color=LABEL_COLOR), ts_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ],
                    spacing=0,
                ),
            )
        )

    # ---------------------------------------------------------------------
    # 2. Event log table
    # ---------------------------------------------------------------------
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.BOLD, color=AXIS_TITLE_COLOR)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.BOLD, color=AXIS_TITLE_COLOR)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.BOLD, color=AXIS_TITLE_COLOR)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.BOLD, color=AXIS_TITLE_COLOR))
        ],
        rows=[],
        heading_row_color=ft.Colors.GREY_50,
        heading_row_height=40,
        data_row_min_height=35,
        border=ft.border.all(1, ft.Colors.GREY_200),
        border_radius=8,
        vertical_lines=ft.border.BorderSide(0, ft.Colors.TRANSPARENT),
        horizontal_lines=ft.border.BorderSide(1, ft.Colors.GREY_100),
    )
    table_container = ft.Container(
        content=ft.Column([table], scroll=ft.ScrollMode.AUTO),
        height=300, bgcolor=ft.Colors.WHITE, border_radius=12, padding=0,
        # JAVÍTÁS: elevation kivéve innen
        border=ft.border.all(1, ft.Colors.GREY_200)
    )

    # ---------------------------------------------------------------------
    # 3. Chart
    # ---------------------------------------------------------------------
    initial_config = field_configs[current_chart_field]

    main_chart_series = ft.LineChartData(
        data_points=history_data[current_chart_field],
        stroke_width=3, color=initial_config['color'],
        curved=True, stroke_cap_round=True,
        below_line_bgcolor=ft.Colors.with_opacity(0.1, initial_config['color']),
    )
    
    chart_axis_title = ft.Text(f"{initial_config['name']} History", style=AXIS_TITLE_STYLE)
    chart_grid_lines = ft.ChartGridLines(interval=1, color=GRID_COLOR, width=1, dash_pattern=[5, 5])
    
    initial_y_labels = generate_y_labels(initial_config["min_y"], initial_config["max_y"])
    x_labels = [ft.ChartAxisLabel(value=i, label=ft.Text(str(i), style=LABEL_STYLE)) for i in range(10)]

    main_chart = ft.LineChart(
        data_series=[main_chart_series],
        min_x=0, max_x=9,
        min_y=initial_config["min_y"], max_y=initial_config["max_y"],
        interactive=True, expand=True,
        left_axis=ft.ChartAxis(title=chart_axis_title, labels=initial_y_labels, labels_size=40),
        bottom_axis=ft.ChartAxis(title=ft.Text("Last 10 Readings Index", style=AXIS_TITLE_STYLE), labels=x_labels, labels_interval=1),
        horizontal_grid_lines=chart_grid_lines, vertical_grid_lines=chart_grid_lines,
        bgcolor=CHART_BG_COLOR, border=ft.border.all(0, ft.Colors.TRANSPARENT),
        tooltip_bgcolor=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
    )
    
    chart_container = ft.Container(
        content=main_chart, height=400, padding=ft.padding.all(20), bgcolor=ft.Colors.WHITE,
        # JAVÍTÁS: elevation kivéve innen
        border_radius=16, expand=True, border=ft.border.all(1, ft.Colors.GREY_200)
    )

    # ---------------------------------------------------------------------
    # 4. Buttons & Layout
    # ---------------------------------------------------------------------
    start_btn = ft.ElevatedButton("Start polling API", icon=ft.Icons.CLOUD_DOWNLOAD, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)))
    stop_btn = ft.OutlinedButton("Stop", icon=ft.Icons.STOP, disabled=True, style=ft.ButtonStyle(padding=15, shape=ft.RoundedRectangleBorder(radius=10)))
    status_indicator = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREY_300, size=12)
    status_text = ft.Text("API Poller: idle", color=LABEL_COLOR)

    col1 = ft.Column(
        [
            ft.Text("Dashboard Overview", size=24, weight=ft.FontWeight.BOLD, color=AXIS_TITLE_COLOR),
            ft.Row(
                [
                    sensor_card("Temp (F1)", temp_value, temp_ts, "°C", "Field1"),
                    sensor_card("Humidity (F2)", hum_value, hum_ts, "%RH", "Field2"),
                    sensor_card("Light (F7)", light_value, light_ts, "Lux", "Field7"),
                ],
                spacing=15, wrap=True,
            ),
            ft.Container(height=10),
            ft.Row([start_btn, stop_btn, ft.Container(width=10), status_indicator, status_text], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.Text("Recent Activity Log", size=18, weight=ft.FontWeight.W_600, color=AXIS_TITLE_COLOR),
            table_container,
        ], spacing=10, expand=2,
    )

    col2 = ft.Column(
        [
            ft.Text("Sensor History Analysis", size=20, weight=ft.FontWeight.W_600, color=AXIS_TITLE_COLOR),
            chart_container,
        ], spacing=10, expand=3,
    )

    page.add(ft.Row([col1, ft.Container(width=20), col2], expand=True, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.VerticalAlignment.START))

    # ---------------------------------------------------------------------
    # 8. Subscriber
    # ---------------------------------------------------------------------
    def on_message(msg):
        if not isinstance(msg, dict) or msg.get("type") != "sensor": return
        name = msg["name"]; value = msg["value"]; unit = msg["unit"]; ts_raw = msg["ts"]
        try:
            dt_obj = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            ts_formatted = dt_obj.strftime("%H:%M:%S")
        except (ValueError, TypeError): ts_formatted = "N/A"

        # Kártyák frissítése
        if name == "Field1": temp_value.value = f"{value} {unit}"; temp_ts.value = ts_formatted
        elif name == "Field2": hum_value.value = f"{value} {unit}"; hum_ts.value = ts_formatted
        elif name == "Field7": light_value.value = f"{value} {unit}"; light_ts.value = ts_formatted

        # Adat mentése és grafikon frissítése
        try:
            float_val = float(value)
            if name in history_data:
                target_history = history_data[name]
                target_history.append(ft.LineChartDataPoint(len(target_history), float_val))
                if len(target_history) > 10:
                    target_history.pop(0)
                    for i, p in enumerate(target_history): p.x = i
                if name == current_chart_field:
                    main_chart_series.data_points = list(target_history)
        except (ValueError, TypeError): pass

        # Napló frissítése
        table.rows.insert(0, ft.DataRow([ft.DataCell(ft.Text(ts_formatted, color=LABEL_COLOR)), ft.DataCell(ft.Text(name, weight=ft.FontWeight.W_500)), ft.DataCell(ft.Text(str(value), weight=ft.FontWeight.BOLD)), ft.DataCell(ft.Text(unit, color=LABEL_COLOR))]))
        if len(table.rows) > 100: table.rows.pop()
        page.update()

    page.pubsub.subscribe(on_message)

    # ---------------------------------------------------------------------
    # 9. ThingSpeak API Poller
    # ---------------------------------------------------------------------
    running = {"flag": False}
    poller_task = None

    async def thingspeak_poller_loop():
        status_text.value = f"Polling ({POLL_INTERVAL_SECONDS}s)..."; status_indicator.color = ft.Colors.AMBER; page.update()
        async with aiohttp.ClientSession() as session:
            while running["flag"]:
                try:
                    async with session.get(THINGSPEAK_URL, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            status_text.value = "Online"; status_indicator.color = ft.Colors.GREEN; page.update()
                            ts = data.get("created_at")
                            f1 = data.get("field1"); f2 = data.get("field2"); f7 = data.get("field7")
                            if f1: page.pubsub.send_all({"type": "sensor", "name": "Field1", "value": f1, "unit": "°C", "ts": ts})
                            if f2: page.pubsub.send_all({"type": "sensor", "name": "Field2", "value": f2, "unit": "%RH", "ts": ts})
                            if f7: page.pubsub.send_all({"type": "sensor", "name": "Field7", "value": f7, "unit": "Lux", "ts": ts})
                        else: status_text.value = f"Error: {response.status}"; status_indicator.color = ft.Colors.RED; page.update()
                except Exception: status_text.value = "Connection Error"; status_indicator.color = ft.Colors.RED; page.update()
                if running["flag"]: await asyncio.sleep(POLL_INTERVAL_SECONDS)

    def start_polling(_):
        if running["flag"]: return
        running["flag"] = True; nonlocal poller_task; poller_task = page.run_task(thingspeak_poller_loop)
        start_btn.disabled = True; stop_btn.disabled = False; page.update()

    def stop_polling(_):
        running["flag"] = False;
        if poller_task: poller_task.cancel()
        status_text.value = "Stopped"; status_indicator.color = ft.Colors.GREY_300; start_btn.disabled = False; stop_btn.disabled = True; page.update()

    start_btn.on_click = start_polling; stop_btn.on_click = stop_polling

ft.app(target=main)