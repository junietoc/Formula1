import flet as ft

# ------------------------------------------------------------------
# Integración opcional con *flet-material* para un look más moderno
# ------------------------------------------------------------------
try:
    import flet_material as fm  # type: ignore
except ModuleNotFoundError:  # Entorno sin flet-material (p.ej. CI)
    class _FMStub:  # noqa: D101
        class Buttons(ft.ElevatedButton):  # noqa: D101
            def __init__(self, *_, title: str = "", **kw):
                super().__init__(title or kw.pop("text", ""), **kw)

    fm = _FMStub()  # type: ignore

from services import UserService, StationService, LoanService

from .base import View


class ReturnView(View):
    """Vista para registrar devoluciones de bicicleta (solo admin)."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    def build(self) -> ft.Control:  # noqa: D401
        page = self.app.page
        db = self.app.db

        # ------------------------------------------------------------------
        # Campos del formulario
        # ------------------------------------------------------------------
        FIELD_WIDTH = 450

        user_cedula = ft.TextField(
            label="Cédula del Usuario",
            hint_text="Ingrese la cédula del usuario",
            width=FIELD_WIDTH,
            prefix_icon=ft.icons.BADGE,
        )

        station_dropdown = ft.Dropdown(
            label="Estación de Devolución",
            width=FIELD_WIDTH,
            options=[
                ft.dropdown.Option("EST001", "EST001 - Calle 26"),
                ft.dropdown.Option("EST002", "EST002 - Salida al Uriel Gutiérrez"),
                ft.dropdown.Option("EST003", "EST003 - Calle 53"),
                ft.dropdown.Option("EST004", "EST004 - Calle 45"),
                ft.dropdown.Option("EST005", "EST005 - Edificio Ciencia y Tecnología"),
            ],
            prefix_icon=ft.icons.LOCATION_ON,
            dense=True,
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
            _update_save_button()

        def _set_result(msg: str, color: str) -> None:
            result_text.value = msg
            result_text.color = color

        # ------------------------------------------------------------------
        # Botón estilizado (usa flet-material si está disponible)
        # ------------------------------------------------------------------

        save_btn = fm.Buttons(
            title="Registrar Devolución",
            on_click=_register,
            icon=ft.icons.ASSIGNMENT_RETURN,
            width=240,
            height=48,
        )

        # Deshabilitado hasta que el formulario esté completo
        save_btn.disabled = True
        save_btn.style = ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREY_400)

        # ---------------------------------------
        # Helper para habilitar / deshabilitar botón
        # ---------------------------------------

        def _update_save_button(_: ft.ControlEvent | None = None) -> None:  # noqa: D401
            complete = bool(user_cedula.value and station_dropdown.value)
            save_btn.disabled = not complete
            save_btn.style = ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN if complete else ft.colors.GREY_400,
            )
            page.update()

        # Vincular cambios para habilitar boton
        user_cedula.on_change = _update_save_button
        station_dropdown.on_change = _update_save_button

        # Agrupar controles en un *Card* para mejor estética
        form_controls = ft.Column(
            [user_cedula, station_dropdown, ft.Container(height=10), save_btn],
            spacing=10,
        )

        return ft.Column(
            [
                ft.Text(
                    "Registrar Devolución de Bicicleta",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Card(
                    content=ft.Container(content=form_controls, padding=15, width=FIELD_WIDTH + 40),
                ),
                ft.Container(height=20),
                result_text,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )
