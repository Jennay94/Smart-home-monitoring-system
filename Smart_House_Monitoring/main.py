import flet as ft
# Import different views (pages) from the 'views' folder.
# This keeps the code modular and organized.
from views.home_view import home_view
from views.sensor_view import sensor_view
from views.realdata_view import realtime_data_view
from views.extras_view import extras_view
from views.rooms_view import rooms_view

def main(page: ft.Page):
    """
    The main entry point of the application.
    Configures the window settings and handles navigation logic.
    """
    
    # --- BASIC CONFIGURATION ---
    page.title = "Smart Home Pro"       # Title of the application window
    page.theme_mode = ft.ThemeMode.LIGHT  # Set the theme to Light mode
    
    # Load custom fonts directly from GitHub repositories.
    # This ensures consistent text rendering across different devices.
    page.fonts = {
        "Roboto": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        "RobotoBold": "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Bold.ttf"
    }
    # Apply the default font family to the entire theme
    page.theme = ft.Theme(font_family="Roboto")

    # --- NAVIGATION LOGIC (ROUTING) ---
    def route_change(route):
        """
        Triggered whenever the route (URL) changes.
        Clears the current view and appends the new one based on the route.
        """
        page.views.clear() # Remove previous page elements from memory

        # Check the current route and append the corresponding view
        if page.route == "/":
            page.views.append(home_view(page))       # Dashboard / Home
        elif page.route == "/sensors":
            page.views.append(sensor_view(page))     # Sensor Logs
        elif page.route == "/extras":
            page.views.append(extras_view(page))     # Extras / Settings
        elif page.route == "/realdatas":
            page.views.append(realtime_data_view(page)) # Realtime Data
        elif page.route == "/rooms":
            page.views.append(rooms_view(page))      # Rooms View
        
        page.update() # Refresh the UI with the new content

    # --- EVENT HANDLERS ---
    # Assign the navigation function to the route change event
    page.on_route_change = route_change
    
    # Navigate to the root URL ("/") on startup
    page.go("/")

# --- APP EXECUTION ---
if __name__ == "__main__":
    ft.app(target=main)