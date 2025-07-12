import flet as ft

from services import UserService, StationService, LoanService

from .base import View


class ReturnView(View):
    """Vista para registrar devoluciones de bicicleta (solo admin)."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    def build(self) -> ft.Control:  # noqa: D401
        page = self.app.page
        db = self.app.db

        user_cedula = ft.TextField(
            label="Cédula del Usuario",
            hint_text="Ingrese la cédula del usuario",
            width=300,
        )

        station_dropdown = ft.Dropdown(
            label="Estación de Devolución",
            width=300,
            options=[
                ft.dropdown.Option("EST001", "EST001 - Calle 26"),
                ft.dropdown.Option("EST002", "EST002 - Salida al Uriel Gutiérrez"),
                ft.dropdown.Option("EST003", "EST003 - Calle 53"),
                ft.dropdown.Option("EST004", "EST004 - Calle 45"),
                ft.dropdown.Option("EST005", "EST005 - Edificio Ciencia y Tecnología"),
            ],
        )

        result_text = ft.Text("", color=ft.colors.GREEN)

        def _register(_: ft.ControlEvent) -> None:  # noqa: D401
            if not all([user_cedula.value, station_dropdown.value]):
                _set_result("Todos los campos son obligatorios", ft.colors.RED)
                return

            open_loans = LoanService.get_open_loans_by_user_cedula(db, user_cedula.value)
            if not open_loans:
                _set_result(
                    "No se encontraron préstamos abiertos para este usuario",
                    ft.colors.RED,
                )
                return
            loan = open_loans[0]
            station = StationService.get_station_by_code(db, station_dropdown.value)
            if not station:
                _set_result("Estación no encontrada", ft.colors.RED)
                return

            LoanService.return_loan(db, loan_id=loan.id, station_in_id=station.id)
            _set_result("Devolución registrada exitosamente", ft.colors.GREEN)
            user_cedula.value = ""
            station_dropdown.value = None
            page.update()

        def _set_result(msg: str, color: str) -> None:
            result_text.value = msg
            result_text.color = color

        save_btn = ft.ElevatedButton(
            "Registrar Devolución",
            icon=ft.icons.ASSIGNMENT_RETURN,
            on_click=_register,
            style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.ORANGE),
        )

        return ft.Column(
            [
                ft.Text(
                    "Registrar Devolución de Bicicleta",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                user_cedula,
                station_dropdown,
                ft.Container(height=20),
                save_btn,
                ft.Container(height=20),
                result_text,
            ],
            scroll=ft.ScrollMode.AUTO,
        ) 