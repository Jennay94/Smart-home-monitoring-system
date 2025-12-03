import flet as ft
from config import *
from typing import List, Dict, Any, Union

a_rooms: List[Dict[str, Any]] = [
    {"id": "r1", "name": "room1", "icon": ft.Icons.HOME, "device_count": 2},
]

a_devices: Dict[str, List[Dict[str, Union[str, int, Any]]]] = {
    "r1": [
        {"id": "d1", "name": "Main Light", "type": "Control", "subtype": "Light Switch", "status": "OFF", "color": COLOR_LIGHT, "icon": ft.Icons.LIGHTBULB},
        {"id": "d2", "name": "Temperature", "type": "Sensor", "subtype": "Thermometer", "value": "22.5", "unit": "°C", "color": COLOR_TEMP, "icon": ft.Icons.THERMOSTAT},
    ],
}

CARD_WIDTH = 320
CARD_HEIGHT = 200


def rooms_view(page: ft.Page):

    initial_room = a_rooms[0]["id"] if a_rooms else None

    room_id = ft.Ref[str]()
    room_id.current = initial_room

    room_list = ft.Ref[ft.Column]()
    device_list = ft.Ref[ft.Column]()
    room_name = ft.Ref[ft.Text]()
    room_container = ft.Ref[ft.Container]()

    def create_slider_card(title, value_control, accent_color, icon_data, description, min_val, max_val, on_change_handler, initial_value, width=CARD_WIDTH, height=CARD_HEIGHT):
        try:
            divisions = int((max_val - min_val) * 10)
            if divisions <= 0:
                divisions = None
        except Exception:
            divisions = None

        icon_container = ft.Container(
            content=ft.Icon(icon_data, color=accent_color, size=24),
            padding=10, bgcolor=ft.Colors.with_opacity(0.08, accent_color),
            border_radius=12,
        )
        temp_slider = ft.Slider(
            min=min_val,
            max=max_val,
            value=initial_value,
            divisions=divisions,
            label="{value}",
            on_change=on_change_handler,
            active_color=accent_color,
            inactive_color=ft.Colors.with_opacity(0.3, accent_color),
            thumb_color=accent_color,
        )
        card = ft.Card(
            elevation=CARD_ELEVATION,
            #shadow_color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            width=width,
            height=height,
            content=ft.Container(
                padding=12,
                content=ft.Column([
                    ft.Row([
                        icon_container,
                        ft.Column([
                            ft.Text(title, size=16, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                            ft.Text(description, size=12, color=TEXT_SECONDARY)
                        ], spacing=2),
                    ], spacing=12),
                    ft.Container(height=12),
                    value_control,
                    temp_slider,
                ])
            )
        )
        return card

    def create_device_card(device_data: Dict[str, Union[str, int, Any]]):
        is_sensor = device_data.get("type") == "Sensor"
        subtype = device_data.get("subtype", "")

        accent_color = device_data.get("color", COLOR_HUM)

        if device_data.get("type") == "Control" and subtype in ("Thermostat", "Humidity Controller"):
            unit = "°C" if subtype == "Thermostat" else "%"
            target_val = device_data.get("target", 22.0)
            target_text = ft.Text(f"{target_val} {unit}", size=20, weight=ft.FontWeight.W_600, color=accent_color)

            def on_slider_change(e):
                new_v = round(float(e.control.value), 1)
                device_data["target"] = new_v
                target_text.value = f"{new_v} {unit}"
                page.update()

            slider_card = create_slider_card(
                title=device_data.get("name", subtype),
                value_control=ft.Row([target_text], alignment=ft.MainAxisAlignment.START),
                accent_color=accent_color,
                icon_data=device_data.get("icon", ft.Icons.THERMOSTAT),
                description=subtype.lower(),
                min_val=(16.0 if subtype == "Thermostat" else 0),
                max_val=(40.0 if subtype == "Thermostat" else 100),
                on_change_handler=on_slider_change,
                initial_value=float(device_data.get("target", 22.0)),
                width=CARD_WIDTH
            )

            remove_btn = ft.ElevatedButton(
                "remove",
                icon=ft.Icons.DELETE_FOREVER,
                on_click=lambda e: remove_device(room_id.current, device_data["id"]),
                style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_DANGER, shape=ft.RoundedRectangleBorder(radius=8)),
                width=CARD_WIDTH
            )

            return ft.Container(
                width=CARD_WIDTH,
                content=ft.Column([
                    slider_card,
                    ft.Container(height=6),
                    remove_btn
                ], tight=True)
            )


        if device_data.get("type") == "Control" and device_data.get("subtype") == "Light Switch":
            status = device_data.get("status", "OFF")
            on_color = COLOR_SUCCESS
            off_color = COLOR_LIGHT
            accent_color = on_color if status == "ON" else off_color

            toggle_btn = ft.ElevatedButton(
                "ON" if status == "ON" else "OFF",
                on_click=lambda e: toggle_light(device_data),
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=accent_color,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                width=100
            )

            card = ft.Card(
                elevation=CARD_ELEVATION,
                color=CARD_BG,
                shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
                width=CARD_WIDTH,
                height=CARD_HEIGHT,
                content=ft.Container(
                    padding=12,
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(
                                    device_data.get("icon", ft.Icons.LIGHTBULB),
                                    color=accent_color,
                                    size=24
                                ),
                                padding=8,
                                bgcolor=ft.Colors.with_opacity(0.08, accent_color),
                                border_radius=10
                            ),
                            ft.Column([
                                ft.Text(
                                    device_data.get("name", "Light"),
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_PRIMARY
                                ),
                                ft.Text("Light Switch", size=12, color=TEXT_SECONDARY)
                            ], spacing=2),
                            ft.Container(expand=True),
                            toggle_btn
                        ])
                    ])
                )
            )

            remove_btn = ft.ElevatedButton(
                "remove",
                icon=ft.Icons.DELETE_FOREVER,
                on_click=lambda e: remove_device(room_id.current, device_data["id"]),
                style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_DANGER, shape=ft.RoundedRectangleBorder(radius=8)),
                width=CARD_WIDTH
            )


            return ft.Container(
                width=CARD_WIDTH,
                content=ft.Column([
                    card,
                    ft.Container(height=6),
                    remove_btn
                ], tight=True)
            )

        
        if is_sensor:
            stype = device_data.get("subtype", "Sensor")
            main_status = f"{device_data.get('value','N/A')} {device_data.get('unit','')}".strip()
            icon_data = device_data.get("icon", ft.Icons.SENSOR_WINDOW)
            accent_color = device_data.get("color", COLOR_HUM)

            card = ft.Card(
                elevation=CARD_ELEVATION,
                color=CARD_BG,
                shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
                width=CARD_WIDTH,
                height=CARD_HEIGHT,
                content=ft.Container(
                    padding=12,
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(icon_data, color=accent_color, size=24),
                                padding=8,
                                bgcolor=ft.Colors.with_opacity(0.08, accent_color),
                                border_radius=10
                            ),
                            ft.Column([
                                ft.Text(
                                    device_data.get("name", "Sensor"),
                                    size=16,
                                    weight=ft.FontWeight.W_600,
                                    color=TEXT_PRIMARY
                                ),
                                ft.Text(stype, size=12, color=TEXT_SECONDARY),
                            ], spacing=2),
                        ], spacing=12),

                        ft.Container(height=8),
                        ft.Text(main_status, size=20, weight=ft.FontWeight.BOLD, color=accent_color),
                        ft.Text("reading", size=12, color=TEXT_SECONDARY),
                    ])
                )
            )

            remove_btn = ft.ElevatedButton(
                "remove",
                icon=ft.Icons.DELETE_FOREVER,
                on_click=lambda e: remove_device(room_id.current, device_data["id"]),
                style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_DANGER, shape=ft.RoundedRectangleBorder(radius=8)),
                width=CARD_WIDTH
            )

            return ft.Container(
                width=CARD_WIDTH,
                content=ft.Column([
                    card,
                    ft.Container(height=6),
                    remove_btn
                ], tight=True)
            )




    def toggle_light(device):
        device["status"] = "ON" if device.get("status") == "OFF" else "OFF"
        update_device_list()
        page.update()

    def get_initial_device_controls(room_id_str):
        if room_id_str in a_devices and a_devices[room_id_str]:
            device_cards = [create_device_card(dev) for dev in a_devices[room_id_str]]
            return [ft.Row(device_cards, spacing=16, wrap=True, alignment=ft.MainAxisAlignment.START)]
        return [ft.Text("no devices yet, add one to begin", color=TEXT_SECONDARY, size=14)]

    def update_room_list():
        if room_list.current:
            room_list.current.controls.clear()
            room_list.current.controls.extend([create_room(room) for room in a_rooms])

    def update_device_list():
        d_room_id = room_id.current
        if device_list.current:
            device_list.current.controls.clear()
            device_list.current.controls.extend(get_initial_device_controls(d_room_id))

    def remove_device(d_room_id, device_id):
        global a_rooms, a_devices
        if d_room_id in a_devices:
            a_devices[d_room_id] = [d for d in a_devices[d_room_id] if d["id"] != device_id]
            for room in a_rooms:
                if room["id"] == d_room_id:
                    room["device_count"] = len(a_devices[d_room_id])
                    break
            update_room_list()
            update_device_list()
            page.update()

    def add_room(e, room_name_entry, dlg):
        global a_rooms, a_devices
        new_name = room_name_entry.value.strip()
        page.close(dlg)
        if new_name:
            new_id = f"r{len(a_rooms) + 1}"
            a_rooms.append({"id": new_id, "name": new_name, "icon": ft.Icons.ROOM_SERVICE, "device_count": 0})
            a_devices[new_id] = []
            if len(a_rooms) == 1:
                room_id.current = new_id
                if room_name.current:
                    room_name.current.value = new_name
            update_room_list()
            update_device_list()
            page.update()

    def add_device(e, d_room_id, device_name_entry, device_type_dd, device_subtype_dd, dlg):
        global a_rooms, a_devices
        new_name = device_name_entry.value.strip()
        new_type = device_type_dd.value
        page.close(dlg)
        if new_name and new_type and d_room_id:
            total_devices = sum(len(v) for v in a_devices.values())
            new_dev_id = f"d{total_devices + 1}"
            type_storage = "Sensor" if new_type.lower() == "sensor" else "Control"
            new_dev_data: Dict[str, Any] = {"id": new_dev_id, "name": new_name, "type": type_storage}

            subtype_val = None
            if device_subtype_dd:
                subtype_val = device_subtype_dd.value

            if type_storage == "Sensor":
                st = subtype_val or "Thermometer"
                new_dev_data["subtype"] = st
                if st == "Thermometer":
                    new_dev_data.update({"value": "22.0", "unit": "°C", "icon": ft.Icons.THERMOSTAT, "color": COLOR_TEMP})
                elif st == "Humidity Sensor":
                    new_dev_data.update({"value": "45", "unit": "%", "icon": ft.Icons.WATER_DROP, "color": COLOR_HUM})
                elif st == "Light Sensor":
                    new_dev_data.update({"value": "300", "unit": "lux", "icon": ft.Icons.FLASH_ON, "color": COLOR_LIGHT})
                else:
                    new_dev_data.update({"value": "N/A", "unit": "", "icon": ft.Icons.DEVICE_UNKNOWN, "color": COLOR_HUM})

            else:
                st = subtype_val or "Light Switch"
                new_dev_data["subtype"] = st
                new_dev_data.update({"status": "OFF"})
                if st == "Light Switch":
                    new_dev_data.update({"icon": ft.Icons.LIGHTBULB, "color": COLOR_LIGHT})
                elif st == "Humidity Controller":
                    new_dev_data.update({"icon": ft.Icons.WATER_DROP, "color": COLOR_HUM, "target": 50.0})
                elif st == "Thermostat":
                    new_dev_data.update({"icon": ft.Icons.THERMOSTAT_ROUNDED, "color": COLOR_TEMP, "target": 22.0})
                else:
                    new_dev_data.update({"icon": ft.Icons.SETTINGS_INPUT_COMPONENT, "color": COLOR_HUM})

            a_devices.setdefault(d_room_id, []).append(new_dev_data)
            for room in a_rooms:
                if room["id"] == d_room_id:
                    room["device_count"] = len(a_devices[d_room_id])
                    break
            update_room_list()
            update_device_list()
            page.update()

    def add_room_thing(e):
        room_name_entry = ft.TextField(label="new room name", autofocus=True)
        dlg = ft.AlertDialog(
            modal=True, title=ft.Text("add new room"), content=room_name_entry,
            actions=[
                ft.TextButton("cancel", on_click=lambda e: page.close(dlg) or page.update()),
                ft.ElevatedButton("add room", on_click=lambda e: add_room(e, room_name_entry, dlg), style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS)),
            ], actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def add_device_thing(e):
        d_room_id = room_id.current
        if not d_room_id:
            return
        device_name_entry = ft.TextField(label="device name")

        device_type_dd = ft.Dropdown(
            label="device type",
            options=[ft.dropdown.Option("Sensor"), ft.dropdown.Option("Controller")],
            value="Sensor"
        )

        sensor_subtype_dd = ft.Dropdown(
            label="sensor type",
            options=[ft.dropdown.Option("Thermometer"), ft.dropdown.Option("Humidity Sensor"), ft.dropdown.Option("Light Sensor")],
            value="Thermometer"
        )

        controller_subtype_dd = ft.Dropdown(
            label="controller type",
            options=[ft.dropdown.Option("Light Switch"), ft.dropdown.Option("Humidity Controller"), ft.dropdown.Option("Thermostat")],
            value="Light Switch"
        )

        sensor_subtype_container = ft.Container(content=sensor_subtype_dd, visible=True)
        controller_subtype_container = ft.Container(content=controller_subtype_dd, visible=False)

        def on_device_type_change(ev):
            sensor_subtype_container.visible = (ev.control.value == "Sensor")
            controller_subtype_container.visible = (ev.control.value == "Controller")
            page.update()

        device_type_dd.on_change = on_device_type_change

        dlg = ft.AlertDialog(
            modal=True, title=ft.Text(f"add device to {room_name.current.value if room_name.current else ''}"),
            content=ft.Column([device_name_entry, device_type_dd, sensor_subtype_container, controller_subtype_container], tight=True),
            actions=[
                ft.TextButton("cancel", on_click=lambda e: page.close(dlg) or page.update()),
                ft.ElevatedButton("add device", on_click=lambda e: add_device(e, d_room_id, device_name_entry, device_type_dd, sensor_subtype_dd if sensor_subtype_container.visible else controller_subtype_dd if controller_subtype_container.visible else None, dlg), style=ft.ButtonStyle(bgcolor=COLOR_SUCCESS)),
            ], actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def create_room(room_data: Dict[str, Any]):
        def select_room(e):
            room_id.current = room_data["id"]
            if room_name.current:
                room_name.current.value = room_data["name"]
            update_room_list()
            update_device_list()
            if room_container.current:
                room_container.current.visible = True
            page.update()

        return ft.Container(
            content=ft.Row([
                ft.Icon(room_data.get("icon", ft.Icons.HOME), color=TEXT_PRIMARY),
                ft.Text(room_data.get("name", "room"), weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                ft.Container(expand=True),
                ft.Text(f'{room_data.get("device_count", 0)}', color=TEXT_SECONDARY),
                ft.Icon(ft.Icons.CHEVRON_RIGHT, color=TEXT_SECONDARY),
            ], alignment=ft.MainAxisAlignment.START, spacing=10),
            padding=ft.padding.symmetric(horizontal=15, vertical=12),
            margin=ft.margin.only(bottom=5),
            bgcolor=ft.Colors.with_opacity(0.05, COLOR_HUM) if room_id.current == room_data["id"] else ft.Colors.TRANSPARENT,
            border_radius=10,
            on_click=select_room,
            ink=True,
        )

    room_title = ft.Text(
        a_rooms[0]["name"] if a_rooms else "no room selected",
        ref=room_name, size=24, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY,
    )

    room_list_column = ft.Column(
        ref=room_list, spacing=6, scroll=ft.ScrollMode.AUTO, height=400,
        controls=[create_room(room) for room in a_rooms]
    )

    device_list_column = ft.Column(
        ref=device_list, spacing=16, scroll=ft.ScrollMode.AUTO,
        controls=get_initial_device_controls(initial_room) if initial_room else [ft.Text("No room selected.", color=TEXT_SECONDARY)]
    )

    panel_height = max(page.height - 200, 300)

    rmgt_panel = ft.Container(
        expand=False,
        width=350,
        height=panel_height,
        content=ft.Card(
            elevation=CARD_ELEVATION,
            shadow_color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            color=CARD_BG,
            shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("rooms", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Divider(height=15, color=TEXT_SECONDARY),
                    room_list_column,
                    ft.Container(height=10),
                    ft.ElevatedButton(
                        "add room", icon=ft.Icons.ADD_HOME_WORK, on_click=add_room_thing,
                        style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_HUM, shape=ft.RoundedRectangleBorder(radius=10)),
                        width=float("inf")
                )
            ])
        )
    )
)

    dmgt_panel = ft.Container(
        expand=True,
        height=panel_height,
        ref=room_container,
        visible=room_id.current is not None,
        content=ft.Card(
            elevation=CARD_ELEVATION, shadow_color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
            color=CARD_BG, shape=ft.RoundedRectangleBorder(radius=CARD_BORDER_RADIUS),
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Row([
                        room_title, ft.Container(expand=True),
                        ft.ElevatedButton(
                            "add device", icon=ft.Icons.ADD_CIRCLE_OUTLINE, on_click=add_device_thing,
                            style=ft.ButtonStyle(color=ft.Colors.WHITE, bgcolor=COLOR_SUCCESS, shape=ft.RoundedRectangleBorder(radius=10))
                        )
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Text("manage devices for this room", color=TEXT_SECONDARY),
                    ft.Divider(height=15, color=TEXT_SECONDARY),
                    ft.Container(content=device_list_column, expand=True, padding=ft.padding.only(top=10))
                ], ft.ScrollMode.AUTO, expand=True)
            )
        ),
    )

    content_column = ft.Column([
        ft.Row([
            ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/"), tooltip="Go Back Home"),
            ft.Text("room setup/customization", size=32, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ], alignment=ft.MainAxisAlignment.START, spacing=10),
        ft.Text("add and organize your devices and so on", size=16, color=TEXT_SECONDARY),
        ft.Container(height=30),
        ft.Row(
            [rmgt_panel, dmgt_panel],
            spacing=20,
            vertical_alignment=ft.CrossAxisAlignment.START,
            alignment=ft.MainAxisAlignment.START,
            wrap=False
        )
    ], scroll=ft.ScrollMode.ADAPTIVE, spacing=0)

    return ft.View(route="/rooms", controls=[content_column], bgcolor=BG_COLOR, padding=SECTION_PADDING, scroll=ft.ScrollMode.ADAPTIVE)
