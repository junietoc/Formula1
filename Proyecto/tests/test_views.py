import pytest
import flet as ft

from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importar vistas
from views.create_user import CreateUserView
from views.availability import AvailabilityView
from views.dashboard import DashboardView
from views.loan import LoanView
from views.return_view import ReturnView
from views.home import HomeView

from unittest.mock import patch


# ---------------------------------------------------------------------------
# Utilidades de prueba
# ---------------------------------------------------------------------------


class DummyPage:
    """Stub mínimo de ft.Page requerido por las vistas para tests."""

    def update(self):
        pass  # no-op

    def window_to_front(self):
        pass  # no-op


class DummyApp:
    """App simplificada que expone sólo los atributos que las vistas usan."""

    def __init__(self, db_session):
        self.db = db_session
        self.page = DummyPage()
        self.nav_rail = ft.NavigationRail()
        self.content_area = ft.Container()
        # Atributos mutados por HomeView
        self.current_user_role = None
        self.current_user_station = None
        self.current_user = None

    # Métodos referenciados por HomeView / DashboardView
    def update_navigation_for_role(self, _role):
        pass

    def show_dashboard_view(self):
        pass


# ---------------------------------------------------------------------------
# Fixture de sesión en memoria (reutiliza logic de test_services)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Pruebas parametrizadas
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "view_cls",
    [
        CreateUserView,
        AvailabilityView,
        DashboardView,
        LoanView,
        ReturnView,
        HomeView,
    ],
)
def test_view_build_returns_control(view_cls, db_session):
    """Cada vista debe construir y devolver un `ft.Control` sin lanzar excepciones."""

    app = DummyApp(db_session)
    control = view_cls(app).build()
    assert isinstance(control, ft.Control), f"{view_cls.__name__} no devolvió ft.Control"


@pytest.fixture
def mock_app():
    class MockNavRail:
        def __init__(self):
            self.destinations = []
            self.selected_index = None
            self.visible = None

    class MockPage:
        def update(self):
            pass

    class MockApp:
        def __init__(self):
            self.nav_rail = MockNavRail()
            self.content_area = type('', (), {'content': None})()
            self.page = MockPage()

    return MockApp()


def test_home_view_instantiation(mock_app):
    with patch('views.dashboard.HomeView') as MockHomeView:
        instance = MockHomeView.return_value
        instance.build.return_value = 'mocked_content'

        dashboard_view = DashboardView(mock_app)
        # Simulate the build process to get the logout button
        column = dashboard_view.build()
        logout_row = column.controls[1]
        logout_btn = logout_row.controls[2]  # Access the logout button

        # Simulate the click event
        logout_btn.on_click(None)

        MockHomeView.assert_called_once_with(mock_app)
        instance.build.assert_called_once()
        assert mock_app.content_area.content == 'mocked_content'
