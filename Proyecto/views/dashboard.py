import flet as ft

from models import UserRoleEnum

from .base import View
from views.home import HomeView
from services import FavoriteBikeService


class DashboardView(View):
    """Vista principal posterior al inicio de sesión (panel)."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    def build(self) -> ft.Control:  # noqa: D401
        page = self.app.page
        role = getattr(self.app, "current_user_role", "regular")
        station = getattr(self.app, "current_user_station", None)

        # --- Mensaje de bienvenida ---
        if getattr(self.app, "current_user", None):
            user_name = self.app.current_user.full_name
            welcome_msg = f"¡Bienvenido, {user_name}!"
        else:
            welcome_msg = (
                "¡Bienvenido, Administrador!"
                if role == "admin"
                else "¡Bienvenido, Usuario Regular!"
            )

        welcome_text = ft.Text(
            welcome_msg,
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_900,
        )

        # --- Contenido según rol ---
        if role == "admin":
            station_name = {
                "EST001": "Calle 26",
                "EST002": "Salida al Uriel Gutiérrez",
                "EST003": "Calle 53",
                "EST004": "Calle 45",
                "EST005": "Edificio Ciencia y Tecnología",
            }.get(station, "No asignada")

            body_content = ft.Column(
                [
                    ft.Container(height=30),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.HOME, color=ft.colors.BLUE),
                                        title=ft.Text(
                                            "Página de Inicio",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        subtitle=ft.Text(f"Estación: {station_name}", size=14),
                                    ),
                                    ft.Container(height=20),
                                    ft.Text(
                                        "Bienvenido al sistema VeciRun",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREY_700,
                                    ),
                                    ft.Container(height=10),
                                    ft.Text(
                                        "Utilice el menú lateral para acceder a las diferentes funciones del sistema.",
                                        size=14,
                                        color=ft.colors.GREY_600,
                                    ),
                                    ft.Container(height=20),
                                    ft.Text(
                                        "Funciones disponibles:",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREY_700,
                                    ),
                                    ft.Container(height=10),
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.icons.PERSON_ADD,
                                                        color=ft.colors.GREEN,
                                                        size=20,
                                                    ),
                                                    ft.Text("Crear nuevos usuarios", size=14),
                                                ]
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.icons.DIRECTIONS_BIKE,
                                                        color=ft.colors.ORANGE,
                                                        size=20,
                                                    ),
                                                    ft.Text(
                                                        "Registrar préstamos de bicicletas",
                                                        size=14,
                                                    ),
                                                ]
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.icons.ASSIGNMENT_RETURN,
                                                        color=ft.colors.RED,
                                                        size=20,
                                                    ),
                                                    ft.Text("Registrar devoluciones", size=14),
                                                ]
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.icons.REPORT,
                                                        color=ft.colors.PURPLE,
                                                        size=20,
                                                    ),
                                                    ft.Text("Ver reportes de devolución", size=14),
                                                ]
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                ]
                            ),
                            padding=20,
                        ),
                        elevation=4,
                    ),
                ]
            )
        else:
            # Obtener información de la bicicleta favorita del usuario
            favorite_bike_info = None
            current_user = getattr(self.app, "current_user", None)
            if current_user:
                db = self.app.db
                favorite_bike = FavoriteBikeService.get_user_favorite_bike_by_cedula(db, current_user.cedula)
                if favorite_bike:
                    station_info = f"Estación: {favorite_bike.current_station.code} - {favorite_bike.current_station.name}" if favorite_bike.current_station else "Estación: No disponible"
                    favorite_bike_info = {
                        "code": favorite_bike.bike_code,
                        "station": station_info,
                        "status": favorite_bike.status.value.title()
                    }

            body_content = ft.Column(
                [
                    ft.Container(height=30),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.PERSON, color=ft.colors.GREEN),
                                        title=ft.Text(
                                            "Panel de Usuario",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        subtitle=ft.Text(
                                            "Acceso a información del sistema", size=14
                                        ),
                                    ),
                                    ft.Container(height=20),
                                    ft.Text(
                                        "Como usuario regular, puede:",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREY_700,
                                    ),
                                    ft.Container(height=10),
                                    ft.Column(
                                        [
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.icons.LOCATION_ON,
                                                        color=ft.colors.BLUE,
                                                        size=20,
                                                    ),
                                                    ft.Text(
                                                        "Consultar disponibilidad de bicicletas",
                                                        size=14,
                                                    ),
                                                ]
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.icons.INFO,
                                                        color=ft.colors.GREY,
                                                        size=20,
                                                    ),
                                                    ft.Text(
                                                        "Ver información de estaciones", size=14
                                                    ),
                                                ]
                                            ),
                                            ft.Row(
                                                [
                                                    ft.Icon(
                                                        ft.icons.FAVORITE,
                                                        color=ft.colors.RED,
                                                        size=20,
                                                    ),
                                                    ft.Text(
                                                        "Gestionar bicicleta favorita", size=14
                                                    ),
                                                ]
                                            ),
                                        ],
                                        spacing=10,
                                    ),
                                ]
                            ),
                            padding=20,
                        ),
                        elevation=4,
                    ),
                ]
            )

            # Agregar información de la bicicleta favorita si existe
            if favorite_bike_info:
                body_content.controls.append(
                    ft.Container(height=20)
                )
                body_content.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column(
                                [
                                    ft.ListTile(
                                        leading=ft.Icon(ft.icons.FAVORITE, color=ft.colors.RED),
                                        title=ft.Text(
                                            "Mi Bicicleta Favorita",
                                            size=18,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                        subtitle=ft.Text(
                                            f"Bicicleta {favorite_bike_info['code']}", size=14
                                        ),
                                    ),
                                    ft.Container(height=10),
                                    ft.Text(
                                        f"Ubicación: {favorite_bike_info['station']}",
                                        size=14,
                                        color=ft.colors.GREY_700,
                                    ),
                                    ft.Text(
                                        f"Estado: {favorite_bike_info['status']}",
                                        size=14,
                                        color=ft.colors.GREY_700,
                                    ),
                                ]
                            ),
                            padding=20,
                        ),
                        elevation=4,
                    )
                )

        # Botón logout
        def _logout(_: ft.ControlEvent) -> None:  # noqa: D401
            # Limpiar estado del usuario
            self.app.clear_user_state()
            
            # Ocultar navegación y mostrar pantalla de login
            self.app.nav_rail.visible = False
            self.app.content_area.content = HomeView(self.app).build()
            page.update()

        logout_btn = ft.ElevatedButton(
            "Cerrar Sesión",
            icon=ft.icons.LOGOUT,
            on_click=_logout,
            style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.RED),
        )

        return ft.Column(
            [
                ft.Container(height=20),
                ft.Row([welcome_text, ft.Container(expand=True), logout_btn]),
                ft.Container(height=20),
                body_content,
            ],
            scroll=ft.ScrollMode.AUTO,
        )
