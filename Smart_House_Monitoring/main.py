import flet as ft
from views.home_view import home_view
from views.sensor_view import sensor_view
from views.realdata_view import realtime_data_view
from views.extras_view import extras_view

def main(page: ft.Page):
    page.title = "Smart Home Pro"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.fonts = {
        "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "RobotoBold": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    }
    page.theme = ft.Theme(font_family="Roboto")

    def route_change(route):
        page.views.clear()
        if page.route == "/":
            page.views.append(home_view(page))
        elif page.route == "/sensors":
            page.views.append(sensor_view(page))
        elif page.route == "/extras":
            page.views.append(extras_view(page))
        elif page.route == "/realdatas":
            page.views.append(realtime_data_view(page))
        page.update()

    page.on_route_change = route_change
    page.go("/")

if __name__ == "__main__":
    ft.app(target=main)