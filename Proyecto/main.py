import flet as ft
# ----------------------------------------------------
# Integración opcional con *flet-material*             
# ----------------------------------------------------
try:
    import flet_material as fm  # type: ignore

    # Configurar un tema Material moderno
    fm.Theme.set_theme(theme="blue")
except ModuleNotFoundError:  # Entorno sin flet-material (p.ej. CI)
    class _FMStub:  # noqa: D101
        class Theme:  # noqa: D101
            bgcolor = None

            @staticmethod
            def set_theme(*args, **kwargs):  # noqa: D401,D401
                pass

        class Buttons(ft.ElevatedButton):  # noqa: D101
            def __init__(self, *_, title: str = "", **kw):
                super().__init__(title or kw.pop("text", ""), **kw)

    fm = _FMStub()  # type: ignore

from database import get_db, create_tables
from services import UserService, BicycleService, StationService, LoanService
from models import (
    User,
    Bicycle,
    Station,
    Loan,
    UserRoleEnum,
    UserAffiliationEnum,
    BikeStatusEnum,
    LoanStatusEnum,
)
import uuid
from views.create_user import CreateUserView
from views.availability import AvailabilityView
from views.home import HomeView
from views.dashboard import DashboardView
from views.loan import LoanView
# Added view to display current open loan for regular users
from views.return_view import ReturnView
from views.current_loan import CurrentLoanView
from views.loan_history import LoanHistoryView
from typing import Callable, Dict

# noqa: F401 needed for typing
from views.base import View
from sample_data import populate_sample_data


class VeciRunApp:
    def __init__(self):
        self.db = next(get_db())
        self.current_user = None

    def main(self, page: ft.Page):
        self.page = page  # Store page reference
        page.title = "VeciRun"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.window_maximized = True
        page.window_resizable = True
        page.padding = 20

        # Set application window icon (supported on newer Flet desktop builds)
        try:
            if hasattr(page, "window") and hasattr(page.window, "icon"):
                page.window.icon = "vecirunlogo.png"
        except Exception:
            # Gracefully skip if the current platform or Flet version does not support it
            pass

        # Aplicar color de fondo del tema Material si existe
        if getattr(fm.Theme, "bgcolor", None):
            page.bgcolor = fm.Theme.bgcolor

        # Initialize database
        create_tables()

        # Create sample data if empty
        self.create_sample_data()

        # Main navigation (will be updated based on role)
        self.nav_rail = ft.NavigationRail(
            selected_index=0,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=100,
            min_extended_width=200,
            destinations=[],
            on_change=self.nav_change,
        )

        # Content area
        self.content_area = ft.Container(
            content=ft.Text("Seleccione una opción del menú", size=20), expand=True, padding=20
        )

        # Layout
        self.main_row = ft.Row(
            [
                self.nav_rail,
                ft.VerticalDivider(width=1),
                self.content_area,
            ],
            expand=True,
        )
        page.add(self.main_row)

        # Initially hide the navigation rail
        self.nav_rail.visible = False

        # Show initial view
        self.content_area.content = HomeView(self).build()
        page.update()

        # Initialize role-based navigation
        self.update_navigation_for_role("regular")

    def nav_change(self, e: ft.ControlEvent):
        # Manejo centralizado usando self.view_registry
        index = e.control.selected_index
        view_factory = self.view_registry.get(index)
        if view_factory is None:
            return  # índice sin vista

        self.content_area.content = view_factory().build()
        self.page.update()

    # show_home_view eliminado: la lógica se trasladó a HomeView

    def show_dashboard_view(self):
        """Wrapper para mostrar DashboardView (mantiene API pública)."""
        self.content_area.content = DashboardView(self).build()
        self.page.update()

    def update_navigation_for_role(self, role):
        """Update navigation based on user role"""
        # Diccionario índice -> factory de vista
        self.view_registry: Dict[int, Callable[[], View]] = {}

        destinations = [
            ft.NavigationRailDestination(
                icon=ft.icons.HOME, selected_icon=ft.icons.HOME, label="Inicio"
            )
        ]
        self.view_registry[0] = lambda: DashboardView(self)

        if role == "admin":
            destinations += [
                ft.NavigationRailDestination(
                    icon=ft.icons.PERSON_ADD, selected_icon=ft.icons.PERSON_ADD, label="Usuarios"
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.DIRECTIONS_BIKE,
                    selected_icon=ft.icons.DIRECTIONS_BIKE,
                    label="Préstamo",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.ASSIGNMENT_RETURN,
                    selected_icon=ft.icons.ASSIGNMENT_RETURN,
                    label="Devolución",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.HISTORY,
                    selected_icon=ft.icons.HISTORY,
                    label="Historial",
                ),
            ]
            self.view_registry[1] = lambda: CreateUserView(self)
            self.view_registry[2] = lambda: LoanView(self)
            self.view_registry[3] = lambda: ReturnView(self)
            self.view_registry[4] = lambda: LoanHistoryView(self)
        else:  # regular
            destinations += [
                ft.NavigationRailDestination(
                    icon=ft.icons.LOCATION_ON,
                    selected_icon=ft.icons.LOCATION_ON,
                    label="Disponibilidad",
                ),
                ft.NavigationRailDestination(
                    icon=ft.icons.DIRECTIONS_BIKE,
                    selected_icon=ft.icons.DIRECTIONS_BIKE,
                    label="Mi Préstamo",
                ),
            ]

            # Índices coherentes con las posiciones de *destinations*
            self.view_registry[1] = lambda: AvailabilityView(self)
            self.view_registry[2] = lambda: CurrentLoanView(self)

        self.nav_rail.destinations = destinations
        self.page.update()

    def show_loan_view(self):  # Obsoletos: delegan a LoanView
        self.content_area.content = LoanView(self).build()
        self.page.update()

    def refresh_loan_view(self, page: ft.Page):
        """Re-render the **LoanView** in isolation.

        This helper is mainly used by unit tests that need to exercise the
        *register_loan* callback without running a full Flet application. The
        implementation therefore has to work even when `page` is a lightweight
        stub (see *tests/test_ui_loan.py*).
        """
        # Store the page reference (test may pass a stub)
        self.page = page  # type: ignore

        # Ensure *content_area* exists – tests inject a stub if running outside
        # a real Flet UI.
        if not hasattr(self, "content_area"):
            self.content_area = ft.Container()

        # Build a fresh LoanView and assign it so that the stubbed
        # ``ft.ElevatedButton`` inside the view is instantiated, allowing the
        # test to grab its callback.
        self.content_area.content = LoanView(self).build()

        # Call update() on the provided page object if available.
        if hasattr(page, "update") and callable(getattr(page, "update")):
            page.update()

    def show_return_view(self):
        self.content_area.content = ReturnView(self).build()
        self.page.update()

    def clear_user_state(self):
        """Clear user-specific state when switching users"""
        # Clear any user-specific attributes
        if hasattr(self, 'current_user_station'):
            delattr(self, 'current_user_station')
        
        # Clear current user and role
        self.current_user = None
        if hasattr(self, 'current_user_role'):
            delattr(self, 'current_user_role')
        
        # Reset navigation to home only if nav_rail exists
        if hasattr(self, 'nav_rail') and self.nav_rail:
            self.nav_rail.selected_index = 0
            if hasattr(self, 'content_area') and self.content_area:
                self.content_area.content = DashboardView(self).build()
                if hasattr(self, 'page') and self.page:
                    self.page.update()

    def create_sample_data(self):
        """Create sample data for testing"""
        populate_sample_data(self.db)


if __name__ == "__main__":
    app = VeciRunApp()
    ft.app(target=app.main)
