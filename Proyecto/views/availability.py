import flet as ft
import os
import base64
from threading import Timer

from services import StationService, BicycleService
from .base import View


class AvailabilityView(View):
    """Vista para consultar la disponibilidad de bicicletas por estación,
    con UI mejorada y animación de overlay sin viaje entre pines."""

    MAP_WIDTH = 659
    OVERLAY_WIDTH = 300

    def __init__(self, app: "VeciRunApp") -> None:
        self.app = app

    def build(self) -> ft.Control:
        page = self.app.page
        db = self.app.db

        # Cargar mapa
        map_file = os.path.join(os.path.dirname(__file__), "campus_mapa.png")
        with open(map_file, "rb") as f:
            map_b64 = base64.b64encode(f.read()).decode()

        # Overlay floater con estilo identico a availability_cards
        info_overlay = ft.Card(
            visible=False,
            width=self.OVERLAY_WIDTH,
            elevation=2,
            content=ft.Container(
                padding=10,
                content=ft.Column([]),
            ),
            opacity=0,
            scale=0.8,
            left=0,
            top=0,
            animate_opacity=300,
            animate_scale=300,
        )

        # Función interna para mostrar contenido tras animar oculta
        def _do_show(code, left, top):
            info_overlay.disabled = False
            info_overlay.visible = True
            station = next((s for s in stations if s.code == code), None)
            if station:
                bike_count = sum(1 for b in available_bikes if b.current_station_id == station.id)
                info_overlay.content.content = ft.Column([
                    ft.ListTile(
                        leading=ft.Icon(ft.icons.LOCATION_ON, color=ft.colors.BLUE),
                        title=ft.Text(station.name, weight=ft.FontWeight.BOLD, size=16),
                        subtitle=ft.Text(f"Código: {station.code}", size=12),
                    ),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.GREEN),
                            ft.Text(
                                f"{bike_count} bicicletas disponibles",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREEN,
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER),
                        padding=10,
                    ),
                    ft.ElevatedButton("Cerrar", on_click=lambda ev: _hide_overlay()),
                ], spacing=5)
            else:
                info_overlay.content.content = ft.Column([
                    ft.Text(f"Detalles de {code}", size=14, color=ft.colors.BLACK),
                    ft.ElevatedButton("Cerrar", on_click=lambda ev: _hide_overlay()),
                ])
            # Posicionar sin animación de movimiento
            desired_left = (left or 0) - 50
            max_left = self.MAP_WIDTH - self.OVERLAY_WIDTH
            info_overlay.left = max(0, min(desired_left, max_left))
            info_overlay.top = max((top or 0) - 90, 0)
            # Animar aparición completa
            info_overlay.opacity = 1
            info_overlay.scale = 1
            page.update()

        # Manejar clic en pin
        def _show_overlay(e: ft.ControlEvent) -> None:
            pin = e.control
            # Si ya visible, ocultar primero
            if info_overlay.visible:
                info_overlay.opacity = 0
                info_overlay.scale = 0.8
                page.update()
                Timer(0.1, lambda: _do_show(pin.data, pin.left, pin.top)).start()
            else:
                # Preparar para aparición
                info_overlay.visible = True
                info_overlay.opacity = 0
                info_overlay.scale = 0.8
                page.update()
                Timer(0.1, lambda: _do_show(pin.data, pin.left, pin.top)).start()

        # Ocultar overlay con animación
        def _hide_overlay() -> None:
            info_overlay.disabled = True
            info_overlay.opacity = 0
            info_overlay.scale = 0.8
            page.update()
            Timer(0.1, lambda: (setattr(info_overlay, 'visible', False), setattr(info_overlay, 'disabled', False), page.update())).start()

        # Creador de pines
        def make_pin(code: str, left: int, top: int) -> ft.IconButton:
            return ft.IconButton(
                icon=ft.icons.LOCATION_ON,
                icon_color=ft.colors.BLUE,
                style=ft.ButtonStyle(bgcolor=ft.colors.TRANSPARENT),
                data=code,
                left=left,
                top=top,
                on_click=_show_overlay,
            )

        # Pines
        pins = [
            make_pin("EST001", 450, 590),
            make_pin("EST002", 123, 365),
            make_pin("EST003", 290, 40),
            make_pin("EST004", 600, 438),
            make_pin("EST005", 315, 320),
        ]

        # Obtener datos
        stations = StationService.get_all_stations(db)
        available_bikes = BicycleService.get_available_bicycles(db)

        # Montar mapa y overlay
        map_stack = ft.Stack(
            controls=[ft.Image(src_base64=map_b64, width=self.MAP_WIDTH)] + pins + [info_overlay],
            width=self.MAP_WIDTH,
            height=669,
        )

        # Tarjetas de disponibilidad (mismo estilo)
        availability_cards = []
        for station in stations:
            bike_count = sum(1 for b in available_bikes if b.current_station_id == station.id)
            availability_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.LOCATION_ON, color=ft.colors.BLUE),
                                title=ft.Text(station.name, size=16, weight=ft.FontWeight.BOLD),
                                subtitle=ft.Text(f"Código: {station.code}", size=12),
                            ),
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.GREEN),
                                    ft.Text(
                                        f"{bike_count} bicicletas disponibles",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREEN,
                                    ),
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                padding=10,
                            ),
                        ]),
                        padding=10,
                    ),
                    elevation=2,
                )
            )

        # Encabezados
        header = ft.Text(
            "Disponibilidad de Bicicletas por Estación",
            size=24,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
        )
        subtitle = ft.Text(
            "Consulta la cantidad de bicicletas disponibles en cada estación",
            size=14,
            text_align=ft.TextAlign.CENTER,
            color=ft.colors.GREY_600,
        )

        # Botón refrescar
        def _refresh(_: ft.ControlEvent) -> None:
            self.app.content_area.content = AvailabilityView(self.app).build()
            page.update()

        refresh_btn = ft.ElevatedButton(
            "Actualizar",
            on_click=_refresh,
            icon=ft.icons.REFRESH,
            style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.BLUE),
        )

        # Layout final
        content_column = ft.Column([
            ft.Container(height=20), header, ft.Container(height=10), subtitle,
            ft.Container(height=20), map_stack, ft.Container(height=30),
            ft.Row([refresh_btn], alignment=ft.MainAxisAlignment.CENTER), ft.Container(height=20),
            
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
           scroll=ft.ScrollMode.AUTO)

        return ft.Stack(controls=[content_column], expand=True)
