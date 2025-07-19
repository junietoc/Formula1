import flet as ft
from datetime import datetime, timezone, timedelta
from services import IncidentService
from models import IncidentTypeEnum, IncidentSeverityEnum

# Zona horaria de Colombia (UTC-5)
CO_TZ = timezone(timedelta(hours=-5))


class IncidentView:
    """Vista para generar incidentes durante la devolución"""

    def __init__(self, app: "VeciRunApp", loan_id, bike_id, user_id, minutes_late: int = 0):  # noqa: F821
        self.app = app
        self.loan_id = loan_id
        self.bike_id = bike_id
        self.user_id = user_id
        self.minutes_late = minutes_late
        self.incidents = []
        self.return_report = None

    def build(self) -> ft.Control:
        """Construye la vista de generación de incidentes"""
        
        # Crear incidente automático si hay retraso
        if self.minutes_late > 15:
            try:
                auto_incident = IncidentService.create_automatic_late_incident(
                    db=self.app.db,
                    loan_id=self.loan_id,
                    bike_id=self.bike_id,
                    reporter_id=self.user_id,
                    minutes_late=self.minutes_late,
                )
                self.incidents.append(auto_incident)
            except Exception as e:
                print(f"Error al crear incidente automático: {e}")
                # Continuar sin el incidente automático

        # Controles para el formulario de incidente
        incident_type_dropdown = ft.Dropdown(
            label="Tipo de incidente",
            options=[
                ft.dropdown.Option("accidente", "Accidentes"),
                ft.dropdown.Option("deterioro", "Deterioro"),
                ft.dropdown.Option("uso_indebido", "Uso indebido"),
                ft.dropdown.Option("otro", "Otro"),
            ],
            width=300,
        )

        severity_dropdown = ft.Dropdown(
            label="Nivel de severidad",
            options=[
                ft.dropdown.Option("leve", "Leve (1 día)"),
                ft.dropdown.Option("media", "Media (3 días)"),
                ft.dropdown.Option("grave", "Grave (7 días)"),
                ft.dropdown.Option("maxima", "Máxima (30 días)"),
            ],
            width=300,
        )

        description_field = ft.TextField(
            label="Descripción del incidente",
            multiline=True,
            min_lines=3,
            max_lines=5,
            width=400,
        )

        # Lista de incidentes generados
        incidents_list = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=200,
        )

        # Información del reporte
        total_days_text = ft.Text("Tiempo total de incidentes: 0 días")
        incident_count_text = ft.Text(f"Incidentes registrados: {len(self.incidents)}")
        
        report_info = ft.Container(
            content=ft.Column([
                ft.Text("Reporte de Devolución", size=20, weight=ft.FontWeight.BOLD),
                total_days_text,
                incident_count_text,
            ]),
            padding=ft.padding.all(16),
            border=ft.border.all(1, ft.colors.GREY_400),
            border_radius=8,
        )

        def update_report_info():
            total_days = sum(
                IncidentService.SEVERITY_DAYS.get(incident.severity, 0)
                for incident in self.incidents
            )
            total_days_text.value = f"Tiempo total de incidentes: {total_days} días"
            incident_count_text.value = f"Incidentes registrados: {len(self.incidents)}"
            self.app.page.update()

        def add_incident(_):
            if not incident_type_dropdown.value or not severity_dropdown.value or not description_field.value:
                self.app.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Por favor complete todos los campos"),
                        bgcolor=ft.colors.RED,
                    )
                )
                return

            try:
                incident = IncidentService.create_incident(
                    db=self.app.db,
                    loan_id=self.loan_id,
                    bike_id=self.bike_id,
                    reporter_id=self.user_id,
                    incident_type=IncidentTypeEnum(incident_type_dropdown.value),
                    severity=IncidentSeverityEnum(severity_dropdown.value),
                    description=description_field.value,
                )
                
                self.incidents.append(incident)
                
                # Limpiar formulario
                incident_type_dropdown.value = None
                severity_dropdown.value = None
                description_field.value = ""
                
                # Actualizar lista y reporte
                refresh_incidents_list()
                update_report_info()
                
                # Forzar actualización de los controles
                self.app.page.update()
                
                self.app.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Incidente agregado exitosamente"),
                        bgcolor=ft.colors.GREEN,
                    )
                )
                
            except Exception as e:
                print(f"Error detallado al crear incidente: {e}")
                import traceback
                traceback.print_exc()
                self.app.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Error al crear incidente: {str(e)}"),
                        bgcolor=ft.colors.RED,
                    )
                )

        def refresh_incidents_list():
            incidents_list.controls.clear()
            
            for i, incident in enumerate(self.incidents, 1):
                severity_days = IncidentService.SEVERITY_DAYS.get(incident.severity, 0)
                severity_enum = IncidentService.SEVERITY_INT_TO_ENUM.get(incident.severity, IncidentSeverityEnum.leve)
                incident_card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"Incidente #{i}", weight=ft.FontWeight.BOLD),
                                ft.Container(expand=True),
                                ft.Text(f"{severity_days} días", color=ft.colors.BLUE),
                            ]),
                            ft.Text(f"Tipo: {incident.type.value.title()}"),
                            ft.Text(f"Severidad: {severity_enum.value.title()}"),
                            ft.Text(f"Descripción: {incident.description}"),
                        ]),
                        padding=ft.padding.all(12),
                    ),
                    margin=ft.margin.only(bottom=8),
                )
                incidents_list.controls.append(incident_card)
            
            # Forzar actualización de la página
            self.app.page.update()

        def finalize_report(_):
            try:
                # Crear reporte de devolución
                self.return_report = IncidentService.create_return_report(
                    db=self.app.db,
                    loan_id=self.loan_id,
                    created_by=self.user_id,
                    incidents=self.incidents,
                )
                
                self.app.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Reporte de devolución finalizado exitosamente"),
                        bgcolor=ft.colors.GREEN,
                    )
                )
                
                # Volver a la vista de devoluciones
                from .return_view import ReturnView
                self.app.content_area.content = ReturnView(self.app).build()
                self.app.page.update()
                
            except Exception as e:
                self.app.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Error al finalizar reporte: {str(e)}"),
                        bgcolor=ft.colors.RED,
                    )
                )

        # Botones
        add_button = ft.ElevatedButton(
            text="Agregar Incidente",
            icon=ft.icons.ADD,
            on_click=add_incident,
        )

        finalize_button = ft.ElevatedButton(
            text="Finalizar Reporte",
            icon=ft.icons.CHECK,
            on_click=finalize_report,
            bgcolor=ft.colors.GREEN,
            color=ft.colors.WHITE,
        )

        # Layout principal
        return ft.Column([
            ft.Text(
                "Generar Incidentes - Devolución",
                size=24,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Divider(),
            
            # Mensaje informativo
            ft.Container(
                content=ft.Text(
                    "Complete el formulario a continuación para agregar incidentes adicionales. "
                    "Luego haga clic en 'Finalizar Reporte' para completar el proceso.",
                    size=14,
                    color=ft.colors.GREY_600,
                ),
                padding=ft.padding.all(10),
                bgcolor=ft.colors.BLUE_50,
                border_radius=8,
            ),
            
            # Información del reporte
            report_info,
            
            ft.Container(height=20),
            
            # Formulario de incidente
            ft.Text("Agregar nuevo incidente:", size=16, weight=ft.FontWeight.BOLD),
            ft.Row([
                incident_type_dropdown,
                severity_dropdown,
            ]),
            ft.Container(height=10),
            description_field,
            ft.Container(height=10),
            add_button,
            
            ft.Container(height=20),
            
            # Lista de incidentes
            ft.Text("Incidentes registrados:", size=16, weight=ft.FontWeight.BOLD),
            incidents_list,
            
            ft.Container(height=20),
            
            # Botón finalizar
            ft.Row([
                ft.Container(expand=True),
                finalize_button,
            ]),
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)

    def show(self):
        """Muestra la vista de incidentes"""
        self.app.content_area.content = self.build()
        self.app.page.update() 