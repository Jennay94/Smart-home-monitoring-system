import flet as ft
from datetime import datetime
import threading
import random
import time
from config import *
import state
from components import create_styled_log_table, create_log_row

def sensor_view(page: ft.Page):
    """
    Displays the Simulated Sensors view.
    It generates random data for Temperature, Humidity, and Light
    and updates the UI in real-time using a background thread.
    """
    
    # --- LOCAL DATA STORAGE ---
    # History list to populate the data table (logs)
    sensor_data_history = [] 
    # Current snapshot of values to update the cards immediately
    current_values = {"temp": "22.70", "hum": "42.10", "light": "650"}
    
    # Configuration for each sensor type (Color, Icon, Unit)
    sensor_conf = {
        "temp": {"color": COLOR_TEMP, "icon": ft.Icons.THERMOSTAT, "name": "Temperature", "unit": "°C"},
        "hum": {"color": COLOR_HUM, "icon": ft.Icons.WATER_DROP, "name": "Humidity", "unit": "%RH"},
        "light": {"color": COLOR_LIGHT, "icon": ft.Icons.LIGHTBULB, "name": "Light", "unit": "lux"},
    }
    
    # --- UI HELPER FUNCTIONS ---

    def create_metric_card(sensor_key):
        """
        Creates a UI Card for a specific sensor.
        Returns the card control and references to the text fields 
        (timestamp, value, unit) so they can be updated later without re-rendering.
        """
        conf = sensor_conf[sensor_key]
        accent = conf["color"]
        
        # Text controls that will change dynamically
        ts_text = ft.Text("Updated: --:--:--", size=11, color=TEXT_SECONDARY)
        value_text = ft.Text("--", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        unit_text = ft.Text("", size=16, color=TEXT_SECONDARY)

        # Card layout structure
        card = ft.Card(
            elevation=CARD_ELEVATION, color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20, width=250,
                content=ft.Column([
                    ft.Row([
                        # Icon with dynamic background color
                        ft.Container(content=ft.Icon(conf["icon"], color=accent, size=28), padding=10, bgcolor=ft.Colors.with_opacity(0.1, accent), border_radius=12),
                        ft.Column([ft.Text(conf["name"], size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY), ts_text], spacing=2),
                    ], spacing=15),
                    ft.Container(height=20),
                    # Value and Unit alignment
                    ft.Row([value_text, unit_text], vertical_alignment=ft.CrossAxisAlignment.END)
                ])
            )
        )
        return card, ts_text, value_text, unit_text
    
    # Create the three main cards and capture their text references
    temp_card, temp_ts, temp_val, temp_unit = create_metric_card("temp")
    humidity_card, hum_ts, hum_val, hum_unit = create_metric_card("hum")
    light_card, light_ts, light_val, light_unit = create_metric_card("light")

    # Store references in a dictionary for easy access by key ('temp', 'hum', etc.)
    card_refs = {
        "temp": {"ts": temp_ts, "val": temp_val, "unit": temp_unit},
        "hum": {"ts": hum_ts, "val": hum_val, "unit": hum_unit},
        "light": {"ts": light_ts, "val": light_val, "unit": light_unit},
    }

    # Create the empty data table using the component helper
    data_table = create_styled_log_table()

    # --- UPDATE LOGIC ---

    def update_card(sensor_key, value):
        """Updates the text values inside a specific card."""
        conf = sensor_conf[sensor_key]
        refs = card_refs[sensor_key]
        refs["ts"].value = f"Updated: {datetime.now().strftime('%H:%M:%S')}"
        refs["val"].value = value
        refs["unit"].value = conf["unit"]

    def update_data_table():
        """Refreshes the log table with the last 10 entries."""
        data_table.rows.clear()
        # Loop through the last 10 items in reverse order (newest first)
        for data in sensor_data_history[-10:][::-1]:
            conf = sensor_conf[data["sensor_key"]]
            row = create_log_row(
                data["time"], conf["name"].upper(), data["value"], conf["unit"], conf["icon"], conf["color"]
            )
            data_table.rows.append(row)

    def update_ui_with_new_data():
        """Orchestrates the UI update for cards and the table."""
        update_card("temp", current_values["temp"])
        update_card("hum", current_values["hum"])
        update_card("light", current_values["light"])
        update_data_table()
        if page: page.update()

    # --- SIMULATION LOGIC (THREAD) ---

    def simulate_sensor_data():
        """
        Background loop that generates random sensor data.
        Runs only while state.simulation_running is True.
        """
        while state.simulation_running:
            # Only generate data if the user hasn't clicked "Stop"
            if status_text.value == "RUNNING":
                curr_time = datetime.now().strftime("%H:%M:%S")
                
                # Generate random values with slight variations
                new_temp = f"{round(20 + random.uniform(1, 5), 2):.2f}"
                new_hum = f"{round(40 + random.uniform(1, 10), 2):.2f}"
                new_light = f"{random.randint(500, 800)}"
                
                # Update local state dictionary
                current_values["temp"] = new_temp
                current_values["hum"] = new_hum
                current_values["light"] = new_light

                # Append to history for the log table
                sensor_data_history.append({"time": curr_time, "sensor_key": "temp", "value": new_temp})
                sensor_data_history.append({"time": curr_time, "sensor_key": "hum", "value": new_hum})
                sensor_data_history.append({"time": curr_time, "sensor_key": "light", "value": new_light})
                
                # Prevent history from growing infinitely (optional cleanup logic could go here)
                if len(sensor_data_history) > 60: pass 

                # Schedule UI update on the main thread (Flet requirement)
                if page:
                    try: page.run_thread(update_ui_with_new_data)
                    except Exception: break
            
            # Wait 3 seconds before next update
            time.sleep(3)

    # --- EVENT HANDLERS ---

    def on_start_click(e):
        """Enables the simulation loop logic visually."""
        start_btn.disabled = True
        stop_btn.disabled = False
        status_indicator.bgcolor = COLOR_SUCCESS
        status_text.value = "RUNNING"
        status_text.color = COLOR_SUCCESS
        page.update()

    def on_stop_click(e):
        """Pauses the data generation visually."""
        start_btn.disabled = False
        stop_btn.disabled = True
        status_indicator.bgcolor = COLOR_DANGER
        status_text.value = "STOPPED"
        status_text.color = COLOR_DANGER
        page.update()

    def on_home_click(e):
        """Stops the thread and navigates back to Home."""
        state.simulation_running = False
        page.go("/")

    # --- LAYOUT COMPONENTS ---

    status_indicator = ft.Container(width=12, height=12, border_radius=6, bgcolor=COLOR_SUCCESS)
    status_text = ft.Text("RUNNING", size=14, weight=ft.FontWeight.BOLD, color=COLOR_SUCCESS)
    
    ctrl_btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), padding=15)
    
    # Control Buttons
    start_btn = ft.ElevatedButton("Start", icon=ft.Icons.PLAY_ARROW, on_click=on_start_click, disabled=True, bgcolor=COLOR_SUCCESS, color=ft.Colors.WHITE, style=ctrl_btn_style)
    stop_btn = ft.ElevatedButton("Stop", icon=ft.Icons.STOP, on_click=on_stop_click, bgcolor=COLOR_DANGER, color=ft.Colors.WHITE, style=ctrl_btn_style)
    
    # Simulation Controls Card
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

    # Page Header
    header = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT_PRIMARY, on_click=on_home_click),
        ft.Column([ft.Text("Simulated Sensors", size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY), ft.Text("Real-time data simulation", size=14, color=TEXT_SECONDARY)], spacing=2),
    ], alignment=ft.MainAxisAlignment.START)

    # Metric Cards Layout
    metrics_row = ft.Row([temp_card, humidity_card, light_card], spacing=20, alignment=ft.MainAxisAlignment.START, wrap=True)
    
    # Data Table Container
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

    # --- INITIALIZATION ---

    # Render initial data before starting the thread
    update_ui_with_new_data()
    
    # Start the simulation thread if it's not already running
    if not state.simulation_running:
        state.simulation_running = True
        state.simulation_thread = threading.Thread(target=simulate_sensor_data, daemon=True)
        state.simulation_thread.start()

    # Assemble the main view column
    main_column = ft.Column([
        header, ft.Container(height=20),
        metrics_row, ft.Container(height=20),
        controls_card, ft.Container(height=20),
        data_table_container, ft.Container(height=20),
    ], scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=0)

    # Return the complete view
    return ft.View(route="/sensors", controls=[main_column], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)