# Flet Pub/Sub Sensor Dashboard - ThingSpeak Integration (VÉGSŐ JAVÍTÁS V4)
# -----------------------------------------
# Features:
# - Async data fetching from ThingSpeak API (Fields 1, 2, 3)
# - Real-time UI updates using pubsub
# - Sensor cards, event log table, and a temperature history chart
# - Two-column dashboard layout: left (UI), right (chart)
# -----------------------------------------
import flet as ft
import asyncio
import aiohttp  # SZÜKSÉGES: pip install aiohttp
from datetime import datetime

# --- THINGSPEAK CONFIGURATION ---
THINGSPEAK_CHANNEL_ID = "3156213"
THINGSPEAK_READ_KEY = "WXM1B5P9O2XBKKMS"
# URL a legutolsó bejegyzés lekéréséhez JSON formátumban
THINGSPEAK_URL = f"https://api.thingspeak.com/channels/{THINGSPEAK_CHANNEL_ID}/feeds/last.json?api_key={THINGSPEAK_READ_KEY}"
# Lekérdezési gyakoriság (másodpercben). Ingyenes ThingSpeak fióknál kb. 15mp a limit.
POLL_INTERVAL_SECONDS = 15

def main(page: ft.Page):
    page.title = "Sensor Monitor (ThingSpeak API)"
    page.padding = 24
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.theme_mode = ft.ThemeMode.LIGHT

    # ---------------------------------------------------------------------
    # 1. Sensor card widgets (latest values)
    # ---------------------------------------------------------------------
    temp_value = ft.Text("—", size=28, weight=ft.FontWeight.BOLD)
    temp_ts = ft.Text("Waiting for data...", size=12)
    hum_value = ft.Text("—", size=28, weight=ft.FontWeight.BOLD)
    hum_ts = ft.Text("", size=12)
    air_value = ft.Text("—", size=28, weight=ft.FontWeight.BOLD)
    air_ts = ft.Text("", size=12)

    # --- JAVÍTÁS V2: Eltávolítottuk a : ft.IconData típusmegjelölést ---
    def sensor_card(title: str, big_text: ft.Text, ts_text: ft.Text, unit_hint: str, icon_data):
        """Reusable card for showing latest sensor reading."""
        return ft.Card(
            elevation=4,
            content=ft.Container(
                padding=16,
                content=ft.Column(
                    [
                        ft.Row([ft.Icon(icon_data), ft.Text(title, size=16, weight=ft.FontWeight.W_600)]),
                        big_text,
                        ft.Text(unit_hint, size=12, color=ft.Colors.GREY),
                        ts_text,
                    ],
                    spacing=6,
                ),
            )
        )

    # ---------------------------------------------------------------------
    # 2. Event log table (latest first)
    # ---------------------------------------------------------------------
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Time")),
            ft.DataColumn(ft.Text("Sensor Field")),
            ft.DataColumn(ft.Text("Value")),
            ft.DataColumn(ft.Text("Unit")),
        ],
        rows=[],
        heading_row_color=ft.Colors.BLUE_50,
        data_row_min_height=28,
    )
    table_container = ft.Container(
        content=ft.Column([table], scroll=ft.ScrollMode.AUTO),
        height=300,
        padding=ft.padding.all(8),
        bgcolor=ft.Colors.with_opacity(0.04, ft.Colors.BLUE),
        border_radius=8,
        border=ft.border.all(1, ft.Colors.GREY_200)
    )

    # ---------------------------------------------------------------------
    # 3. Temperature line chart (last 10 samples)
    # ---------------------------------------------------------------------
    temp_points: list[ft.LineChartDataPoint] = []
    temp_series = ft.LineChartData(
        data_points=temp_points,
        stroke_width=3,
        color=ft.Colors.BLUE,
        curved=True,
        stroke_cap_round=True,
        below_line_bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE),
    )
    
    chart_grid_lines = ft.ChartGridLines(interval=1, color=ft.Colors.GREY_200, width=1)
    
    temp_chart = ft.LineChart(
        data_series=[temp_series],
        min_x=0,
        max_x=9,  # always 10 samples window: x = 0..9
        interactive=True,
        expand=True,
        # --- JAVÍTÁS V3/V4: Kivettünk minden extra paramétert (grid_lines, interval) ---
        left_axis=ft.ChartAxis(
            title=ft.Text("Temperature (Field 1)"),
        ),
        bottom_axis=ft.ChartAxis(
            title=ft.Text("Last 10 readings index"),
        ),
        # --- JAVÍTÁS V3: grid_lines hozzáadva globálisan a grafikonhoz ---
        horizontal_grid_lines=chart_grid_lines,
        vertical_grid_lines=chart_grid_lines,
        bgcolor=ft.Colors.WHITE,
        border=ft.border.all(1, ft.Colors.GREY_200)
    )
    chart_container = ft.Container(
        content=temp_chart,
        height=350,
        padding=ft.padding.all(16),
        bgcolor=ft.Colors.WHITE,
        border_radius=12,
        expand=True,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.GREY_300)
    )

    # ---------------------------------------------------------------------
    # 4. Start/Stop buttons & Status
    # ---------------------------------------------------------------------
    start_btn = ft.ElevatedButton("Start polling API", icon=ft.Icons.CLOUD_DOWNLOAD)
    stop_btn = ft.OutlinedButton("Stop", icon=ft.Icons.STOP, disabled=True)
    status_indicator = ft.Icon(ft.Icons.CIRCLE, color=ft.Colors.GREY, size=14)
    status_text = ft.Text("API Poller: idle")

    # ---------------------------------------------------------------------
    # 5. LEFT COLUMN (Cards + Buttons + Table)
    # ---------------------------------------------------------------------
    col1 = ft.Column(
        [
            ft.Text("ThingSpeak Sensor Data", size=20, weight=ft.FontWeight.BOLD),
            ft.Row(
                [
                    sensor_card("Temp (F1)", temp_value, temp_ts, "Unit: °C (assumed)", ft.Icons.THERMOSTAT),
                    sensor_card("Humidity (F2)", hum_value, hum_ts, "Unit: %RH (assumed)", ft.Icons.WATER_DROP),
                    sensor_card("Air Qual (F3)", air_value, air_ts, "Unit: AQI (assumed)", ft.Icons.AIR),
                ],
                spacing=12,
                wrap=True,
            ),
            ft.Divider(),
            ft.Row([start_btn, stop_btn, status_indicator, status_text], spacing=12, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ft.Text("Incoming data log (latest first)", weight=ft.FontWeight.W_600),
            table_container,
        ],
        spacing=16,
        expand=2,
    )

    # ---------------------------------------------------------------------
    # 6. RIGHT COLUMN (Chart)
    # ---------------------------------------------------------------------
    col2 = ft.Column(
        [
            ft.Row(
                [ft.Text("Temperature History (Field 1)", size=18, weight=ft.FontWeight.W_600)],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            chart_container,
        ],
        spacing=8,
        expand=3,
    )

    # ---------------------------------------------------------------------
    # 7. MAIN LAYOUT
    # ---------------------------------------------------------------------
    page.add(
        ft.Row(
            [col1, ft.VerticalDivider(width=1), col2],
            expand=True,
            spacing=20,
            alignment=ft.MainAxisAlignment.START,
        )
    )

    # ---------------------------------------------------------------------
    # 8. Subscriber: receives sensor messages pushed by the poller
    # ---------------------------------------------------------------------
    def on_message(msg):
        """Handles messages sent via page.pubsub.send_all()"""
        if not isinstance(msg, dict) or msg.get("type") != "sensor":
            return
        
        name = msg["name"] # e.g., "Field1"
        value = msg["value"]
        unit = msg["unit"]
        ts_raw = msg["ts"] # ThingSpeak timestamp string

        # Format timestamp nicely (HH:MM:SS)
        try:
            # Parse ThingSpeak format like "2023-10-27T10:45:00Z"
            dt_obj = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            ts_formatted = dt_obj.strftime("%H:%M:%S")
        except ValueError:
            ts_formatted = ts_raw
        except TypeError:
            ts_formatted = "N/A"

        # --- Update sensor cards based on Field mapping ---
        # Feltételezés: Field 1 -> Temp, Field 2 -> Hum, Field 3 -> Air
        if name == "Field1":
            temp_value.value = f"{value} {unit}"
            temp_ts.value = f"Last update: {ts_formatted}"
            
            # --- Update temperature chart (Field 1 only) ---
            try:
                float_val = float(value)
                temp_points.append(ft.LineChartDataPoint(len(temp_points), float_val))
                # Keep only last 10 points and shift X axis
                if len(temp_points) > 10:
                    temp_points.pop(0)
                    for i, p in enumerate(temp_points):
                        p.x = i  # normalize x into 0–9 range
                temp_series.data_points = temp_points
            except (ValueError, TypeError):
                print(f"Could not convert Field1 value '{value}' to float for chart.")

        elif name == "Field2":
            hum_value.value = f"{value} {unit}"
            hum_ts.value = f"Last update: {ts_formatted}"
        elif name == "Field3":
            air_value.value = f"{value} {unit}"
            air_ts.value = f"Last update: {ts_formatted}"

        # --- Add log table row (newest first) ---
        table.rows.insert(
            0,
            ft.DataRow(
                [
                    ft.DataCell(ft.Text(ts_formatted)),
                    ft.DataCell(ft.Text(name)),
                    ft.DataCell(ft.Text(str(value))),
                    ft.DataCell(ft.Text(unit)),
                ]
            ),
        )
        # Limit table size
        if len(table.rows) > 200:
            table.rows.pop()
            
        page.update()

    page.pubsub.subscribe(on_message)

    # ---------------------------------------------------------------------
    # 9. ThingSpeak API Poller (Async Task)
    # ---------------------------------------------------------------------
    # A szimulátort lecseréljük egy aszinkron HTTP lekérdezőre
    running = {"flag": False}
    poller_task = None

    async def thingspeak_poller_loop():
        """Periodically fetches the last entry from ThingSpeak API."""
        status_text.value = f"Polling every {POLL_INTERVAL_SECONDS}s..."
        status_indicator.color = ft.Colors.AMBER
        page.update()

        # Itt használjuk az aiohttp-t, amit telepíteni kell
        async with aiohttp.ClientSession() as session:
            while running["flag"]:
                try:
                    async with session.get(THINGSPEAK_URL, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            status_text.value = "API Connection: OK (waiting next poll)"
                            status_indicator.color = ft.Colors.GREEN
                            page.update()

                            # Adatok feldolgozása
                            timestamp = data.get("created_at")
                            
                            # Field 1 feldolgozása (Feltételezett Hőmérséklet)
                            f1_val = data.get("field1")
                            if f1_val:
                                page.pubsub.send_all({"type": "sensor", "name": "Field1", "value": f1_val, "unit": "°C", "ts": timestamp})
                            
                            # Field 2 feldolgozása (Feltételezett Páratartalom)
                            f2_val = data.get("field2")
                            if f2_val:
                                page.pubsub.send_all({"type": "sensor", "name": "Field2", "value": f2_val, "unit": "%RH", "ts": timestamp})

                            # Field 3 feldolgozása (Feltételezett Levegőminőség)
                            f3_val = data.get("field3")
                            if f3_val:
                                page.pubsub.send_all({"type": "sensor", "name": "Field3", "value": f3_val, "unit": "AQI", "ts": timestamp})

                        else:
                             status_text.value = f"API Error: HTTP {response.status}"
                             status_indicator.color = ft.Colors.RED
                             page.update()

                except Exception as e:
                    status_text.value = f"Connection Error: {str(e)}"
                    status_indicator.color = ft.Colors.RED
                    print(f"Polling error: {e}")
                    page.update()
                
                # Várakozás a következő lekérdezésig (ha még futnia kell)
                if running["flag"]:
                    await asyncio.sleep(POLL_INTERVAL_SECONDS)

    def start_polling(_):
        if running["flag"]:
            return
        running["flag"] = True
        nonlocal poller_task
        # Flet run_task indítja az aszinkron függvényt anélkül, hogy blokkolná az UI-t
        poller_task = page.run_task(thingspeak_poller_loop)
        start_btn.disabled = True
        stop_btn.disabled = False
        page.update()

    async def stop_polling_async():
        running["flag"] = False
        if poller_task:
            poller_task.cancel()
        status_text.value = "API Poller: stopped"
        status_indicator.color = ft.Colors.RED
        start_btn.disabled = False
        stop_btn.disabled = True
        page.update()

    def stop_polling(_):
        page.run_task(stop_polling_async)

    start_btn.on_click = start_polling
    stop_btn.on_click = stop_polling

ft.app(target=main)