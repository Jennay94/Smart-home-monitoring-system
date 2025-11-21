import flet as ft

def main(page: ft.Page):
    page.title = "Smart Home Controller"
    page.padding = 25
    page.bgcolor = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    page.scroll = ft.ScrollMode.ADAPTIVE
    
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

    # Header
    header = ft.Container(
        content=ft.Column([
            ft.Text("🏠 Smart Home Dashboard", 
                   size=28, 
                   weight=ft.FontWeight.BOLD,
                   color=ft.Colors.WHITE),
            ft.Text("Real-time monitoring & control system", 
                   size=14, 
                   color=ft.Colors.WHITE70),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=30),
    )

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

    # Add all components to the page
    page.add(
        ft.Column([
            header,
            ft.Container(height=10),
            first_row,
            ft.Container(height=20),
            second_row,
        ], 
        scroll=ft.ScrollMode.ADAPTIVE,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

ft.app(target=main)