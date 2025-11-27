import flet as ft
from config import *

def generate_y_labels(min_val, max_val):
    """Generates dynamic Y-axis labels based on data range."""
    rng = max_val - min_val
    if rng <= 20: step = 5
    elif rng <= 50: step = 10
    elif rng <= 200: step = 25
    elif rng <= 1000: step = 200
    else: step = 500
    
    labels = []
    start = (int(min_val) // step) * step
    end = (int(max_val) // step + 1) * step
    
    curr = start
    while curr <= end:
        labels.append(ft.ChartAxisLabel(value=curr, label=ft.Text(str(int(curr)), style=LABEL_STYLE)))
        curr += step
    return labels

def create_styled_log_table():
    """Creates the base DataTable structure."""
    return ft.DataTable(
        heading_row_color=BG_COLOR,
        heading_row_height=50,
        data_row_min_height=60,
        border=ft.border.all(1, "#E0E0E0"),
        border_radius=12,
        vertical_lines=ft.border.BorderSide(0, "transparent"),
        horizontal_lines=ft.border.BorderSide(1, "#EEEEEE"),
        columns=[
            ft.DataColumn(ft.Text("Time", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Sensor", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Value", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY)),
            ft.DataColumn(ft.Text("Unit", weight=ft.FontWeight.W_600, color=TEXT_SECONDARY))
        ],
        rows=[],
    )

def create_log_row(time_str, sensor_name, value_str, unit_str, icon_data, color):
    """Creates a styled DataRow with an icon for the logs."""
    return ft.DataRow(cells=[
        ft.DataCell(ft.Text(time_str, size=13, color=TEXT_PRIMARY)),
        ft.DataCell(ft.Row([
            ft.Icon(icon_data, color=color, size=18),
            ft.Text(sensor_name, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)
        ], spacing=12)),
        ft.DataCell(ft.Text(value_str, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)),
        ft.DataCell(ft.Text(unit_str, size=13, color=TEXT_SECONDARY)),
    ])