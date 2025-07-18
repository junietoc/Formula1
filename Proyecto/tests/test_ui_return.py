import importlib
import types

import flet as ft
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base,
    Station,
    Bicycle,
    User,
    Loan,
    UserRoleEnum,
    UserAffiliationEnum,
    BikeStatusEnum,
    LoanStatusEnum,
)

# ---------------------------------------------------------------------------
# Lightweight stub to capture the *on_click* callback of ft.ElevatedButton
# ---------------------------------------------------------------------------


class _DummyButton:  # pragma: no cover – helpers only
    """Replacement for *ft.ElevatedButton* that stores the callback provided."""

    last_callback = None  # type: ignore

    def __init__(self, *args, on_click=None, **kwargs):  # noqa: D401
        self.on_click = on_click
        _DummyButton.last_callback = on_click


# ---------------------------------------------------------------------------
# Import the module and patch its *ft.ElevatedButton* BEFORE using ReturnView
# ---------------------------------------------------------------------------

rv_module = importlib.import_module("views.return_view")
# Patch ft.ElevatedButton to capture callbacks
original_elevated_button = ft.ElevatedButton
ft.ElevatedButton = _DummyButton  # type: ignore
ReturnView = rv_module.ReturnView  # convenience alias

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


class DummyPage:  # pragma: no cover – helpers only
    def update(self):
        pass


class DummyApp:  # pragma: no cover – helpers only
    """Minimal application object exposing only what *ReturnView* needs."""

    def __init__(self, db_session, station_code: str):
        self.db = db_session
        self.page = DummyPage()
        self.content_area = types.SimpleNamespace(content=None)
        self.current_user_station = station_code

    # Called by the callback inside ReturnView
    def show_return_view(self):
        pass  # no-op for unit tests


# ---------------------------------------------------------------------------
# Fixtures
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


@pytest.fixture(scope="function")
def setup_station(db_session):
    """Create and return a sample station used by the tests."""
    station = Station(code="EST001", name="Calle 26")
    db_session.add(station)
    db_session.commit()
    return station


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_return_view_shows_message_when_no_loans(db_session, setup_station):
    """If no open loans exist for the admin's station, the view must show an informative message."""

    app = DummyApp(db_session, station_code="EST001")

    control = ReturnView(app).build()
    assert isinstance(control, ft.Column)

    # Expect a Text control that contains the no-pending-loans message
    messages = [c for c in control.controls if isinstance(c, ft.Text)]
    assert any("No hay devoluciones pendientes" in m.value for m in messages)


def test_return_view_registers_loan_return(db_session, setup_station):
    """Pressing the *Registrar devolución* button should close the loan without errors."""

    # -----------------------
    # Arrange – build dataset
    # -----------------------
    station = setup_station

    # User & bike
    user = User(
        cedula="99999999",
        carnet="USER_99999999",
        full_name="Usuario Prueba",
        email="prueba@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )
    bike = Bicycle(
        serial_number="SN123",
        bike_code="B001",
        status=BikeStatusEnum.prestada,
        current_station_id=None,
    )
    db_session.add_all([user, bike])
    db_session.commit()

    # Open loan expected to be returned in station EST001
    loan = Loan(
        user_id=user.id,
        bike_id=bike.id,
        station_out_id=station.id,  # salida desde misma estación para simplicidad
        station_in_id=station.id,
        status=LoanStatusEnum.abierto,
    )
    db_session.add(loan)
    db_session.commit()

    # -----------------------
    # Act – build view & simulate click
    # -----------------------
    app = DummyApp(db_session, station_code="EST001")

    # Reset last_callback tracker to avoid contamination from previous tests
    _DummyButton.last_callback = None

    ReturnView(app).build()

    callback = _DummyButton.last_callback
    assert callable(callback), "No se capturó el callback del botón"

    # Execute the callback (simulate button click)
    callback(None)

    # -----------------------
    # Assert – loan is now closed
    # -----------------------
    updated_loan = db_session.query(Loan).filter(Loan.id == loan.id).first()
    assert updated_loan.status == LoanStatusEnum.cerrado, "El préstamo no se cerró correctamente"
    assert updated_loan.time_in is not None, "La hora de devolución no fue registrada" 