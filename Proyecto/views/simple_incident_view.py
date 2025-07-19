import flet as ft


class SimpleIncidentView:
    """Vista simplificada para generar incidentes durante la devolución"""

    def __init__(self, app: "VeciRunApp", loan_id, bike_id, user_id, minutes_late: int = 0):  # noqa: F821
        self.app = app
        self.loan_id = loan_id
        self.bike_id = bike_id
        self.user_id = user_id
        self.minutes_late = minutes_late

    def build(self) -> ft.Control:
        """Construye la vista de generación de incidentes"""
        
        print("SimpleIncidentView.build() llamado con:")
        print(f"  loan_id: {self.loan_id}")
        print(f"  bike_id: {self.bike_id}")
        print(f"  user_id: {self.user_id}")
        print(f"  minutes_late: {self.minutes_late}")

        # Layout principal simplificado
        return ft.Column([
            ft.Text(
                "Generar Incidentes - Devolución (Vista Simplificada)",
                size=24,
                weight=ft.FontWeight.BOLD,
            ),
            ft.Divider(),
            ft.Text(f"Préstamo ID: {self.loan_id}"),
            ft.Text(f"Bicicleta ID: {self.bike_id}"),
            ft.Text(f"Usuario ID: {self.user_id}"),
            ft.Text(f"Minutos de retraso: {self.minutes_late}"),
            ft.Container(height=20),
            ft.ElevatedButton(
                text="Volver a Devoluciones",
                icon=ft.icons.ARROW_BACK,
                on_click=self._go_back,
            ),
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=10)

    def _go_back(self, _):
        """Volver a la vista de devoluciones"""
        from .return_view import ReturnView
        self.app.content_area.content = ReturnView(self.app).build()
        self.app.page.update()

    def show(self):
        """Muestra la vista de incidentes"""
        print("SimpleIncidentView.show() llamado")
        self.app.content_area.content = self.build()
        self.app.page.update() 