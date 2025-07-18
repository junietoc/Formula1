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
            on_change=self.search_history,  # Real-time search on each keystroke
            on_submit=self.search_history,  # Trigger search on Enter key press
            suffix=ft.IconButton(
                icon=ft.icons.CLEAR,
                on_click=self.clear_search,
                tooltip="Borrar búsqueda",
            ),
        )
        self.search_button = ft.ElevatedButton(
            text="Buscar Historial",
            icon=ft.icons.SEARCH,
            on_click=self.search_history,
        )
        # Placeholder; we'll update with real data after fetching loans
        self.results_container = ft.Container(padding=20)

        self.user_info = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)

        # ---------------------------------------------------------
        # Pre-load loans for the current admin station (or all)
        # ---------------------------------------------------------
        db = self.app.db
        self.station_code: str | None = getattr(self.app, "current_user_station", None)

        if self.station_code:
            self.all_loans = LoanService.get_loans_by_station_code(db, self.station_code)
        else:
            # Fallback to every loan in the system (e.g., when no station assigned)
            self.all_loans = LoanService.get_all_loans(db)

        # Initialize pagination
        self.filtered_loans = self.all_loans
        self.page_size = 5
        self.current_page = 1
        self.max_pages = max(1, (len(self.filtered_loans) + self.page_size - 1) // self.page_size)

        # Populate initial page of loans
        if self.filtered_loans:
            self.update_results()
        else:
            self.results_container.content = ft.Text(
                "No hay préstamos registrados para este punto", color=ft.colors.GREY_600, size=16
            )

    def search_history(self, e):
        """Search for loan history by cedula"""
        query = self.cedula_input.value.strip()

        if not query:
            # Reset: show all loans
            self.user_info.value = ""
            self.filtered_loans = self.all_loans
        else:
            # Filter loans by cedula substring (case-insensitive)
            self.filtered_loans = [ln for ln in self.all_loans if ln.user and query.lower() in ln.user.cedula.lower()]

            if self.filtered_loans:
                user = self.filtered_loans[0].user
                self.user_info.value = f"Usuario: {user.full_name} - Cédula: {user.cedula}"
            else:
                self.user_info.value = ""

        # Reset to first page and recalculate
        self.current_page = 1
        self.max_pages = max(1, (len(self.filtered_loans) + self.page_size - 1) // self.page_size)

        if not self.filtered_loans:
            self.results_container.content = ft.Text(
                "No se encontró ningún préstamo para los criterios dados",
                color=ft.colors.GREY_600,
                size=16,
            )
            try:
                self.app.page.scroll_to(self.results_container)
            except Exception:
                pass
            self.app.page.update()
        else:
            self.update_results()

    def clear_search(self, e):
        """Clear the search field and show all loans"""
        # Clear input and perform a fresh search (resets pagination)
        self.cedula_input.value = ""
        self.search_history(e)

    def update_results(self):
        """Update results container based on current page and filtered loans"""
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        page_loans = self.filtered_loans[start:end]

        # Build the current page list
        slice_list = self.build_loan_history_list(page_loans)

        # Pagination controls
        pagination = ft.Row([
            ft.IconButton(
                icon=ft.icons.CHEVRON_LEFT,
                disabled=self.current_page == 1,
                on_click=self.prev_page,
            ),
            ft.Text(f"Página {self.current_page}/{self.max_pages}", weight=ft.FontWeight.BOLD),
            ft.IconButton(
                icon=ft.icons.CHEVRON_RIGHT,
                disabled=self.current_page == self.max_pages,
                on_click=self.next_page,
            ),
        ], alignment=ft.MainAxisAlignment.CENTER)

        # Combine list and controls
        self.results_container.content = ft.Column([slice_list, pagination], spacing=10)

        # Scroll to top of results
        try:
            self.app.page.scroll_to(self.results_container)
        except Exception:
            pass

        self.app.page.update()

    def prev_page(self, e):
        """Go to previous page of results"""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_results()

    def next_page(self, e):
        """Go to next page of results"""
        if self.current_page < self.max_pages:
            self.current_page += 1
            self.update_results()

    def build_loan_history_list(self, loans: list) -> ft.Control:
        """Build the loan history list view"""
        loan_cards: list[ft.Control] = []

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
            
            # Get user info
            user_name = loan.user.full_name if loan.user else "N/A"
            user_cedula = loan.user.cedula if loan.user else "N/A"
            
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
                        ft.Row([
                            ft.Text(f"Usuario: {user_name} - Cédula: {user_cedula}", 
                                   weight=ft.FontWeight.BOLD, size=14),
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
        
        # Calculate pagination header values
        start = (self.current_page - 1) * self.page_size + 1
        end = start + len(loans) - 1
        total = len(self.filtered_loans)

        return ft.Column(
            [
                ft.Text(
                    f"Total de préstamos: {total}",
                    weight=ft.FontWeight.BOLD,
                    size=18,
                    color=ft.colors.BLUE_700,
                ),
                ft.Text(
                    f"Mostrando {start} - {end}",
                    size=16,
                    color=ft.colors.GREY_600,
                ),
                ft.Divider(),
                ft.Column(loan_cards, spacing=10),
            ],
            spacing=10,
        )

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