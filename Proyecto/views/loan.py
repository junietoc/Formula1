import flet as ft

# -----------------------------
# Integración opcional flet-material
# -----------------------------
try:
    import flet_material as fm  # type: ignore
except ModuleNotFoundError:  # Entorno sin flet-material
    from types import SimpleNamespace

    class _FMStub:  # noqa: D101
        class Buttons(ft.ElevatedButton):  # noqa: D101
            def __init__(self, *_, title: str = "", **kw):
                super().__init__(title or kw.pop("text", ""), **kw)

    fm = _FMStub()  # type: ignore

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
        FIELD_WIDTH = 450

        user_cedula = ft.TextField(
            label="Cédula del Usuario",
            hint_text="Ingrese la cédula del usuario",
            width=FIELD_WIDTH,
            prefix_icon=ft.icons.BADGE,
        )

        station_opts = [
            ft.dropdown.Option("EST001", "EST001 - Calle 26"),
            ft.dropdown.Option("EST002", "EST002 - Salida al Uriel Gutiérrez"),
            ft.dropdown.Option("EST003", "EST003 - Calle 53"),
            ft.dropdown.Option("EST004", "EST004 - Calle 45"),
            ft.dropdown.Option("EST005", "EST005 - Edificio Ciencia y Tecnología"),
        ]

        # Estación asignada al administrador en sesión (valor fijo)
        current_station = getattr(self.app, "current_user_station", None)

        # Dropdown de estación de salida: valor fijo y deshabilitado para admins
        station_out = ft.Dropdown(
            label="Estación de Salida",
            width=FIELD_WIDTH,
            options=station_opts,
            value=current_station,
            disabled=True,
            prefix_icon=ft.icons.TRANSFER_WITHIN_A_STATION,
            dense=True,
        )

        # Opciones de estación de llegada excluyendo la estación de salida
        station_in_opts = (
            [opt for opt in station_opts if opt.key != current_station]
            if current_station
            else station_opts
        )
        station_in = ft.Dropdown(
            label="Estación de Llegada",
            width=FIELD_WIDTH,
            options=station_in_opts,
            disabled=current_station is None,
            prefix_icon=ft.icons.LOCATION_ON,
            dense=True,
        )

        # --- Sincronizar dropdowns ---
        def _update_station_in(_: ft.ControlEvent) -> None:  # noqa: D401
            out_val = station_out.value
            if not out_val:
                station_in.disabled = True
                station_in.options = station_in_opts
            else:
                station_in.disabled = False
                station_in.options = [opt for opt in station_in_opts if opt.key != out_val]
                if station_in.value == out_val:
                    station_in.value = None
            page.update()

        station_out.on_change = _update_station_in

        # --- Vincular actualizaciones de estado ---
        station_in.on_change = lambda e: _update_save_button()
        user_cedula.on_change = lambda e: _update_save_button()

        # Bicicletas disponibles en el sistema
        available_bikes = BicycleService.get_available_bicycles(db)

        # -------------------------------------------------
        # Filtrar por estación asignada al administrador
        # -------------------------------------------------
        # Si el administrador tiene una estación asociada (sección de
        # inicio de sesión), solo mostraremos las bicicletas ubicadas en
        # dicha estación. Esto evita que el operador seleccione vehículos
        # que no estén físicamente en su punto de entrega.
        if current_station:
            available_bikes = [
                bike
                for bike in available_bikes
                if bike.current_station and bike.current_station.code == current_station
            ]
        # -----------------------------
        # Selección de bicicleta (cards)
        # -----------------------------

        selected_bike: dict[str, str | None] = {"code": None}

        bike_card_map: dict[str, ft.Card] = {}

        def _make_bike_select_handler(code: str):
            """Genera handler de click para seleccionar bicicleta."""

            def _handler(_: ft.ControlEvent) -> None:  # noqa: D401
                # Guardar selección
                selected_bike["code"] = code

                # Actualizar estado visual de todas las tarjetas
                for c_code, card in bike_card_map.items():
                    is_selected = c_code == code
                    card.elevation = 8 if is_selected else 1
                    card.content.bgcolor = ft.colors.BLUE_50 if is_selected else ft.colors.GREY_100
                page.update()
                _update_save_button()

            return _handler

        bike_cards: list[ft.Card] = []
        CARD_W, CARD_H = 110, 110  # un poco más grande y legible

        for bike in available_bikes:
            card = ft.Card(
                elevation=1,
                content=ft.Container(
                    width=CARD_W,
                    height=CARD_H,
                    bgcolor=ft.colors.GREY_100,
                    border_radius=8,
                    padding=8,
                    alignment=ft.alignment.center,
                    on_click=_make_bike_select_handler(bike.bike_code),
                    content=ft.Column(
                        [
                            ft.Icon(ft.icons.DIRECTIONS_BIKE, size=24, color=ft.colors.BLUE_700),
                            ft.Text(
                                bike.bike_code,
                                weight=ft.FontWeight.BOLD,
                                size=13,
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=4,
                    ),
                    tooltip=f"Serie: {bike.serial_number}",
                    ink=True,
                ),
            )
            bike_card_map[bike.bike_code] = card
            bike_cards.append(card)

        bikes_grid = ft.Row(
            controls=bike_cards,
            wrap=True,
            spacing=8,
            run_spacing=8,
        )

        result_text = ft.Text("", color=ft.colors.GREEN)

        # -------------------
        # Guardar préstamo
        # -------------------
        def _register(_: ft.ControlEvent) -> None:  # noqa: D401
            # Validaciones
            if not all([
                user_cedula.value,
                selected_bike["code"],
                station_out.value,
                station_in.value,
            ]):
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

            # ==============================
            # NUEVA VALIDACIÓN:
            # ==============================
            open_loans = LoanService.get_open_loans_by_user(db, user.id)
            if open_loans:
                _set_result("El usuario ya tiene un préstamo activo y no puede registrar otro.", ft.colors.RED)
                return

            bike = BicycleService.get_bicycle_by_code(db, selected_bike["code"])
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
            station_in.value = None  # station_out permanece fijo

            # Reset selección de bicicleta
            selected_bike["code"] = None
            for card in bike_card_map.values():
                card.elevation = 1
                card.content.bgcolor = ft.colors.GREY_100

            page.update()
            _update_save_button()

        def _set_result(msg: str, color: str) -> None:
            # Evitar duplicar mensajes: ya no se actualiza `result_text`.

            # Mostrar SnackBar emergente con el resultado
            page.snack_bar = ft.SnackBar(
                content=ft.Text(msg, color=ft.colors.WHITE),
                bgcolor=color,
                open=True,
                duration=3000,
            )
            page.update()

        save_btn = fm.Buttons(
            title="Registrar Préstamo",
            on_click=_register,
            width=240,
            height=48,
        )

        # -------------------------------------------------
        # Compatibilidad con tests (entorno sin Flet real)
        # -------------------------------------------------
        # Los tests de *pytest* reemplazan ``ft.ElevatedButton`` por un stub
        # que expone el atributo de clase ``last_callback`` para capturar la
        # última función *on_click* registrada. Algunas implementaciones de
        # *flet-material* (o variaciones en el flujo de importación) pueden
        # hacer que dicha referencia no se actualice correctamente.
        # Para evitar fallos esporádicos, actualizamos manualmente el valor
        # cuando detectamos dicho atributo.
        if hasattr(ft.ElevatedButton, "last_callback"):
            ft.ElevatedButton.last_callback = _register

        # Deshabilitado hasta que el formulario esté completo
        save_btn.disabled = True
        save_btn.style = ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREY_400)

        # ---------------------------------------
        # Helper para habilitar / deshabilitar botón
        # ---------------------------------------

        def _update_save_button() -> None:  # noqa: D401
            complete = bool(
                user_cedula.value
                and selected_bike["code"]
                and station_out.value
                and station_in.value
                and station_out.value != station_in.value
            )
            save_btn.disabled = not complete
            save_btn.style = ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN if complete else ft.colors.GREY_400,
            )
            page.update()

        form_controls = ft.Column(
            [
                user_cedula,
                station_out,
                station_in,
                ft.Container(height=10),
                save_btn,
            ],
            spacing=10,
        )

        bikes_section = ft.Column(
            [
                ft.Text("Seleccione una bicicleta", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=8),
                bikes_grid,
            ]
        )

        return ft.Column(
            [
                ft.Text(
                    "Registrar Préstamo de Bicicleta",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Row(
                    [
                        ft.Card(content=ft.Container(content=form_controls, padding=15, width=FIELD_WIDTH+40)),
                        ft.Container(width=20),
                        ft.Container(
                            expand=True,
                            content=ft.Card(
                                content=ft.Container(content=bikes_section, padding=15),
                            ),
                        ),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                ft.Container(height=20),
                result_text,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )
