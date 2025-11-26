import flet as ft
from datetime import datetime
import random
import time
import threading

# --- 1. OLDAL: FŐOLDAL (Smart Home Controller) ---
def home_view(page: ft.Page):
    # A háttérszínt itt állítjuk be az adott nézethez
    bgcolor = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"

    # --- Eredeti kód eleje (függvények és definíciók) ---
    # Button click handlers
    def on_light_click(e):
        if light_button.text == "Turn ON":
            light_status.value = "Status: ON"
            light_status.color = ft.Colors.GREEN
            light_button.text = "Turn OFF"
            light_button.bgcolor = "#FF6B6B"
            light_card.bgcolor = "#4ECDC4"
            light_icon.content = ft.Text("💡", size=28)
        else:
            light_status.value = "Status: OFF"
            light_status.color = ft.Colors.RED
            light_button.text = "Turn ON"
            light_button.bgcolor = "#4ECDC4"
            light_card.bgcolor = "#FFD93D"
            light_icon.content = ft.Text("💡", size=28)
        page.update()

    def on_door_click(e):
        if door_button.text == "Unlock":
            door_status.value = "Door: UNLOCKED"
            door_status.color = ft.Colors.GREEN
            door_button.text = "Lock"
            door_button.bgcolor = "#FF6B6B"
            door_icon.content = ft.Text("🚪", size=28)
        else:
            door_status.value = "Door: LOCKED"
            door_status.color = ft.Colors.RED
            door_button.text = "Unlock"
            door_button.bgcolor = "#4ECDC4"
            door_icon.content = ft.Text("🔒", size=28)
        page.update()

    def on_fan_click(e):
        if fan_button.text == "Turn ON":
            fan_status.value = "Status: ON"
            fan_status.color = ft.Colors.GREEN
            fan_button.text = "Turn OFF"
            fan_button.bgcolor = "#FF6B6B"
            fan_icon.content = ft.Text("🌀", size=28)
        else:
            fan_status.value = "Status: OFF"
            fan_status.color = ft.Colors.RED
            fan_button.text = "Turn ON"
            fan_button.bgcolor = "#4ECDC4"
            fan_icon.content = ft.Text("💨", size=28)
        page.update()

    def on_rain_click(e):
        if rain_button.text == "Set YES":
            rain_status.value = "Rain: YES"
            rain_status.color = "#4ECDC4"
            rain_button.text = "Set NO"
            rain_button.bgcolor = "#FFD93D"
            rain_icon.content = ft.Text("🌧️", size=28)
        else:
            rain_status.value = "Rain: NO"
            rain_status.color = "#FFD93D"
            rain_button.text = "Set YES"
            rain_button.bgcolor = "#4ECDC4"
            rain_icon.content = ft.Text("☀️", size=28)
        page.update()

    def on_window_click(e):
        if window_button.text == "Open":
            window_status.value = "Window: OPEN"
            window_status.color = ft.Colors.GREEN
            window_button.text = "Close"
            window_button.bgcolor = "#FF6B6B"
            window_icon.content = ft.Text("🪟", size=28)
        else:
            window_status.value = "Window: CLOSED"
            window_status.color = ft.Colors.RED
            window_button.text = "Open"
            window_button.bgcolor = "#4ECDC4"
            window_icon.content = ft.Text("🚫", size=28)
        page.update()

    # Create colorful card function
    def create_sensor_card(title, value, unit, value_color, icon, bg_color, details, width=280, height=200):
        return ft.Container(
            content=ft.Column([
                # Header with icon
                ft.Row([
                    ft.Container(
                        content=ft.Text(icon, size=24),
                        width=45,
                        height=45,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Real-time sensor", size=10, color=ft.Colors.WHITE70),
                    ], spacing=2),
                ], spacing=12),
                
                # Value display
                ft.Container(
                    content=ft.Column([
                        ft.Text(value, size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(unit, size=14, color=ft.Colors.WHITE70),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=10, bottom=10),
                ),
                
                # Details section
                ft.Container(
                    content=ft.Column([
                        ft.Text("Sensor Details", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(details, size=10, color=ft.Colors.WHITE70),
                    ]),
                    bgcolor=ft.Colors.WHITE24,
                    padding=8,
                    border_radius=8,
                ),
            ]),
            bgcolor=bg_color,
            padding=15,
            border_radius=20,
            width=width,
            height=height,
        )

    # Create interactive card function
    def create_interactive_card(title, status, status_color, icon, bg_color, description, button, width=280, height=200):
        return ft.Container(
            content=ft.Column([
                # Header with icon
                ft.Row([
                    ft.Container(
                        content=ft.Text(icon, size=24),
                        width=45,
                        height=45,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        alignment=ft.alignment.center,
                    ),
                    ft.Column([
                        ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Smart device", size=10, color=ft.Colors.WHITE70),
                    ], spacing=2),
                ], spacing=12),
                
                # Status and description
                ft.Column([
                    ft.Text(status, size=18, weight=ft.FontWeight.BOLD, color=status_color),
                    ft.Text(description, size=12, color=ft.Colors.WHITE70),
                ], spacing=5),
                
                # Button
                ft.Container(
                    content=button,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=10),
                ),
                
                # Quick stats
                ft.Container(
                    content=ft.Row([
                        ft.Text("🔄 Auto", size=10, color=ft.Colors.WHITE70),
                        ft.Text("⚡ Low Power", size=10, color=ft.Colors.WHITE70),
                        ft.Text("📱 Connected", size=10, color=ft.Colors.WHITE70),
                    ], spacing=8),
                    alignment=ft.alignment.center,
                ),
            ]),
            bgcolor=bg_color,
            padding=15,
            border_radius=20,
            width=width,
            height=height,
        )

    # --- ÚJ ELEM: Navigációs gomb a 2. oldalra ---
    go_to_sensors_btn = ft.ElevatedButton(
        "Go to Real-Time Sensors 📊",
        on_click=lambda _: page.go("/sensors"), # Ez visz át a másik oldalra
        style=ft.ButtonStyle(
            color=ft.Colors.BLUE_900,
            bgcolor=ft.Colors.WHITE,
            padding=20,
        )
    )

    # Header (Módosítva, hogy tartalmazza a gombot)
    header = ft.Container(
        content=ft.Column([
            ft.Text("🏠 Smart Home Dashboard", 
                    size=28, 
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE),
            ft.Text("Real-time monitoring & control system", 
                    size=14, 
                    color=ft.Colors.WHITE70),
            ft.Container(height=20),
            go_to_sensors_btn # Gomb hozzáadva
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=30),
    )

    # --- Innentől az eredeti kód folytatódik a kártyák létrehozásával ---
    # Line 1: Sensor Cards (Temperature, Humidity, Light)
    temp_card = create_sensor_card(
        "Temperature",
        "22.5", "°C",
        ft.Colors.WHITE,
        "🌡️",
        "#FF6B6B",
        "DHT22 Sensor\nRange: -40°C to 80°C\nAccuracy: ±0.5°C"
    )

    humidity_card = create_sensor_card(
        "Humidity", 
        "45", "% RH",
        ft.Colors.WHITE,
        "💧",
        "#4ECDC4",
        "DHT22 Sensor\nRange: 0-100% RH\nAccuracy: ±2%"
    )

    # Light Card Components
    light_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    light_button = ft.ElevatedButton(
        "Turn ON",
        on_click=on_light_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN,
            padding=15,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        width=120,
    )
    light_icon = ft.Container(
        content=ft.Text("💡", size=24),
        width=45,
        height=45,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        alignment=ft.alignment.center,
    )
    light_card = create_interactive_card(
        "Light",
        "650 Lux",
        ft.Colors.AMBER,
        "💡",
        "#FFD93D",
        "BH1750 Light Sensor",
        light_button
    )

    # Line 2: Control Cards (Fan, Rain, Window, Door)
    # Fan Card
    fan_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    fan_button = ft.ElevatedButton(
        "Turn ON",
        on_click=on_fan_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN,
            padding=15,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        width=120,
    )
    fan_icon = ft.Container(
        content=ft.Text("💨", size=24),
        width=45,
        height=45,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        alignment=ft.alignment.center,
    )
    fan_card = create_interactive_card(
        "Fan",
        "Status: OFF",
        ft.Colors.RED,
        "💨",
        "#FF9FF3",
        "DC Motor Fan Control",
        fan_button
    )

    # Rain Card
    rain_status = ft.Text("Rain: NO", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE)
    rain_button = ft.ElevatedButton(
        "Set YES",
        on_click=on_rain_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE,
            padding=15,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        width=120,
    )
    rain_icon = ft.Container(
        content=ft.Text("☀️", size=24),
        width=45,
        height=45,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        alignment=ft.alignment.center,
    )
    rain_card = create_interactive_card(
        "Rain Detection",
        "Rain: NO",
        ft.Colors.ORANGE,
        "☀️",
        "#54A0FF",
        "Rain Sensor Module",
        rain_button
    )

    # Window Card
    window_status = ft.Text("Window: CLOSED", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    window_button = ft.ElevatedButton(
        "Open",
        on_click=on_window_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN,
            padding=15,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        width=120,
    )
    window_icon = ft.Container(
        content=ft.Text("🚫", size=24),
        width=45,
        height=45,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        alignment=ft.alignment.center,
    )
    window_card = create_interactive_card(
        "Window",
        "Window: CLOSED",
        ft.Colors.RED,
        "🚫",
        "#FF9F43",
        "Smart Window Controller",
        window_button
    )

    # Door Card
    door_status = ft.Text("Door: LOCKED", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.RED)
    door_button = ft.ElevatedButton(
        "Unlock",
        on_click=on_door_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE,
            padding=15,
            shape=ft.RoundedRectangleBorder(radius=12),
        ),
        width=120,
    )
    door_icon = ft.Container(
        content=ft.Text("🔒", size=24),
        width=45,
        height=45,
        bgcolor=ft.Colors.WHITE,
        border_radius=10,
        alignment=ft.alignment.center,
    )
    door_card = create_interactive_card(
        "Front Door",
        "Door: LOCKED",
        ft.Colors.RED,
        "🔒",
        "#48DBFB",
        "Smart Lock System",
        door_button
    )

    # Rows layout
    first_row = ft.Row(
        [temp_card, humidity_card, light_card],
        spacing=20,
        wrap=True,
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
    )

    second_row = ft.Row(
        [fan_card, rain_card, window_card, door_card],
        spacing=20,
        wrap=True,
        alignment=ft.MainAxisAlignment.SPACE_EVENLY,
    )

    # Fő tartalmi oszlop
    content_column = ft.Column([
            header,
            ft.Container(height=10),
            first_row,
            ft.Container(height=20),
            second_row,
        ],
        scroll=ft.ScrollMode.ADAPTIVE,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
    )

    # --- VÁLTOZÁS: A végén nem page.add-ot használunk, hanem visszaadunk egy View-t ---
    return ft.View(
        route="/", # Ez a főoldal útvonala
        controls=[content_column],
        bgcolor=bgcolor,
        padding=25,
        scroll=ft.ScrollMode.ADAPTIVE
    )


# --- 2. OLDAL: SZENZOR MONITOR ---
def sensor_view(page: ft.Page):
    # A háttérszínt itt állítjuk be az adott nézethez
    bgcolor = ft.Colors.BLUE_900

    # --- Eredeti kód eleje ---
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
    # FONTOS: nonlocal változóként fogjuk használni a szimuláció leállításához
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
        # A ciklus addig fut, amíg az is_running igaz. 
        # Ha elnavigálunk, false-ra állítjuk.
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
                # Fontos: ellenőrizzük, hogy a page még létezik-e
                if page:
                    try:
                        page.run_thread(
                            lambda: update_ui_with_new_data()
                        )
                    except Exception:
                        # Ha már nincs page (elnavigáltunk), állítsuk le a ciklust
                        break
            
            # Várakozás a következő frissítésig
            time.sleep(3) 
    
    def update_ui_with_new_data():
        # Update cards
        update_card("temp", current_values["temp"], "°C")
        update_card("hum", current_values["hum"], "%RH")
        update_card("light", current_values["light"], "lux")
        
        # Update data table
        update_data_table()
        
        # Refresh the page if it's still attached
        if page:
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
    
    # --- VÁLTOZÁS: Home gomb kezelője ---
    def on_home_click(e):
        # Nagyon fontos: Leállítjuk a szimulációs ciklust!
        nonlocal is_running
        is_running = False
        
        # Visszanavigálunk a főoldalra ("/")
        page.go("/")
    
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
                    on_click=on_home_click, # A vissza nyíl is hazavisz
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
    # FONTOS: A daemon=True biztosítja, hogy ha bezárjuk az appot, a szál is leálljon
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
    
    # --- VÁLTOZÁS: Itt is ft.View-t adunk vissza ---
    return ft.View(
        route="/sensors",
        controls=[
            ft.Container(
                content=main_column,
                expand=True,
            )
        ],
        bgcolor=bgcolor,
        padding=25,
        scroll=ft.ScrollMode.ADAPTIVE
    )


# --- FŐ ALKALMAZÁS LOGIKA ---
def main(page: ft.Page):
    page.title = "Smart Home Super App"
    
    # Ez a függvény kezeli az útvonalváltást
    def route_change(route):
        page.views.clear() # Töröljük az előző nézetet
        
        # Eldöntjük, melyik nézetet töltsük be az URL alapján
        if page.route == "/":
            page.views.append(home_view(page))
        elif page.route == "/sensors":
            page.views.append(sensor_view(page))
            
        page.update()

    # Ez kezeli a "Vissza" gombot a böngészőben/mobilon
    def view_pop(view):
        page.views.pop()
        top_view = page.views[-1]
        page.go(top_view.route)

    # Beállítjuk az eseménykezelőket
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    
    # Elindítjuk az alkalmazást a főoldalon ("/")
    page.go("/")

ft.app(target=main)