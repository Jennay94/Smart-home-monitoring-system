import flet as ft
from datetime import datetime
import asyncio
import aiohttp
from config import *
import state
from components import create_styled_log_table, create_log_row, generate_y_labels

def realtime_data_view(page: ft.Page):
    logger.info("Real-time ThingSpeak view loading...")
    
    current_chart_field = "Field1"
    polling_state = {"is_running": False}
    
    field_configs = {
        "Field1": {"name": "Temperature", "color": COLOR_TEMP, "icon": ft.Icons.THERMOSTAT, "unit": "°C", "min_y": 10, "max_y": 40},
        "Field2": {"name": "Humidity", "color": COLOR_HUM, "icon": ft.Icons.WATER_DROP, "unit": "%RH", "min_y": 20, "max_y": 90},
        "Field3": {"name": "Soil Moisture", "color": COLOR_SOIL, "icon": ft.Icons.GRASS, "unit": "%", "min_y": 0, "max_y": 100},
        "Field4": {"name": "Rain", "color": COLOR_RAIN, "icon": ft.Icons.WATER, "unit": "mm", "min_y": 0, "max_y": 10},
        "Field5": {"name": "Fan", "color": COLOR_FAN, "icon": ft.Icons.WIND_POWER, "unit": "RPM", "min_y": 0, "max_y": 2000},
        "Field7": {"name": "Light", "color": COLOR_LIGHT, "icon": ft.Icons.LIGHTBULB, "unit": "lux", "min_y": 0, "max_y": 1000},
    }

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
        main_chart_series.data_points = list(state.GLOBAL_THINGSPEAK_HISTORY[field_id])
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

    table = create_styled_log_table()

    table_container = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(padding=20, content=ft.Column([
            ft.Text("Live Data Log", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), 
            ft.Container(height=10), 
            ft.Column([table], scroll=ft.ScrollMode.AUTO, height=300)
        ]))
    )

    initial_config = field_configs[current_chart_field]
    main_chart_series = ft.LineChartData(
        data_points=list(state.GLOBAL_THINGSPEAK_HISTORY[current_chart_field]),
        stroke_width=4, color=initial_config['color'], curved=True, stroke_cap_round=True,
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

    def on_message(msg):
        if not isinstance(msg, dict) or msg.get("type") != "sensor": return
        field_id = msg["name"]; value = msg["value"]; ts_raw = msg["ts"]
        
        if field_id not in field_configs: return
        config = field_configs[field_id]

        try:
            dt_obj = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            ts_formatted = dt_obj.strftime("%H:%M:%S")
        except (ValueError, TypeError): ts_formatted = "N/A"

        txt_refs[field_id]["val"].value = str(value)
        txt_refs[field_id]["ts"].value = f"Last update: {ts_formatted}"

        try:
            float_val = float(value)
            target_history = state.GLOBAL_THINGSPEAK_HISTORY[field_id]
            target_history.append(ft.LineChartDataPoint(len(target_history), float_val))
            if len(target_history) > 10:
                target_history.pop(0)
                for i, p in enumerate(target_history): p.x = i
            if field_id == current_chart_field:
                main_chart_series.data_points = list(target_history)
        except (ValueError, TypeError): pass

        row = create_log_row(
            ts_formatted, config["name"], str(value), config["unit"], config["icon"], config["color"]
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
                            status_text.value = "API Connection: OK"; status_indicator.bgcolor = COLOR_SUCCESS; page.update()
                            ts = data.get("created_at")
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