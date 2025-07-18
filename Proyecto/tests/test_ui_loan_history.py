import pytest
import flet as ft
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Station, Bicycle, BikeStatusEnum, UserRoleEnum, UserAffiliationEnum
from services import UserService, LoanService
from views.loan_history import LoanHistoryView
import types


class DummyPage:
    def __init__(self):
        self.updated = False

    def update(self):
        self.updated = True

    def scroll_to(self, _):
        pass


@pytest.fixture
def db_session():
    # In-memory SQLite database for testing
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def app(db_session):
    # Minimal app stub for LoanHistoryView
    class App:
        pass

    app = App()
    app.db = db_session
    app.page = DummyPage()
    # No station filter
    app.current_user_station = None
    return app


def create_dummy_data(session, count):
    # Create a station
    station = Station(code="ST01", name="Station 1")
    session.add(station)
    session.commit()
    session.refresh(station)

    # Create a bicycle
    bike = Bicycle(serial_number="SN01", bike_code="BC01", status=BikeStatusEnum.disponible)
    session.add(bike)
    session.commit()
    session.refresh(bike)

    # Create a user
    user = UserService.create_user(
        session,
        cedula="C123456",
        carnet="",
        full_name="Test User",
        email="test@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )

    # Generate loans
    loans = []
    for _ in range(count):
        loan = LoanService.create_loan(
            session,
            user_id=user.id,
            bike_id=bike.id,
            station_out_id=station.id,
        )
        loans.append(loan)
    return loans


def test_initial_pagination(db_session, app):
    # Create 12 loans to span multiple pages (5 per page)
    create_dummy_data(db_session, 12)

    view = LoanHistoryView(app)
    assert view.current_page == 1
    assert view.max_pages == 3

    content = view.results_container.content
    assert isinstance(content, ft.Column)

    slice_list, pagination = content.controls
    assert isinstance(slice_list, ft.Column)
    # First page should contain 5 loan cards
    # The fourth control in slice_list is the inner Column of loan cards
    loan_cards_column = slice_list.controls[3]
    assert isinstance(loan_cards_column, ft.Column)
    assert len(loan_cards_column.controls) == 5

    # Pagination text should reflect page 1 of 3
    page_text = pagination.controls[1]
    assert isinstance(page_text, ft.Text)
    assert page_text.value == "Página 1/3"


def test_navigation(db_session, app):
    # Create 7 loans: should have 2 pages
    create_dummy_data(db_session, 7)

    view = LoanHistoryView(app)

    # Initial state
    content = view.results_container.content
    slice_list, pagination = content.controls
    # First page should contain 5 loan cards
    loan_cards_column = slice_list.controls[3]
    assert isinstance(loan_cards_column, ft.Column)
    assert len(loan_cards_column.controls) == 5
    assert pagination.controls[1].value == "Página 1/2"

    # Navigate to next page
    view.next_page(None)
    assert view.current_page == 2
    content = view.results_container.content
    slice_list, pagination = content.controls
    # Second page should contain remaining 2 loan cards
    loan_cards_column = slice_list.controls[3]
    assert isinstance(loan_cards_column, ft.Column)
    assert len(loan_cards_column.controls) == 2
    assert pagination.controls[1].value == "Página 2/2"

    # Navigate back to previous page
    view.prev_page(None)
    assert view.current_page == 1
    content = view.results_container.content
    _, pagination = content.controls
    assert pagination.controls[1].value == "Página 1/2"


def test_search_no_matches(db_session, app):
    # Create some loans
    create_dummy_data(db_session, 3)

    view = LoanHistoryView(app)
    # Search for a non-existent cedula substring
    view.cedula_input.value = "XYZ"
    view.search_history(None)

    # No loans should match
    assert view.filtered_loans == []

    content = view.results_container.content
    # Should display 'no results' message as a Text control
    assert isinstance(content, ft.Text)
    assert content.value == "No se encontró ningún préstamo para los criterios dados"
    assert view.current_page == 1
    assert view.max_pages == 1


def test_range_header(db_session, app):
    # Create 6 loans: spans 2 pages
    create_dummy_data(db_session, 6)

    view = LoanHistoryView(app)
    content = view.results_container.content
    slice_list, _ = content.controls

    # Header should show total and current range
    text_total = slice_list.controls[0]
    text_range = slice_list.controls[1]
    assert text_total.value == "Total de préstamos: 6"
    assert text_range.value == "Mostrando 1 - 5" 