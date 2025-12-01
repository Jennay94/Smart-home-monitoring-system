import flet as ft
from datetime import datetime
import random
import time
import threading

def main(page: ft.Page):
    page.title = "Sensor Monitor Dashboard - Real Time"
    page.padding = 25
    page.bgcolor = ft.Colors.BLUE_900
    page.scroll = ft.ScrollMode.ADAPTIVE  # Enable page scrolling
    
    # Real-time data storage
    sensor_data = [
        {"time": datetime.now().strftime("%H:%M:%S"), "sensor": "temp", "value": "22.70", "unit": "°C"},
        {"time": datetime.now().strftime("%H:%M:%S"), "sensor": "hum", "value": "42.10", "unit": "%RH"},
        {"time": datetime.now().strftime("%H:%M:%S"), "sensor": "light", "value": "650", "unit": "lux"},
    ]
    
    # Current sensor values for cards
    current_values = {
        "temp": "22.70",
        "hum": "42.10", 
        "light": "650"
    }
    
    # Color themes for different sensors
    sensor_colors = {
        "temp": {"color": "#FF6B6B", "icon": "🌡️", "bg": "#FFF5F5", "name": "Temperature"},
        "hum": {"color": "#4ECDC4", "icon": "💧", "bg": "#F0FDFA", "name": "Humidity"},
        "light": {"color": "#FFD93D", "icon": "💡", "bg": "#FFFDE7", "name": "Light"},
    }
    
    # Update flags
    is_running = True
    update_thread = None
    
    # Create larger metric card
    def create_metric_card(sensor_type):
        color_info = sensor_colors[sensor_type]
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Text(color_info["icon"], size=32),  # Larger icon
                                width=60,  # Larger container
                                height=60,
                                bgcolor=ft.Colors.WHITE,
                                border_radius=15,
                                alignment=ft.alignment.center,
                            ),
                            ft.Column([
                                ft.Text(color_info["name"], size=18, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),  # Larger text
                                ft.Text(f"Updated: --:--:--", size=12, color=ft.Colors.WHITE54),
                            ], spacing=3),
                        ],
                        spacing=15,
                    ),
                    ft.Container(height=15),
                    ft.Text("--", size=42, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),  # Larger value
                    ft.Text("", size=16, color=ft.Colors.WHITE54),  # Larger unit
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=10,
            ),
            bgcolor=color_info["color"],
            padding=25,  # More padding
            border_radius=25,
            width=220,  # Wider card
            height=220,  # Taller card
        )
    
    # Create cards
    temp_card = create_metric_card("temp")
    humidity_card = create_metric_card("hum") 
    light_card = create_metric_card("light")
    
    # Store card references for updates
    cards = {
        "temp": temp_card,
        "hum": humidity_card,
        "light": light_card
    }
    
    # Data table
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.BOLD, size=14, color=ft.Colors.BLACK)),
        ],
        rows=[],
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=10,
    )
    
    # Update card with new data
    def update_card(sensor_type, value, unit):
        card = cards[sensor_type]
        color_info = sensor_colors[sensor_type]
        
        # Update the value text (third child in column)
        card.content.controls[2].value = value
        # Update the unit text (fourth child in column)
        card.content.controls[3].value = unit
        # Update timestamp (second child of second child in first row)
        card.content.controls[0].controls[1].controls[1].value = f"Updated: {datetime.now().strftime('%H:%M:%S')}"
        
    # Update data table
    def update_data_table():
        # Clear existing rows
        data_table.rows.clear()
        
        # Add latest 8 entries (show most recent first)
        recent_data = sensor_data[-8:][::-1]
        
        for data in recent_data:
            color_info = sensor_colors[data["sensor"]]
            data_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(data["time"], size=13, weight=ft.FontWeight.BOLD)),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Row([
                                    ft.Text(color_info["icon"], size=16),  # Larger icon
                                    ft.Text(data["sensor"].upper(), size=13, weight=ft.FontWeight.BOLD),
                                ], spacing=8),  # More spacing
                                padding=8,
                            )
                        ),
                        ft.DataCell(ft.Text(data["value"], size=15, weight=ft.FontWeight.BOLD)),  # Larger text
                        ft.DataCell(ft.Text(data["unit"], size=13, color=ft.Colors.GREY_600)),
                    ]
                )
            )
    
    # Simulate sensor data updates
    def simulate_sensor_data():
        while is_running:
            if status_text.value == "Simulator: RUNNING":
                # Generate random but realistic sensor data
                new_temp = round(20 + random.uniform(1, 5), 2)
                new_hum = round(40 + random.uniform(1, 10), 2)
                new_light = random.randint(500, 800)
                
                current_time = datetime.now().strftime("%H:%M:%S")
                
                # Update current values
                current_values["temp"] = f"{new_temp:.2f}"
                current_values["hum"] = f"{new_hum:.2f}"
                current_values["light"] = f"{new_light}"
                
                # Add to sensor data history
                sensor_data.extend([
                    {"time": current_time, "sensor": "temp", "value": f"{new_temp:.2f}", "unit": "°C"},
                    {"time": current_time, "sensor": "hum", "value": f"{new_hum:.2f}", "unit": "%RH"},
                    {"time": current_time, "sensor": "light", "value": f"{new_light}", "unit": "lux"},
                ])
                
                # Update UI in main thread
                page.run_thread(
                    lambda: update_ui_with_new_data()
                )
            
            time.sleep(3)  # Update every 3 seconds
    
    def update_ui_with_new_data():
        # Update cards
        update_card("temp", current_values["temp"], "°C")
        update_card("hum", current_values["hum"], "%RH")
        update_card("light", current_values["light"], "lux")
        
        # Update data table
        update_data_table()
        
        # Refresh the page
        page.update()
    
    # Button handlers
    def on_start_click(e):
        start_btn.disabled = True
        stop_btn.disabled = False
        status_indicator.bgcolor = ft.Colors.GREEN
        status_text.value = "Simulator: RUNNING"
        page.update()
    
    def on_stop_click(e):
        start_btn.disabled = False
        stop_btn.disabled = True
        status_indicator.bgcolor = ft.Colors.RED
        status_text.value = "Simulator: STOPPED"
        page.update()
    
    def on_home_click(e):
        nonlocal is_running
        is_running = False
        page.clean()
        page.add(ft.Text("Home Screen", size=24))
    
    # Initialize with current data
    def initialize_data():
        update_card("temp", current_values["temp"], "°C")
        update_card("hum", current_values["hum"], "%RH") 
        update_card("light", current_values["light"], "lux")
        update_data_table()
    
    # Control Panel
    status_indicator = ft.Container(
        width=15,  # Larger indicator
        height=15,
        border_radius=8,
        bgcolor=ft.Colors.GREEN,
    )
    
    status_text = ft.Text(
        "Simulator: RUNNING",
        size=16,  # Larger text
        color=ft.Colors.WHITE,
        weight=ft.FontWeight.BOLD,
    )
    
    start_btn = ft.ElevatedButton(
        "▶ Start Publishing",
        icon=ft.Icons.PLAY_ARROW,
        on_click=on_start_click,
        disabled=True,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN,
            padding=25,  # More padding
            shape=ft.RoundedRectangleBorder(radius=15),
        ),
        height=55,  # Taller button
    )
    
    stop_btn = ft.ElevatedButton(
        "⏹ Stop Simulator",
        icon=ft.Icons.STOP,
        on_click=on_stop_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED,
            padding=25,
            shape=ft.RoundedRectangleBorder(radius=15),
        ),
        height=55,
    )
    
    controls_card = ft.Container(
        content=ft.Column(
            [
                ft.Text("Simulation Controls", 
                       size=20,  # Larger text
                       weight=ft.FontWeight.BOLD,
                       color=ft.Colors.WHITE),
                ft.Container(height=20),  # More spacing
                ft.Row(
                    [start_btn, stop_btn],
                    spacing=20,  # More spacing between buttons
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(height=20),
                ft.Row(
                    [status_indicator, status_text],
                    spacing=12,  # More spacing
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=ft.Colors.BLUE_700,
        padding=30,  # More padding
        border_radius=25,
        margin=ft.margin.symmetric(vertical=25),
    )
    
    # Header Section
    header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    icon_size=28,  # Larger icon
                    on_click=lambda e: print("Back clicked"),
                ),
                ft.Column([
                    ft.Text("Real-Time Sensor Monitor", 
                           size=26,  # Larger title
                           weight=ft.FontWeight.BOLD,
                           color=ft.Colors.WHITE),
                    ft.Text("Live IoT Sensor Data Stream", 
                           size=16,  # Larger subtitle
                           color=ft.Colors.WHITE54),
                ], spacing=5),
                ft.Container(expand=True),
            ],
            alignment=ft.MainAxisAlignment.START,
        ),
        margin=ft.margin.only(bottom=35),
    )
    
    metrics_row = ft.Row(
        [temp_card, humidity_card, light_card],
        spacing=25,  # More spacing between cards
        alignment=ft.MainAxisAlignment.CENTER,
        wrap=True,
    )
    
    data_table_container = ft.Container(
        content=ft.Column(
            [
                ft.Row([
                    ft.Icon(ft.Icons.TABLE_CHART, color=ft.Colors.WHITE, size=28),  # Larger icon
                    ft.Text("Live Sensor Data Stream", 
                           size=20,  # Larger text
                           weight=ft.FontWeight.BOLD,
                           color=ft.Colors.WHITE),
                ], spacing=12),
                ft.Container(height=15),
                ft.Container(
                    content=data_table,
                    bgcolor=ft.Colors.WHITE,
                    padding=20,  # More padding
                    border_radius=20,
                ),
            ]
        ),
        margin=ft.margin.only(bottom=25),
    )
    
    # Home Button
    home_btn = ft.ElevatedButton(
        "🏠 HOME",
        on_click=on_home_click,
        bgcolor=ft.Colors.ORANGE,
        color=ft.Colors.WHITE,
        width=220,  # Wider button
        height=55,  # Taller button
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=15),
        ),
    )
    
    # Initialize data
    initialize_data()
    
    # Start simulation thread
    update_thread = threading.Thread(target=simulate_sensor_data, daemon=True)
    update_thread.start()
    
    # Main layout with scrollable column
    main_column = ft.Column(
        [
            header,
            metrics_row,
            controls_card,
            data_table_container,
            ft.Container(
                content=home_btn,
                alignment=ft.alignment.center,
                margin=ft.margin.only(bottom=20),
            ),
        ],
        scroll=ft.ScrollMode.ADAPTIVE,  # Enable scrolling for the column
        expand=True,  # Allow column to expand
        spacing=0,
    )
    
    # Add to page with scroll container
    page.add(
        ft.Container(
            content=main_column,
            expand=True,  # Expand to fill available space
        )
    )

ft.app(target=main)