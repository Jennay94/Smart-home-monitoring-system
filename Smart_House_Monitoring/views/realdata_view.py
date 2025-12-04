import flet as ft
from datetime import datetime
import asyncio
import aiohttp
from config import *
import state
from components import create_styled_log_table, create_log_row, generate_y_labels

# ==============================================================================
# --- HELPER: ROBUST DYNAMIC SCALING ---
# ==============================================================================
def update_chart_scale(chart, data_points, config):
    """
    Recalculates the Y-axis min/max based on the visible data points.
    Includes a safety margin to prevent the line from hitting the edges.
    """
    if not data_points:
        # Default fallback if no data exists
        chart.min_y = config["min_y"]
        chart.max_y = config["max_y"]
        return

    # 1. Find the absolute min and max in the current dataset
    y_values = [dp.y for dp in data_points]
    current_min = min(y_values)
    current_max = max(y_values)

    # 2. Calculate a margin (10% of the range)
    diff = current_max - current_min
    if diff == 0: 
        # If line is flat (e.g., constant 20°C), creates a virtual margin
        margin = current_max * 0.1 if current_max != 0 else 10
    else:
        margin = diff * 0.1

    # 3. Determine new limits
    new_min = current_min - margin
    new_max = current_max + margin

    # 4. Special handling for sensors that shouldn't go below zero (Light, Rain, Hum)
    # If the configured min is 0, we try to respect that unless data is actually negative.
    if config["min_y"] == 0 and new_min < 0:
        new_min = 0

    # 5. Apply to chart
    chart.min_y = new_min
    chart.max_y = new_max
    
    # 6. Regenerate labels for the Y-axis
    chart.left_axis.labels = generate_y_labels(new_min, new_max)

def realtime_data_view(page: ft.Page):
    logger.info("Real-time ThingSpeak view loading...")
    
    current_chart_field = "Field1"
    polling_state = {"is_running": False}
    
    # --- Sensor Configurations ---
    field_configs = {
        "Field1": {"name": "Temperature", "color": COLOR_TEMP, "icon": ft.Icons.THERMOSTAT, "unit": "°C", "min_y": 0, "max_y": 50},
        "Field2": {"name": "Humidity", "color": COLOR_HUM, "icon": ft.Icons.WATER_DROP, "unit": "%RH", "min_y": 0, "max_y": 100},
        "Field3": {"name": "Soil Moisture", "color": COLOR_SOIL, "icon": ft.Icons.GRASS, "unit": "%", "min_y": 0, "max_y": 100},
        "Field4": {"name": "Rain", "color": COLOR_RAIN, "icon": ft.Icons.WATER, "unit": "mm", "min_y": 0, "max_y": 20},
        "Field5": {"name": "Fan", "color": COLOR_FAN, "icon": ft.Icons.WIND_POWER, "unit": "RPM", "min_y": 0, "max_y": 2000},
        "Field7": {"name": "Light", "color": COLOR_LIGHT, "icon": ft.Icons.LIGHTBULB, "unit": "lux", "min_y": 0, "max_y": 1000},
    }

    # Text references for fast updates
    txt_refs = {fId: {"val": ft.Text("—", size=28, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), 
                      "ts": ft.Text("Waiting...", size=11, color=TEXT_SECONDARY)} 
                for fId in field_configs}

    # --- Interaction Logic ---
    def on_card_clicked(e, field_id):
        nonlocal current_chart_field; current_chart_field = field_id
        config = field_configs[field_id]
        
        # Update Chart visual style
        chart_axis_title.value = f"{config['name']} History"
        main_chart_series.color = config['color']
        main_chart_series.below_line_bgcolor = ft.Colors.with_opacity(0.2, config['color'])
        
        # Load and set data
        current_data = list(state.GLOBAL_THINGSPEAK_HISTORY[field_id])
        main_chart_series.data_points = current_data
        
        # Force scale update immediately
        update_chart_scale(main_chart, current_data, config)
        page.update()

    # --- UI Component Creators ---
    def create_sensor_card_ui(field_id):
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
                            ft.Text(f"{config['name']} ({field_id})", size=14, weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)
                        ], spacing=10),
                        ft.Container(height=10),
                        ft.Row([txt_refs[field_id]["val"], ft.Text(config["unit"], size=14, color=TEXT_SECONDARY)], vertical_alignment=ft.CrossAxisAlignment.END),
                        ft.Container(height=5),
                        txt_refs[field_id]["ts"],
                    ], spacing=0),
            )
        )

    # --- Table Section ---
    table = create_styled_log_table()
    table_container = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(padding=20, content=ft.Column([
            ft.Text("Live Data Log", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), 
            ft.Container(height=10), 
            ft.Column([table], scroll=ft.ScrollMode.AUTO, height=350)
        ]))
    )

    # --- Chart Section ---
    initial_config = field_configs[current_chart_field]
    initial_data = list(state.GLOBAL_THINGSPEAK_HISTORY[current_chart_field])
    
    main_chart_series = ft.LineChartData(
        data_points=initial_data,
        stroke_width=4, color=initial_config['color'], curved=True, stroke_cap_round=True,
        below_line_bgcolor=ft.Colors.with_opacity(0.2, initial_config['color']),
    )
    chart_axis_title = ft.Text(f"{initial_config['name']} History", style=AXIS_TITLE_STYLE)
    
    # X-Axis Labels (Static 0-9 for history)
    x_labels = [ft.ChartAxisLabel(value=i, label=ft.Text(str(i), style=LABEL_STYLE)) for i in range(10)]

    main_chart = ft.LineChart(
        data_series=[main_chart_series],
        min_x=0, max_x=9,
        # Initial Min/Max (will be overwritten instantly)
        min_y=0, max_y=100,
        interactive=True, expand=True,
        left_axis=ft.ChartAxis(title=chart_axis_title, labels_size=40),
        bottom_axis=ft.ChartAxis(title=ft.Text("Index", style=AXIS_TITLE_STYLE), labels=x_labels, labels_interval=1),
        bgcolor=CHART_BG_COLOR, border=ft.border.all(0, ft.Colors.TRANSPARENT), tooltip_bgcolor=CARD_BG,
    )
    # Apply initial scaling
    update_chart_scale(main_chart, initial_data, initial_config)
    
    chart_card = ft.Card(
        elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
        content=ft.Container(content=main_chart, height=500, padding=20)
    )

    # --- Header & Controls ---
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

    # ==========================================================================
    # --- RESPONSIVE LAYOUT (The Solution for Layout Issues) ---
    # ==========================================================================
    
    # 1. Left Column (Cards + Controls)
    overview_cards = [create_sensor_card_ui(fId) for fId in ["Field1", "Field2", "Field7", "Field3"]]
    
    left_column_content = ft.Column([
        ft.Text("Dashboard Overview", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        ft.Column(overview_cards, spacing=15),
        ft.Container(height=20),
        polling_controls,
    ], spacing=0)

    # 2. Right Column (Chart)
    right_column_content = ft.Column([
        ft.Text("Sensor History Analysis", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Container(height=10),
        chart_card,
    ], spacing=0)

    # 3. Responsive Grid
    # On Mobile (xs): Columns stack (12 width)
    # On Desktop (xl): Left is 4 (1/3), Right is 8 (2/3)
    main_grid = ft.ResponsiveRow([
        ft.Column([left_column_content], col={"xs": 12, "md": 5, "xl": 4}),
        ft.Column([right_column_content], col={"xs": 12, "md": 7, "xl": 8}),
    ], spacing=30, run_spacing=30)

    main_layout = ft.Column([
        header, ft.Container(height=20),
        main_grid, ft.Container(height=30),
        table_container,
    ], expand=True)

    # --- Data Logic ---
    def on_message(msg):
        if not isinstance(msg, dict) or msg.get("type") != "sensor": return
        field_id = msg["name"]; value = msg["value"]; ts_raw = msg["ts"]
        
        if field_id not in field_configs: return
        config = field_configs[field_id]

        # Update Card Text
        try:
            dt_obj = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            ts_formatted = dt_obj.strftime("%H:%M:%S")
        except (ValueError, TypeError): ts_formatted = "N/A"

        txt_refs[field_id]["val"].value = str(value)
        txt_refs[field_id]["ts"].value = f"Last update: {ts_formatted}"

        # Update History & Chart
        try:
            float_val = float(value)
            target_history = state.GLOBAL_THINGSPEAK_HISTORY[field_id]
            target_history.append(ft.LineChartDataPoint(len(target_history), float_val))
            
            # Keep history short (10 points)
            if len(target_history) > 10:
                target_history.pop(0)
                # Re-index x values to be 0..9
                for i, p in enumerate(target_history): p.x = i
            
            # If this is the active chart, update it LIVE
            if field_id == current_chart_field:
                main_chart_series.data_points = list(target_history)
                # CRITICAL: Recalculate scale immediately
                update_chart_scale(main_chart, target_history, config)

        except (ValueError, TypeError): pass

        # Update Table
        row = create_log_row(ts_formatted, config["name"], str(value), config["unit"], config["icon"], config["color"])
        table.rows.insert(0, row)
        if len(table.rows) > 50: table.rows.pop()
        
        if page: page.update()

    page.pubsub.subscribe(on_message)

    # --- Polling Loop ---
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

    # ScrollMode.ADAPTIVE allows scrolling if content overflows on small screens
    return ft.View(route="/realdatas", controls=[main_layout], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)