import flet as ft
import os
import base64

from services import StationService, BicycleService

from .base import View


class AvailabilityView(View):
    """Vista para consultar la disponibilidad de bicicletas por estación."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:  # noqa: D401
        """Construye la vista y devuelve el Control principal."""
        page = self.app.page
        db = self.app.db
        # Load campus map v5 with blue circles
        map_file = os.path.join(os.path.dirname(__file__), "campus_mapa.png")
        with open(map_file, "rb") as f:
            map_b64 = base64.b64encode(f.read()).decode()

        # Side panel overlay for pin details (initially empty)
        drawer_container = ft.Container(
            content=ft.Column(
                [],
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            width=300,
            padding=20,
            expand=True,
            right=0,
            top=0,
            visible=False,
            bgcolor=ft.colors.WHITE,
        )

        # Functions to open/close the side panel with dynamic content based on pin id
        def _open_drawer(e: ft.ControlEvent) -> None:
            # Determine which pin was clicked
            pin_id = e.control.data
            # Build details content for each pin
            if pin_id == "calle53":
                details = [
                    ft.Text("Información de Calle 53", weight=ft.FontWeight.BOLD, size=18),
                    ft.Text("Este es un punto de interés ubicado en Calle 53."),
                ]
            elif pin_id == "cyt":
                details = [
                    ft.Text("Información de CyT", weight=ft.FontWeight.BOLD, size=18),
                    ft.Text("Este es el Centro de Tecnología (CyT).")
                ]
            else:
                details = [ft.Text(f"Detalles de {pin_id}")]
            # Close button
            details.append(ft.ElevatedButton("Cerrar", on_click=_close_drawer))
            # Update drawer content and show
            drawer_container.content = ft.Column(details, spacing=10, scroll=ft.ScrollMode.AUTO)
            drawer_container.visible = True
            page.update()

        def _close_drawer(e: ft.ControlEvent) -> None:
            drawer_container.visible = False
            page.update()

        # Define pin positions based on campus map and bind open_drawer with data id
        pins = [
            # Calle 53
            ft.IconButton(
                icon=ft.icons.PIN_DROP,
                icon_color=ft.colors.BLUE,
                data="calle53",
                left=290,
                top=40,
                on_click=_open_drawer
            ),
            # CyT
            ft.IconButton(
                icon=ft.icons.PIN_DROP,
                icon_color=ft.colors.BLUE,
                data="cyt",
                left=315,
                top=320,
                on_click=_open_drawer
            ),
            # agregar más pines con coordenadas apropiadas...
        ]
        
        # Overlay map image and pins
        map_stack = ft.Stack(
            controls=[    # ← primero la imagen escalada… ← fondo
                ft.Image(src_base64=map_b64, width=659)
            ] + pins,       # …luego los pins
            width=659,
            height=669,
        )

        # Obtener datos
        stations = StationService.get_all_stations(db)
        available_bikes = BicycleService.get_available_bicycles(db)

        availability_cards: list[ft.Control] = []
        for station in stations:
            bike_count = sum(1 for bike in available_bikes if bike.current_station_id == station.id)

            card = ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.LOCATION_ON, color=ft.colors.BLUE),
                                title=ft.Text(station.name, size=16, weight=ft.FontWeight.BOLD),
                                subtitle=ft.Text(f"Código: {station.code}", size=12),
                            ),
                            ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(
                                            ft.icons.DIRECTIONS_BIKE,
                                            color=ft.colors.GREEN,
                                        ),
                                        ft.Text(
                                            f"{bike_count} bicicletas disponibles",
                                            size=14,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.colors.GREEN,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                padding=10,
                            ),
                        ]
                    ),
                    padding=10,
                ),
                elevation=2,
            )
            availability_cards.append(card)

        # Encabezado
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

        # Handler de refresco
        def _refresh(_: ft.ControlEvent) -> None:  # noqa: D401
            # Reinserta una nueva instancia de la vista
            self.app.content_area.content = AvailabilityView(self.app).build()
            page.update()

        refresh_btn = ft.ElevatedButton(
            "Actualizar",
            on_click=_refresh,
            icon=ft.icons.REFRESH,
            style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.BLUE),
        )

        # Wrap the main content and the side panel into a Stack
        content_column = ft.Column(
            [
                ft.Container(height=20),
                header,
                ft.Container(height=10),
                subtitle,
                ft.Container(height=20),
                map_stack,
                ft.Container(height=30),
                ft.Row([refresh_btn], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                ft.GridView(
                    runs_count=2,
                    max_extent=300,
                    child_aspect_ratio=1.0,
                    spacing=20,
                    run_spacing=20,
                    controls=availability_cards,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
        return ft.Stack(
            controls=[content_column, drawer_container],
            expand=True,
        )
