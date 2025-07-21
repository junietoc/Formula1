from __future__ import annotations

import flet as ft

# -------------------------------------------------------------------
# Optional integration with *flet-material* for consistent styling
# -------------------------------------------------------------------
try:
    import flet_material as fm  # type: ignore
except ModuleNotFoundError:  # CI or environments without flet-material
    class _FMStub:  # noqa: D101
        pass

    fm = _FMStub()  # type: ignore

from services import LoanService, IncidentService
from models import LoanStatusEnum
from .base import View


class CurrentLoanView(View):
    """View that lets a *regular* user check their active loan."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    # ------------------------------------------------------------------
    # Helpers de interfaz
    # ------------------------------------------------------------------
    def _show_incidents_dialog(self, loan):
        """Muestra un diálogo con los incidentes y posibles sanciones del préstamo"""

        db = self.app.db

        from models import Sanction  # Importar local para evitar ciclos

        incidents = IncidentService.get_incidents_by_loan(db, loan.id)

        if not incidents:
            # Fallback: debería no ocurrir porque sólo se llama si hay incidentes,
            # pero por seguridad mostrar mensaje simple
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Sin incidentes"),
                content=ft.Text("Este préstamo no tiene incidentes registrados."),
                actions=[ft.TextButton("Cerrar", on_click=lambda _e: self._close_dialog())],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            self.app.page.dialog = dialog
            dialog.open = True
            self.app.page.update()
            return

        # Construir listado de incidentes
        incident_controls: list[ft.Control] = []

        for i, incident in enumerate(incidents, start=1):
            severity_enum = IncidentService.SEVERITY_INT_TO_ENUM.get(incident.severity)
            severity_str = severity_enum.value.title() if severity_enum else str(incident.severity)

            sanction = (
                db.query(Sanction).filter(Sanction.incident_id == incident.id).first()
            )

            sanction_details: list[ft.Control]
            if sanction:
                status_text = sanction.status.value if hasattr(sanction.status, "value") else str(sanction.status)

                # Seleccionar color según el estado de la sanción
                _status_colors = {
                    "activa": ft.colors.RED_400,
                    "apelada": ft.colors.ORANGE_400,
                    "expirada": ft.colors.GREY_600,
                }
                status_color = _status_colors.get(getattr(sanction.status, "name", ""), ft.colors.GREY_600)

                sanction_details = [
                    ft.Row([
                        ft.Text("Sanción:", weight=ft.FontWeight.BOLD),
                        ft.Text(status_text, color=status_color),
                    ], spacing=5),
                    ft.Text(
                        f"Inicio: {sanction.start_at.strftime('%d/%m/%Y %H:%M')}",
                        size=11,
                    ),
                    ft.Text(
                        f"Fin: {sanction.end_at.strftime('%d/%m/%Y %H:%M')}",
                        size=11,
                    ),
                ]

                # Mostrar información de apelación y respuesta, si existen
                if sanction.appeal_text:
                    sanction_details.extend([
                        ft.Divider(),
                        ft.Text("Motivo de la apelación:", weight=ft.FontWeight.BOLD, size=11),
                        ft.Text(sanction.appeal_text, size=11),
                    ])

                    if sanction.appeal_response:
                        sanction_details.extend([
                            ft.Text("Respuesta del operador:", weight=ft.FontWeight.BOLD, size=11),
                            ft.Text(sanction.appeal_response or "(sin respuesta)", size=11),
                        ])

                # Indicar si fue rechazada o aceptada (independiente de respuesta)
                if sanction.status.name == "activa":
                    sanction_details.append(
                        ft.Text("Apelación rechazada", color=ft.colors.RED_400, size=11)
                    )
                elif sanction.status.name == "expirada":
                    sanction_details.append(
                        ft.Text("Apelación aceptada", color=ft.colors.GREEN, size=11)
                    )
                # Mostrar botón solo si la sanción está activa y nunca ha sido apelada
                if getattr(sanction.status, "name", "") == "activa" and not sanction.appeal_text:
                    sanction_details.append(
                        ft.ElevatedButton(
                            "Apelar Sanción",
                            icon=ft.icons.GAVEL,
                            style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=8, vertical=4)),
                            on_click=lambda _e, sanc=sanction: self._show_appeal_dialog(sanc),
                        )
                    )
            else:
                sanction_details = [ft.Text("Sin sanción asociada", size=11, color=ft.colors.GREY_600)]

            incident_controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"Incidente #{i}", weight=ft.FontWeight.BOLD),
                            ft.Container(width=10),
                            ft.Text(incident.type.value.title()),
                            ft.Container(width=10),
                            ft.Text(severity_str, color=ft.colors.BLUE_600),
                        ], spacing=0),
                        ft.Text(incident.description or "Sin descripción", size=11),
                        *sanction_details,
                    ], spacing=4),
                    padding=ft.padding.all(8),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=4,
                )
            )

        def _close(_):
            self._close_dialog()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalles de Incidentes"),
            content=ft.Container(
                content=ft.Column(
                    incident_controls,
                    tight=False,
                    spacing=8,
                    scroll=ft.ScrollMode.ADAPTIVE,
                ),
                width=600,
            ),
            actions=[ft.TextButton("Cerrar", on_click=_close)],
            actions_alignment=ft.MainAxisAlignment.END,
            shape=ft.RoundedRectangleBorder(radius=8),
        )

        self.app.page.dialog = dialog
        dialog.open = True
        self.app.page.update()

    def _close_dialog(self):
        """Cierra el diálogo actual (si existe)"""
        dlg = getattr(self.app.page, "dialog", None)
        if dlg is not None:
            dlg.open = False
            self.app.page.update()

    # ------------------------------------------------------------------
    # Apelación de sanción
    # ------------------------------------------------------------------

    def _show_appeal_dialog(self, sanction):  # noqa: D401
        """Muestra un diálogo para que el usuario envíe la apelación."""

        from models import SanctionStatusEnum  # Import local para evitar ciclos

        # Seguridad: impedir múltiples apelaciones desde otros clientes o versiones
        if sanction.appeal_text:
            self.app.page.snack_bar = ft.SnackBar(
                content=ft.Text("La sanción ya ha sido apelada."),
                open=True,
            )
            self.app.page.update()
            return

        appeal_field = ft.TextField(label="Motivo de la apelación", multiline=True, width=400)

        def _submit(_):  # noqa: D401
            text = appeal_field.value.strip()
            if text:
                sanction.appeal_text = text
                sanction.status = SanctionStatusEnum.apelada
                self.app.db.commit()
                self._close_dialog()
                # Notificar al usuario
                self.app.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Apelación enviada."),
                    open=True,
                )
                self.app.page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Apelar Sanción"),
            content=appeal_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda _e: self._close_dialog()),
                ft.TextButton("Enviar", on_click=_submit),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.app.page.dialog = dlg
        dlg.open = True
        self.app.page.update()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:  # noqa: D401
        db = self.app.db

        # ------------------------------------------------------------------
        # Mostrar TODOS los préstamos (historial completo) del usuario
        # ------------------------------------------------------------------
        from datetime import datetime

        user = getattr(self.app, "current_user", None)
        if user is None:
            return ft.Text("Error: ningún usuario autenticado.", color=ft.colors.RED, size=16)

        # Obtener el historial completo de préstamos (abiertos y cerrados)
        loans = LoanService.get_loans_by_user(db, user.id)

        # ------------------------------------------------------------------
        # Sin préstamos registrados
        # ------------------------------------------------------------------
        if not loans:
            return ft.Column(
                [
                    ft.Icon(ft.icons.DIRECTIONS_BIKE, size=64, color=ft.colors.GREY_400),
                    ft.Text(
                        "No tienes préstamos registrados",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.GREY_700,
                    ),
                    ft.Text(
                        "Cuando solicites tu primera bicicleta, aparecerá aquí.",
                        size=16,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )

        # Colores asociados a cada estado de préstamo
        status_colors = {
            LoanStatusEnum.abierto: ft.colors.GREEN,
            LoanStatusEnum.cerrado: ft.colors.BLUE,
            LoanStatusEnum.tardio: ft.colors.ORANGE,
            LoanStatusEnum.perdido: ft.colors.RED,
        }

        # --------------------------------------------------
        # Helper para construir una tarjeta de préstamo
        # --------------------------------------------------
        def build_loan_card(loan):
            bike_code = loan.bike.bike_code if loan.bike else "N/A"
            station_out = (
                f"{loan.station_out.code} - {loan.station_out.name}" if loan.station_out else "N/A"
            )
            station_in = (
                f"{loan.station_in.code} - {loan.station_in.name}" if loan.station_in else "Pendiente"
            )

            time_out_str = loan.time_out.strftime("%d/%m/%Y %H:%M") if loan.time_out else "N/A"
            time_in_str = loan.time_in.strftime("%d/%m/%Y %H:%M") if loan.time_in else "Pendiente"

            # --------------------------------------------------
            # Comprobar incidentes y estado de sus sanciones
            # --------------------------------------------------

            incidents = IncidentService.get_incidents_by_loan(db, loan.id)

            from models import Sanction, SanctionStatusEnum  # import local para evitar ciclos

            has_incident = bool(incidents)
            # Determinar si todas las sanciones están expiradas
            all_sanctions_expired = True
            any_appeal_rejected = False

            for incident in incidents:
                sanction = (
                    db.query(Sanction)
                    .filter(Sanction.incident_id == incident.id)
                    .first()
                )

                if sanction is None:
                    all_sanctions_expired = False
                    continue

                # Verificar expiración
                if sanction.status != SanctionStatusEnum.expirada:
                    all_sanctions_expired = False

                # Identificar apelaciones rechazadas
                if (
                    sanction.appeal_text
                    and sanction.status == SanctionStatusEnum.activa
                ):
                    any_appeal_rejected = True

            # Duración
            if loan.status == LoanStatusEnum.abierto and loan.time_out:
                delta = datetime.now() - loan.time_out
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
            elif loan.time_in and loan.time_out:
                delta = loan.time_in - loan.time_out
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = "N/A"

            status_text = loan.status.value.title()
            status_color = status_colors.get(loan.status, ft.colors.GREY)

            # ------------------------------------------------------------------
            # Construir la fila principal con estado e indicador de incidente
            # ------------------------------------------------------------------
            row_controls = [
                ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.BLUE),
                ft.Text(
                    f"Bicicleta: {bike_code}",
                    weight=ft.FontWeight.BOLD,
                    size=16,
                ),
                ft.Container(expand=True),
            ]

            # Indicador de incidente (si existe)
            if has_incident:
                if all_sanctions_expired:
                    # Incidentes resueltos → icono de solución verde
                    icon_symbol = ft.icons.CHECK_CIRCLE
                    icon_clr = ft.colors.GREEN
                    tooltip = "Incidente(s) resuelto(s)"
                elif any_appeal_rejected:
                    # Apelación rechazada → icono de cancelación naranja
                    icon_symbol = ft.icons.CANCEL
                    icon_clr = ft.colors.ORANGE
                    tooltip = "Apelación rechazada"
                else:
                    # Incidentes pendientes o apelación en curso → advertencia roja
                    icon_symbol = ft.icons.REPORT
                    icon_clr = ft.colors.RED
                    tooltip = "Ver incidente(s)"

                row_controls.append(
                    ft.IconButton(
                        icon=icon_symbol,
                        icon_color=icon_clr,
                        tooltip=tooltip,
                        on_click=lambda _e, ln=loan: self._show_incidents_dialog(ln),
                    )
                )

            # Chip de estado del préstamo
            row_controls.append(
                ft.Container(
                    content=ft.Text(status_text, color=ft.colors.WHITE),
                    bgcolor=status_color,
                    padding=ft.padding.all(8),
                    border_radius=ft.border_radius.all(12),
                )
            )

            return ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(row_controls),
                            ft.Divider(),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Estación de salida:", weight=ft.FontWeight.BOLD),
                                            ft.Text(station_out),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Estación de llegada:", weight=ft.FontWeight.BOLD),
                                            ft.Text(station_in),
                                        ],
                                        expand=True,
                                    ),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Fecha de salida:", weight=ft.FontWeight.BOLD),
                                            ft.Text(time_out_str),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Fecha de llegada:", weight=ft.FontWeight.BOLD),
                                            ft.Text(time_in_str),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Duración:", weight=ft.FontWeight.BOLD),
                                            ft.Text(duration_str),
                                        ],
                                        expand=True,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    padding=ft.padding.all(16),
                ),
                margin=ft.margin.only(bottom=10),
            )

        # --------------------------------------------------
        # Separar préstamos actuales y pasados
        # --------------------------------------------------
        open_loans = [ln for ln in loans if ln.status == LoanStatusEnum.abierto]
        past_loans = [ln for ln in loans if ln.status != LoanStatusEnum.abierto]

        # --------------------------------------------------
        # Sección "Préstamo Actual"
        # --------------------------------------------------
        if open_loans:
            current_section = [build_loan_card(open_loans[0])]
        else:
            current_section = [
                ft.Container(
                    content=ft.Text(
                        "No hay ningún préstamo activo",
                        size=16,
                        color=ft.colors.GREY_600,
                    ),
                    padding=ft.padding.all(12),
                )
            ]

        # --------------------------------------------------
        # Sección "Préstamos Pasados"
        # --------------------------------------------------
        past_cards = [build_loan_card(ln) for ln in past_loans] if past_loans else [
            ft.Text("No hay préstamos pasados", size=16, color=ft.colors.GREY_600)
        ]

        return ft.Column(
            [
                # Header y contenido del préstamo actual
                ft.Text(
                    "Préstamo Actual",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_700,
                ),
                ft.Divider(),
                *current_section,
                ft.Container(height=20),
                # Header y contenido de préstamos pasados
                ft.Text(
                    "Préstamos Pasados",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_700,
                ),
                ft.Divider(),
                ft.Column(past_cards, spacing=10),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ) 