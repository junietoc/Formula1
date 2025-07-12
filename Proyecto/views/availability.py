import flet as ft

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

        return ft.Column(
            [
                ft.Container(height=20),
                header,
                ft.Container(height=10),
                subtitle,
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
