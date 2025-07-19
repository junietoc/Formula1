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
                
                incident_item = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Text(f"#{i}", weight=ft.FontWeight.BOLD, size=12),
                            ft.Text(f"{incident.type.value.title()}", size=12),
                            ft.Text(f"{severity_enum.value.title()}", size=12),
                            ft.Text(f"{severity_days} días", size=12, color=ft.colors.BLUE),
                        ]),
                        ft.Text(incident.description, size=11, color=ft.colors.GREY_600),
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

    def show(self):
        """Muestra la vista de reportes"""
        self.app.content_area.content = self.build()
        self.app.page.update() 