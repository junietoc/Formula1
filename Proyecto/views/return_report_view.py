import flet as ft
from services import IncidentService
from models import IncidentSeverityEnum


class ReturnReportView:
    """Vista para mostrar reportes de devolución"""

    def __init__(self, app: "VeciRunApp"):  # noqa: F821
        self.app = app

    def build(self) -> ft.Control:
        """Construye la vista de reportes de devolución"""
        
        # Obtener todos los reportes de devolución
        from models import ReturnReport, Loan, User, Incident
        from sqlalchemy.orm import joinedload
        
        reports = (
            self.app.db.query(ReturnReport)
            .options(
                joinedload(ReturnReport.loan).joinedload(Loan.user),
                joinedload(ReturnReport.loan).joinedload(Loan.bike),
                joinedload(ReturnReport.incidents),
                joinedload(ReturnReport.creator),
            )
            .order_by(ReturnReport.created_at.desc())
            .all()
        )

        # ------------------------------------------------------------------
        # Filtrar reportes por estación cuando el usuario es administrador
        # ------------------------------------------------------------------
        current_role = getattr(self.app, "current_user_role", None)
        if current_role == "admin":
            station_code = getattr(self.app, "current_user_station", None)
            if station_code:
                reports = [
                    r for r in reports
                    if (
                        (r.loan.station_in and r.loan.station_in.code == station_code)
                        or (r.loan.station_out and r.loan.station_out.code == station_code)
                    )
                ]
        
        if not reports:
            return ft.Column([
                ft.Text(
                    "No hay reportes de devolución registrados",
                    size=18,
                    color=ft.colors.GREY_700,
                )
            ])
        
        # Generar las tarjetas de reportes
        report_cards = []
        
        for report in reports:
            # Obtener incidentes del reporte
            incidents = (
                self.app.db.query(Incident)
                .filter(Incident.return_report_id == report.id)
                .all()
            )
            
            # Crear lista de incidentes
            incidents_list = ft.Column(spacing=5)
            for i, incident in enumerate(incidents, 1):
                severity_days = IncidentService.SEVERITY_DAYS.get(incident.severity, 0)
                severity_enum = IncidentService.SEVERITY_INT_TO_ENUM.get(
                    incident.severity, IncidentSeverityEnum.leve
                )

                # Verificar si ya existe una sanción para este incidente
                from models import Sanction
                existing_sanction = (
                    self.app.db.query(Sanction)
                    .filter(Sanction.incident_id == incident.id)
                    .first()
                )

                # Definir el botón según exista o no la sanción
                if existing_sanction:
                    sanction_button = ft.ElevatedButton(
                        text="Ver Sanción",
                        icon=ft.icons.VISIBILITY,
                        on_click=lambda _e, sanc=existing_sanction: self._view_sanction(sanc),
                        style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=4)),
                    )
                else:
                    sanction_button = ft.ElevatedButton(
                        text="Generar Sanción",
                        icon=ft.icons.GAVEL,
                        on_click=lambda _e, inc=incident: self._generate_sanction(inc),
                        style=ft.ButtonStyle(padding=ft.padding.symmetric(horizontal=10, vertical=4)),
                    )
                
                incident_item = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"#{i}", weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(f"{incident.type.value.title()}", size=12),
                            ft.Text(f"{severity_enum.value.title()}", size=12),
                            ft.Text(f"{severity_days} días", size=12, color=ft.colors.BLUE),
                        ]),
                        ft.Text(incident.description, size=11, color=ft.colors.GREY_600),
                        sanction_button,
                    ]),
                    padding=ft.padding.all(8),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=4,
                )
                incidents_list.controls.append(incident_item)
            
            # Crear tarjeta del reporte
            report_card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.REPORT, color=ft.colors.BLUE),
                            ft.Text(
                                f"Reporte #{str(report.id)[:8]}...",
                                weight=ft.FontWeight.BOLD,
                                size=16,
                            ),
                            ft.Container(expand=True),
                            ft.Text(
                                f"{report.total_incident_days} días total",
                                color=ft.colors.BLUE,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Column([
                                ft.Text("Usuario:", weight=ft.FontWeight.BOLD, size=12),
                                ft.Text(
                                    f"{report.loan.user.full_name} (CC {report.loan.user.cedula})",
                                    size=12,
                                ),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Bicicleta:", weight=ft.FontWeight.BOLD, size=12),
                                ft.Text(report.loan.bike.bike_code, size=12),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Est. Salida:", weight=ft.FontWeight.BOLD, size=12),
                                ft.Text(
                                    f"{report.loan.station_out.code} - {report.loan.station_out.name}" if report.loan.station_out else "-",
                                    size=12,
                                ),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Est. Llegada:", weight=ft.FontWeight.BOLD, size=12),
                                ft.Text(
                                    f"{report.loan.station_in.code} - {report.loan.station_in.name}" if report.loan.station_out else "-",
                                    size=12,
                                ),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Fecha:", weight=ft.FontWeight.BOLD, size=12),
                                ft.Text(
                                    report.created_at.strftime("%d/%m/%Y %H:%M"),
                                    size=12,
                                ),
                            ], expand=True),
                        ]),
                        ft.Container(height=10),
                        ft.Text(
                            f"Incidentes ({len(incidents)}):",
                            weight=ft.FontWeight.BOLD,
                            size=14,
                        ),
                        incidents_list,
                    ]),
                    padding=ft.padding.all(16),
                ),
                margin=ft.margin.only(bottom=16),
            )
            
            report_cards.append(report_card)
        
        # Layout principal
        return ft.Column([
            ft.Text(
                "Reportes de Devolución",
                size=24,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Divider(),
            ft.Text(
                f"Total de reportes: {len(reports)}",
                size=16,
                color=ft.colors.GREY_600,
            ),
            ft.Container(height=20),
            ft.Column(
                report_cards,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)

    def _generate_sanction(self, incident):
        """Genera una sanción básica para el incidente proporcionado y muestra confirmación"""
        from models import Sanction
        from datetime import datetime, timedelta, timezone

        # Calcular duración en días basado en severidad
        days = IncidentService.SEVERITY_DAYS.get(incident.severity, 0)
        if days == 0:
            # No se requiere sanción si la severidad no está mapeada
            self.app.page.snack_bar = ft.SnackBar(
                content=ft.Text("La severidad del incidente no requiere sanción."),
                open=True,
            )
            self.app.page.update()
            return

        # Crear la sanción en la base de datos
        operator_uuid = None
        current_user_obj = getattr(self.app, "current_user", None)
        if current_user_obj is not None:
            operator_uuid = current_user_obj.id

        sanction = Sanction(
            user_id=incident.loan.user_id,
            incident_id=incident.id,
            operator_id=operator_uuid,
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=days),
        )
        self.app.db.add(sanction)
        self.app.db.commit()

        # Refrescar la vista para que el botón cambie a "Ver Sanción"
        self.app.content_area.content = self.build()
        self.app.page.update()

        # Mostrar información de la sanción recién creada
        self._view_sanction(sanction)

    def _view_sanction(self, sanction):
        """Muestra un diálogo con los detalles de la sanción"""
        import datetime as _dt

        def _close(_):
            dialog.open = False
            self.app.page.update()

        status_text = sanction.status.value if hasattr(sanction.status, "value") else str(sanction.status)

        # Obtener datos del usuario para mostrar nombre y cédula
        user_obj = getattr(sanction, "user", None)
        if user_obj is None:
            from models import User
            user_obj = self.app.db.query(User).filter(User.id == sanction.user_id).first()

        user_line = "Desconocido"
        if user_obj is not None:
            user_line = f"{user_obj.full_name} (CC {user_obj.cedula})"

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detalle de Sanción"),
            content=ft.Column([
                ft.Text(f"Usuario: {user_line}"),
                ft.Text(f"Incidente ID: {sanction.incident_id}"),
                ft.Text(f"Inicio: {sanction.start_at.strftime('%d/%m/%Y %H:%M') if sanction.start_at else ''}"),
                ft.Text(f"Fin: {sanction.end_at.strftime('%d/%m/%Y %H:%M') if sanction.end_at else ''}"),
                ft.Text(f"Estado: {status_text}"),
            ], tight=True, spacing=5),
            actions=[
                ft.TextButton("Cerrar", on_click=_close),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.app.page.dialog = dialog
        dialog.open = True
        self.app.page.update()

    def show(self):
        """Muestra la vista de reportes"""
        self.app.content_area.content = self.build()
        self.app.page.update() 