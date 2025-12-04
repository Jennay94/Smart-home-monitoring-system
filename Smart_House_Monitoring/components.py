import flet as ft
from config import *

def generate_y_labels(min_val, max_val):
    """
    Generates dynamic Y-axis labels based on data range.
    This ensures the chart grid looks clean and readable regardless of the data scale.
    """
    # Calculate the range of the data
    rng = max_val - min_val
    
    # Determine the step size based on the magnitude of the range
    if rng <= 20: step = 5
    elif rng <= 50: step = 10
    elif rng <= 200: step = 25
    elif rng <= 1000: step = 200
    else: step = 500
    
    labels = []
    # Calculate the starting point: round down min_val to the nearest multiple of 'step'
    start = (int(min_val) // step) * step
    # Calculate the ending point: round up max_val to the nearest multiple of 'step'
    end = (int(max_val) // step + 1) * step
    
    # Generate label objects from start to end with the calculated step
    curr = start
    while curr <= end:
        labels.append(ft.ChartAxisLabel(
            value=curr, 
            label=ft.Text(str(int(curr)), style=LABEL_STYLE) # Apply global label style
        ))
        curr += step
    return labels

def create_styled_log_table():
    """
    Creates the base DataTable structure for the logs.
    Defines the styling (borders, colors) and column headers.
    """
    return ft.DataTable(
        heading_row_color=BG_COLOR,         # Background color for the header
        heading_row_height=50,              # Height of the header row
        data_row_min_height=60,             # Minimum height for data rows
        border=ft.border.all(1, "#E0E0E0"), # Light grey border around the table
        border_radius=12,                   # Rounded corners
        vertical_lines=ft.border.BorderSide(0, "transparent"), # Hide vertical grid lines
        horizontal_lines=ft.border.BorderSide(1, "#EEEEEE"),   # Subtle horizontal grid lines
        columns=[
            # Define columns with styled headers
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY))
        ],
        rows=[], # Start with an empty list of rows
    )

def create_log_row(time_str, sensor_name, value_str, unit_str, icon_data, color):
    """
    Creates a single styled DataRow to be added to the log table.
    Includes an icon next to the sensor name for better visual identification.
    """
    return ft.DataRow(cells=[
        # Time Column
        ft.DataCell(ft.Text(time_str, size=13, color=TEXT_PRIMARY)),
        
        # Sensor Column: Contains a Row with an Icon and the Sensor Name
        ft.DataCell(ft.Row([
            ft.Icon(icon_data, color=color, size=18), # Dynamic icon and color based on sensor type
            ft.Text(sensor_name, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
        ], spacing=12)),
        
        # Value Column: Bold text for emphasis
        ft.DataCell(ft.Text(value_str, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
        
        # Unit Column
        ft.DataCell(ft.Text(unit_str, size=13, color=TEXT_SECONDARY)),
    ])