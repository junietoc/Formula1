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
        """Construye la vista de devoluciones basadas en la estación del administrador.

        El formulario antiguo se ha eliminado. Ahora se muestran todos los
        préstamos *abiertos* cuyo campo ``station_in`` ya apunta a la estación
        asignada al administrador en sesión. El operador simplemente pulsa
        "Registrar devolución" en la fila correspondiente y el préstamo se
        cierra al instante.
        """
        page = self.app.page
        db = self.app.db

        # ------------------------------------------------------------------
        # Validación de contexto: se requiere estación asignada
        # ------------------------------------------------------------------
        station_code: str | None = getattr(self.app, "current_user_station", None)
        if not station_code:
            return ft.Text(
                "Error: No se ha asignado ninguna estación al administrador.",
                color=ft.colors.RED,
                size=16,
            )

        station = StationService.get_station_by_code(db, station_code)
        if not station:
            return ft.Text(
                f"Error: Estación desconocida: {station_code}",
                color=ft.colors.RED,
                size=16,
            )

        # ------------------------------------------------------------------
        # Consultar préstamos abiertos previstos para esta estación
        # ------------------------------------------------------------------
        from models import LoanStatusEnum, Loan  # import local para evitar ciclos

        open_loans: list[Loan] = (
            db.query(Loan)
            .filter(
                Loan.status == LoanStatusEnum.abierto,
                Loan.station_in_id == station.id,
            )
            .all()
        )

        if not open_loans:
            return ft.Column(
                [
                    ft.Text(
                        f"No hay devoluciones pendientes para la estación {station.code} - {station.name}.",
                        size=18,
                        color=ft.colors.GREY_700,
                    )
                ]
            )

        # ------------------------------------------------------------------
        # Helper para mostrar mensajes de resultado
        # ------------------------------------------------------------------
        result_text = ft.Text("")

        def _set_result(msg: str, color: str):
            result_text.value = msg
            result_text.color = color

            # Mostrar SnackBar emergente con el resultado
            page.snack_bar = ft.SnackBar(
                content=ft.Text(msg, color=ft.colors.WHITE),
                bgcolor=color,
                open=True,
                duration=3000,
            )
            page.update()

        # ------------------------------------------------------------------
        # Generar las filas de préstamos
        # ------------------------------------------------------------------
        loan_rows: list[ft.Control] = []

        def _make_return_handler(loan_id):
            def _handler(_: ft.ControlEvent):
                try:
                    # Obtener el préstamo antes de devolverlo
                    loan = LoanService.get_loan_by_id(db, loan_id)
                    if not loan:
                        _set_result("Préstamo no encontrado", ft.colors.RED)
                        return
                    
                    # Calcular minutos de retraso
                    minutes_late = 0
                    if loan.time_out:
                        loan_time = loan.time_out
                        if loan_time.tzinfo is None:
                            loan_time = loan_time.replace(tzinfo=CO_TZ)
                        minutes_late = int((now - loan_time).total_seconds() // 60)
                        if minutes_late <= 15:  # No es tardío
                            minutes_late = 0
                    
                    # Registrar la devolución solo si no está cerrado
                    if loan.status == LoanStatusEnum.abierto:
                        LoanService.return_loan(db, loan_id=loan_id, station_in_id=station.id)
                    else:
                        print(f"Préstamo ya está cerrado con status: {loan.status}")
                    
                    # Redirigir a la vista de incidentes
                    print(f"Creando vista de incidentes con:")
                    print(f"  loan_id: {loan_id} (tipo: {type(loan_id)})")
                    print(f"  bike_id: {loan.bike_id} (tipo: {type(loan.bike_id)})")
                    # Verificar si hay un usuario actual
                    if not self.app.current_user:
                        _set_result("Error: No hay usuario autenticado", ft.colors.RED)
                        return
                    
                    print(f"  user_id: {self.app.current_user.id} (tipo: {type(self.app.current_user.id)})")
                    print(f"  minutes_late: {minutes_late}")
                    
                    from .incident_view import IncidentView
                    incident_view = IncidentView(
                        app=self.app,
                        loan_id=loan_id,  # Ya es UUID
                        bike_id=loan.bike_id,  # Ya es UUID
                        user_id=self.app.current_user.id,  # Ya es UUID
                        minutes_late=minutes_late,
                    )
                    incident_view.show()
                    
                except Exception as exc:  # noqa: BLE001
                    print(f"Error en devolución: {exc}")
                    import traceback
                    traceback.print_exc()
                    _set_result(str(exc), ft.colors.RED)

            return _handler


        from datetime import datetime, timezone, timedelta
        # Zona horaria de Colombia (UTC-5)
        CO_TZ = timezone(timedelta(hours=-5))
        ALERT_MINUTES = 15

        now = datetime.now(CO_TZ)

        for loan in open_loans:
            user_label = f"{loan.user.full_name} (CC {loan.user.cedula})"
            bike_label = loan.bike.bike_code
            date_label = loan.time_out.strftime("%d/%m/%Y %H:%M") if loan.time_out else "-"

            # Calcular minutos transcurridos
            minutes_elapsed = None
            is_late = False
            if loan.time_out:
                # Asegura que ambos datetime sean aware
                loan_time = loan.time_out
                if loan_time.tzinfo is None:
                    loan_time = loan_time.replace(tzinfo=CO_TZ)
                minutes_elapsed = int((now - loan_time).total_seconds() // 60)
                is_late = minutes_elapsed > ALERT_MINUTES

            # Alerta visual si es tardío
            tile_bg = ft.colors.RED_100 if is_late else None
            alert_icon = ft.Icon(ft.icons.WARNING, color=ft.colors.RED, tooltip=f"¡Préstamo tardío! Tiempo transcurrido: {minutes_elapsed} min. (máx. {ALERT_MINUTES} min)") if is_late else None

            # Crear una tarjeta más simple y robusta
            tile = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.BLUE),
                            ft.Text(f"Bicicleta: {bike_label}", 
                                   weight=ft.FontWeight.BOLD, size=16),
                            ft.Container(expand=True),
                            alert_icon if alert_icon else ft.Container(),
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Column([
                                ft.Text("Usuario:", weight=ft.FontWeight.BOLD),
                                ft.Text(user_label),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Fecha de salida:", weight=ft.FontWeight.BOLD),
                                ft.Text(date_label),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Tiempo transcurrido:", weight=ft.FontWeight.BOLD),
                                ft.Text(f"{minutes_elapsed} min" if minutes_elapsed is not None else "N/A"),
                            ], expand=True),
                            ft.Column([
                                ft.ElevatedButton(
                                    text="Registrar devolución",
                                    icon=ft.icons.CHECK,
                                    on_click=_make_return_handler(loan.id),
                                    width=180,
                                    height=40,
                                ),
                            ]),
                        ]),
                    ]),
                    padding=ft.padding.all(16),
                    bgcolor=tile_bg,
                ),
                margin=ft.margin.only(bottom=10),
            )
            loan_rows.append(tile)

        # ------------------------------------------------------------------
        # Layout final
        # ------------------------------------------------------------------
        return ft.Column(
            [
                ft.Text(
                    f"Devoluciones pendientes – Estación {station.code} - {station.name}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Column(loan_rows, spacing=5, scroll=ft.ScrollMode.AUTO, expand=True),
                ft.Container(height=20),
                result_text,
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )
