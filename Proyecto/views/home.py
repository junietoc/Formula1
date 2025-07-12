import flet as ft

from models import UserRoleEnum
from services import UserService

from .base import View


class HomeView(View):
    """Vista de inicio / pantalla de login."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    # ------------------------------------------------------------------
    def build(self) -> ft.Control:  # noqa: D401
        page = self.app.page
        db = self.app.db

        # Si ya hay usuario logeado, redirige a dashboard
        if hasattr(self.app, "current_user_role") and self.app.current_user_role:
            self.app.show_dashboard_view()
            return ft.Container()  # Control dummy; nunca se muestra

        # ----------------------
        # Controles auxiliares
        # ----------------------
        role_dropdown = ft.Dropdown(
            label="Rol de Usuario",
            width=350,
            options=[
                ft.dropdown.Option("regular", "Usuario Regular"),
                ft.dropdown.Option("admin", "Administrador"),
            ],
            value="regular",
            border_color=ft.colors.BLUE,
            focused_border_color=ft.colors.BLUE_400,
        )

        station_dropdown = ft.Dropdown(
            label="Seleccione una estación",
            width=350,
            options=[
                ft.dropdown.Option("EST001", "Calle 26"),
                ft.dropdown.Option("EST002", "Salida al Uriel Gutiérrez"),
                ft.dropdown.Option("EST003", "Calle 53"),
                ft.dropdown.Option("EST004", "Calle 45"),
                ft.dropdown.Option("EST005", "Edificio Ciencia y Tecnología"),
            ],
            visible=False,
            border_color=ft.colors.BLUE,
            focused_border_color=ft.colors.BLUE_400,
        )

        station_container = ft.Container(
            content=ft.Column(
                [
                    ft.Text("Estación Asignada", size=16, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "(Requerido para administradores)",
                        size=12,
                        color=ft.colors.GREY_600,
                    ),
                    ft.Container(height=10),
                    station_dropdown,
                ]
            ),
            padding=ft.padding.only(bottom=20),
            visible=False,
        )

        cedula_field = ft.TextField(
            label="Cédula",
            hint_text="Ingrese su cédula",
            width=350,
            visible=True,
        )

        status_text = ft.Text("", visible=False)

        # ---------------------------
        # Handlers
        # ---------------------------
        def on_role_change(_: ft.ControlEvent) -> None:  # noqa: D401
            if role_dropdown.value == "admin":
                station_container.visible = True
                station_dropdown.visible = True
                cedula_field.visible = False
            else:
                station_container.visible = False
                station_dropdown.visible = False
                station_dropdown.value = None
                cedula_field.visible = True
            page.update()

        role_dropdown.on_change = on_role_change

        def sign_in_click(_: ft.ControlEvent) -> None:  # noqa: D401
            # Validación específica de admin
            if role_dropdown.value == "admin" and not station_dropdown.value:
                _set_status(
                    "Por favor seleccione una estación para administradores",
                    ft.colors.RED,
                )
                return

            if role_dropdown.value == "regular":
                if not cedula_field.value:
                    _set_status("Por favor ingrese su cédula", ft.colors.RED)
                    return
                user = UserService.get_user_by_cedula(db, cedula_field.value)
                if not user or user.role != UserRoleEnum.usuario:
                    _set_status("Usuario no encontrado o rol inválido", ft.colors.RED)
                    return
                self.app.current_user = user

            # Guardar estado global
            self.app.current_user_role = role_dropdown.value
            self.app.current_user_station = (
                station_dropdown.value if role_dropdown.value == "admin" else None
            )

            # Mostrar navegación y dashboard
            self.app.nav_rail.visible = True
            self.app.update_navigation_for_role(role_dropdown.value)
            page.update()

            _set_status("¡Inicio de sesión exitoso!", ft.colors.GREEN)
            page.window_to_front()
            self.app.show_dashboard_view()

        def _set_status(msg: str, color: str) -> None:
            status_text.value = msg
            status_text.color = color
            status_text.visible = True
            page.update()

        sign_in_button = ft.ElevatedButton(
            "Iniciar Sesión",
            width=350,
            height=50,
            on_click=sign_in_click,
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE,
                shape=ft.RoundedRectangleBorder(radius=10),
            ),
        )

        # --------------------------------
        # Tarjeta de inicio de sesión
        # --------------------------------
        sign_in_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Container(
                            content=ft.Row(
                                [
                                    ft.Icon(
                                        ft.icons.DIRECTIONS_BIKE,
                                        size=40,
                                        color=ft.colors.BLUE,
                                    ),
                                    ft.Text(
                                        "VeciRun",
                                        size=32,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLUE,
                                    ),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            padding=ft.padding.only(bottom=20),
                        ),
                        ft.Text(
                            "Sistema de Préstamo de Bicicletas Universitario",
                            size=16,
                            text_align=ft.TextAlign.CENTER,
                            color=ft.colors.GREY_600,
                        ),
                        ft.Container(height=25),
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        "Seleccione su rol",
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.Container(height=10),
                                    role_dropdown,
                                ]
                            ),
                            padding=ft.padding.only(bottom=20),
                        ),
                        ft.Container(content=cedula_field, padding=ft.padding.only(bottom=20)),
                        station_container,
                        ft.Container(content=sign_in_button, padding=ft.padding.only(top=20)),
                        ft.Container(content=status_text, padding=ft.padding.only(top=15)),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=40,
                width=450,
            ),
            elevation=8,
            margin=ft.margin.all(20),
        )

        container = ft.Container(
            content=ft.Column(
                [
                    ft.Container(height=40),
                    ft.Text(
                        "Bienvenido al Sistema VeciRun",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.BLUE_900,
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        "Acceda al sistema seleccionando su rol correspondiente",
                        size=18,
                        text_align=ft.TextAlign.CENTER,
                        color=ft.colors.GREY_700,
                    ),
                    ft.Container(height=40),
                    ft.Row([sign_in_card], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=40),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
            ),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.colors.BLUE_50, ft.colors.WHITE],
            ),
            expand=True,
        )

        return container
