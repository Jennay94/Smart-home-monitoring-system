import flet as ft
from config import *

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

    # --- UI Card Creators ---
    def create_sensor_card(title, value, unit, accent_color, icon_data, details, width=300):
        return ft.Card(
            elevation=CARD_ELEVATION,
            shadow_color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20, width=width,
                content=ft.Column([
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(icon_data, color=accent_color, size=24),
                            padding=10, bgcolor=ft.Colors.with_opacity(0.1, accent_color),
                            border_radius=12,
                        ),
                        ft.Column([
                            ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Text("Real-time sensor", size=12, color=TEXT_SECONDARY)
                        ], spacing=2),
                    ], spacing=15),
                    ft.Container(height=15),
                    ft.Row([
                        ft.Text(value, size=36, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                        ft.Text(unit, size=16, color=TEXT_SECONDARY),
                    ], vertical_alignment=ft.CrossAxisAlignment.END),
                     ft.Container(height=10),
                    ft.Container(
                        content=ft.Text(details, size=11, color=TEXT_SECONDARY),
                        padding=ft.padding.symmetric(horizontal=12, vertical=8),
                        bgcolor=BG_COLOR, border_radius=8, width=float("inf")
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
                padding=20, width=width,
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
        color=ft.Colors.WHITE, bgcolor=COLOR_HUM,
        padding=ft.padding.symmetric(horizontal=24, vertical=18),
        shape=ft.RoundedRectangleBorder(radius=12), elevation=2
    )
    
    go_to_sensors_btn = ft.ElevatedButton("Simulated Sensors 📊", on_click=lambda _: page.go("/sensors"), style=nav_btn_style)
    go_to_real_datas_btn = ft.ElevatedButton("Real Data (IoT) 📈", on_click=lambda _: page.go("/realdatas"), style=nav_btn_style)
    go_to_extras_btn = ft.ElevatedButton("Extras & AI Chat 🤖", on_click=lambda _: page.go("/extras"), style=nav_btn_style)

    header = ft.Container(
        content=ft.Column([
            ft.Text("Smart Home Dashboard", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
            ft.Text("Overview and control panel", size=16, color=TEXT_SECONDARY),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=30, top=10), alignment=ft.alignment.center
    )

    nav_row = ft.Container(
        content=ft.Row([go_to_sensors_btn, go_to_real_datas_btn, go_to_extras_btn], spacing=15, alignment=ft.MainAxisAlignment.CENTER, wrap=True),
        margin=ft.margin.only(bottom=40)
    )

    # --- Instantiate Cards ---
    temp_card = create_sensor_card("Temperature", "22.5", "°C", COLOR_TEMP, ft.Icons.THERMOSTAT, "BME280 Sensor | Range: -40 to 80°C")
    humidity_card = create_sensor_card("Humidity", "45", "% RH", COLOR_HUM, ft.Icons.WATER_DROP, "BME280 Sensor | Range: 0-100%")

    light_status = ft.Text("Status: OFF", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    light_button = ft.ElevatedButton("Turn ON", on_click=on_light_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    light_icon = ft.Icon(ft.Icons.LIGHTBULB, color=COLOR_LIGHT, size=24)
    light_icon_container = ft.Container(content=light_icon, padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_LIGHT), border_radius=12)
    light_card = create_interactive_card("Light", light_status, light_icon_container, "TSL2591 Sensor Controlled", light_button)

    door_status = ft.Text("Door: LOCKED", size=18, weight=ft.FontWeight.W_600, color=COLOR_DANGER)
    door_button = ft.ElevatedButton("Unlock", on_click=on_door_click, style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_HUM, shape=ft.RoundedRectangleBorder(radius=12)), width=float("inf"))
    door_icon_container = ft.Container(content=ft.Icon(ft.Icons.LOCK, color=COLOR_HUM, size=24), padding=10, bgcolor=ft.Colors.with_opacity(0.1, COLOR_HUM), border_radius=12)
    door_card = create_interactive_card("Front Door", door_status, door_icon_container, "Smart Lock System", door_button)
    
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
