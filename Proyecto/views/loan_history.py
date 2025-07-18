from __future__ import annotations

import flet as ft
from datetime import datetime

# -------------------------------------------------------------------
# Optional integration with *flet-material* for consistent styling
# -------------------------------------------------------------------
try:
    import flet_material as fm  # type: ignore
except ModuleNotFoundError:  # CI or environments without flet-material
    class _FMStub:  # noqa: D101
        pass

    fm = _FMStub()  # type: ignore

from services import LoanService, UserService
from models import LoanStatusEnum
from .base import View


class LoanHistoryView(View):
    """View that lets administrators search for loan history by user cedula."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app
        self.cedula_input = ft.TextField(
            label="Cédula del usuario",
            hint_text="Ingrese la cédula del usuario",
            width=300,
            border_color=ft.colors.BLUE_400,
        )
        self.search_button = ft.ElevatedButton(
            text="Buscar Historial",
            icon=ft.icons.SEARCH,
            on_click=self.search_history,
        )
        self.results_container = ft.Container(
            content=ft.Text("Ingrese una cédula para buscar el historial", 
                           color=ft.colors.GREY_600, size=16),
            padding=20,
            expand=True,
        )
        self.user_info = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)

    def search_history(self, e):
        """Search for loan history by cedula"""
        cedula = self.cedula_input.value.strip()
        if not cedula:
            self.results_container.content = ft.Text(
                "Por favor ingrese una cédula válida",
                color=ft.colors.RED_400,
                size=16
            )
            self.app.page.update()
            return

        db = self.app.db
        
        # First check if user exists
        user = UserService.get_user_by_cedula(db, cedula)
        if not user:
            self.user_info.value = ""
            self.results_container.content = ft.Text(
                f"No se encontró ningún usuario con la cédula {cedula}",
                color=ft.colors.RED_400,
                size=16
            )
            self.app.page.update()
            return

        # Get loan history
        loans = LoanService.get_loan_history_by_cedula(db, cedula)
        
        # Update user info
        self.user_info.value = f"Usuario: {user.full_name} - Cédula: {user.cedula}"
        
        if not loans:
            self.results_container.content = ft.Text(
                f"El usuario {user.full_name} no tiene historial de préstamos",
                color=ft.colors.GREY_600,
                size=16
            )
        else:
            self.results_container.content = self.build_loan_history_list(loans)
        
        self.app.page.update()

    def build_loan_history_list(self, loans: list) -> ft.Control:
        """Build the loan history list view"""
        loan_cards = []
        
        for loan in loans:
            # Get basic loan info
            bike_code = loan.bike.bike_code if loan.bike else "N/A"
            station_out = f"{loan.station_out.code} - {loan.station_out.name}" if loan.station_out else "N/A"
            station_in = f"{loan.station_in.code} - {loan.station_in.name}" if loan.station_in else "Pendiente"
            
            # Format dates
            time_out_str = loan.time_out.strftime("%d/%m/%Y %H:%M") if loan.time_out else "N/A"
            time_in_str = loan.time_in.strftime("%d/%m/%Y %H:%M") if loan.time_in else "Pendiente"
            
            # Calculate duration if loan is closed
            duration_str = "En curso"
            if loan.time_in and loan.time_out:
                duration = loan.time_in - loan.time_out
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
            
            # Status color and text
            status_colors = {
                LoanStatusEnum.abierto: ft.colors.GREEN,
                LoanStatusEnum.cerrado: ft.colors.BLUE,
                LoanStatusEnum.tardio: ft.colors.ORANGE,
                LoanStatusEnum.perdido: ft.colors.RED,
            }
            
            status_color = status_colors.get(loan.status, ft.colors.GREY)
            status_text = loan.status.value.title()
            
            # Create card for each loan
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.BLUE),
                            ft.Text(f"Bicicleta: {bike_code}", 
                                   weight=ft.FontWeight.BOLD, size=16),
                            ft.Container(expand=True),
                            ft.Container(
                                content=ft.Text(status_text, color=ft.colors.WHITE),
                                bgcolor=status_color,
                                padding=ft.padding.all(8),
                                border_radius=ft.border_radius.all(12),
                            )
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Column([
                                ft.Text("Estación de salida:", weight=ft.FontWeight.BOLD),
                                ft.Text(station_out),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Estación de llegada:", weight=ft.FontWeight.BOLD),
                                ft.Text(station_in),
                            ], expand=True),
                        ]),
                        ft.Row([
                            ft.Column([
                                ft.Text("Fecha de salida:", weight=ft.FontWeight.BOLD),
                                ft.Text(time_out_str),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Fecha de llegada:", weight=ft.FontWeight.BOLD),
                                ft.Text(time_in_str),
                            ], expand=True),
                            ft.Column([
                                ft.Text("Duración:", weight=ft.FontWeight.BOLD),
                                ft.Text(duration_str),
                            ], expand=True),
                        ]),
                    ]),
                    padding=ft.padding.all(16),
                ),
                margin=ft.margin.only(bottom=10),
            )
            loan_cards.append(card)
        
        return ft.Column([
            ft.Text(f"Total de préstamos: {len(loans)}", 
                   weight=ft.FontWeight.BOLD, size=18, color=ft.colors.BLUE_700),
            ft.Divider(),
            ft.Column(
                loan_cards,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            )
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def build(self) -> ft.Control:
        """Build the loan history view"""
        return ft.Column([
            ft.Text(
                "Historial de Préstamos",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_700,
            ),
            ft.Text(
                "Busque el historial de préstamos de cualquier usuario por cédula",
                size=16,
                color=ft.colors.GREY_600,
            ),
            ft.Divider(),
            ft.Row([
                self.cedula_input,
                self.search_button,
            ], alignment=ft.MainAxisAlignment.START),
            ft.Divider(),
            self.user_info,
            self.results_container,
        ], expand=True, scroll=ft.ScrollMode.AUTO) 