import flet as ft

from services import (
    UserService,
    BicycleService,
    StationService,
    LoanService,
)

from .base import View


class LoanView(View):
    """Vista para registrar préstamos de bicicletas (solo admin)."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    def build(self) -> ft.Control:  # noqa: D401
        page = self.app.page
        db = self.app.db

        # -----------------------
        # Campos del formulario
        # -----------------------
        user_cedula = ft.TextField(
            label="Cédula del Usuario",
            hint_text="Ingrese la cédula del usuario",
            width=300,
        )

        station_opts = [
            ft.dropdown.Option("EST001", "EST001 - Calle 26"),
            ft.dropdown.Option("EST002", "EST002 - Salida al Uriel Gutiérrez"),
            ft.dropdown.Option("EST003", "EST003 - Calle 53"),
            ft.dropdown.Option("EST004", "EST004 - Calle 45"),
            ft.dropdown.Option("EST005", "EST005 - Edificio Ciencia y Tecnología"),
        ]

        station_out = ft.Dropdown(label="Estación de Salida", width=300, options=station_opts)
        station_in = ft.Dropdown(
            label="Estación de Llegada",
            width=300,
            options=station_opts,
            disabled=True,
        )

        # --- Sincronizar dropdowns ---
        def _update_station_in(_: ft.ControlEvent) -> None:  # noqa: D401
            out_val = station_out.value
            if not out_val:
                station_in.disabled = True
                station_in.options = station_opts
            else:
                station_in.disabled = False
                station_in.options = [opt for opt in station_opts if opt.key != out_val]
                if station_in.value == out_val:
                    station_in.value = None
            page.update()

        station_out.on_change = _update_station_in

        available_bikes = BicycleService.get_available_bicycles(db)
        bike_radio = ft.RadioGroup(
            content=ft.Column(
                [
                    ft.Radio(value=b.bike_code, label=f"{b.bike_code} - {b.serial_number}")
                    for b in available_bikes
                ]
            )
        )

        result_text = ft.Text("", color=ft.colors.GREEN)

        # -------------------
        # Guardar préstamo
        # -------------------
        def _register(_: ft.ControlEvent) -> None:  # noqa: D401
            # Validaciones
            if not all(
                [
                    user_cedula.value,
                    bike_radio.value,
                    station_out.value,
                    station_in.value,
                ]
            ):
                _set_result("Todos los campos son obligatorios", ft.colors.RED)
                return
            if station_out.value == station_in.value:
                _set_result(
                    "La estación de llegada debe ser diferente a la de salida",
                    ft.colors.RED,
                )
                return

            user = UserService.get_user_by_cedula(db, user_cedula.value)
            if not user:
                _set_result("Usuario no encontrado", ft.colors.RED)
                return
            bike = BicycleService.get_bicycle_by_code(db, bike_radio.value)
            if not bike:
                _set_result("Bicicleta no encontrada", ft.colors.RED)
                return
            st_out = StationService.get_station_by_code(db, station_out.value)
            st_in = StationService.get_station_by_code(db, station_in.value)
            if not st_out or not st_in:
                _set_result("Estación no encontrada", ft.colors.RED)
                return

            # Registrar préstamo
            LoanService.create_loan(
                db,
                user_id=user.id,
                bike_id=bike.id,
                station_out_id=st_out.id,
                station_in_id=st_in.id,
            )
            _set_result("Préstamo registrado exitosamente", ft.colors.GREEN)
            # Limpiar campos
            user_cedula.value = ""
            station_out.value = station_in.value = None
            bike_radio.value = None
            page.update()

        def _set_result(msg: str, color: str) -> None:
            result_text.value = msg
            result_text.color = color

        save_btn = ft.ElevatedButton(
            "Registrar Préstamo",
            on_click=_register,
            style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREEN),
        )

        return ft.Column(
            [
                ft.Text(
                    "Registrar Préstamo de Bicicleta",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                user_cedula,
                station_out,
                station_in,
                ft.Container(height=20),
                bike_radio,
                ft.Container(height=20),
                save_btn,
                ft.Container(height=20),
                result_text,
            ],
            scroll=ft.ScrollMode.AUTO,
        )
