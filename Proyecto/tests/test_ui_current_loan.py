import types
import pytest
import flet as ft
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

import database  # to override SessionLocal if needed
from models import (
    Base,
    Station,
    Bicycle,
    BikeStatusEnum,
    UserRoleEnum,
    UserAffiliationEnum,
    LoanStatusEnum,
)
from services import UserService, LoanService
from views.current_loan import CurrentLoanView


class DummyPage:  # Minimal stub to satisfy view
    def update(self):
        pass


@pytest.fixture
def db_session():
    """Provide an isolated in-memory DB session for each test"""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    # Replace global SessionLocal used by database module (if referenced)
    database.SessionLocal = SessionLocal  # type: ignore
    yield session
    session.close()


@pytest.fixture
def dummy_app(db_session):
    """Return a minimal app object with the bits CurrentLoanView expects."""

    class _App:
        pass

    app = _App()
    app.db = db_session
    app.page = DummyPage()
    return app


def _create_common_entities(session):
    """Create a station and bike helper."""
    station = Station(code="ST01", name="Estacion 1")
    bike = Bicycle(serial_number="SN01", bike_code="BK01", status=BikeStatusEnum.disponible)
    session.add_all([station, bike])
    session.commit()
    session.refresh(station)
    session.refresh(bike)
    return station, bike


def _create_user(session):
    return UserService.create_user(
        session,
        cedula="123456",
        carnet="",
        full_name="Usuario Prueba",
        email="user@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )


def test_no_loans_shows_message(dummy_app):
    """If user has no loans, the view should show the empty message."""
    session = dummy_app.db
    user = _create_user(session)
    dummy_app.current_user = user

    view = CurrentLoanView(dummy_app)
    content = view.build()

    assert isinstance(content, ft.Column)
    # Expect the first Text control to show the empty-state headline
    # The inner icon + texts are inside the Column when no loans
    assert any(
        isinstance(ctrl, ft.Text) and ctrl.value == "No tienes préstamos registrados"
        for ctrl in content.controls
    )


def test_only_open_loan_sections(dummy_app):
    """With one open loan, should get 'Préstamo Actual' section and a 'no past loans' message."""
    session = dummy_app.db
    station, bike = _create_common_entities(session)
    user = _create_user(session)
    dummy_app.current_user = user

    # Create one open loan
    LoanService.create_loan(session, user.id, bike.id, station.id)

    view = CurrentLoanView(dummy_app)
    root = view.build()

    # Expect headers
    headers = [ctrl.value for ctrl in root.controls if isinstance(ctrl, ft.Text)]
    assert "Préstamo Actual" in headers
    assert "Préstamos Pasados" in headers

    # Helper: collect all Text controls recursively
    def collect_texts(ctrl):
        texts = []
        if isinstance(ctrl, ft.Text):
            texts.append(ctrl)
        # Drill into common containers
        if hasattr(ctrl, "controls"):
            for c in ctrl.controls:
                texts.extend(collect_texts(c))
        if hasattr(ctrl, "content") and ctrl.content is not None:
            texts.extend(collect_texts(ctrl.content))
        return texts

    all_texts = collect_texts(root)

    # Expect message about no past loans somewhere in the tree
    assert any(txt.value == "No hay préstamos pasados" for txt in all_texts)

    # There should be at least one Card (current loan)
    assert any(isinstance(ctrl, ft.Card) for ctrl in root.controls)


def test_open_and_past_loans(dummy_app):
    """When user has open and closed loans, both sections list cards appropriately."""
    session = dummy_app.db
    station, bike = _create_common_entities(session)
    user = _create_user(session)
    dummy_app.current_user = user

    # Open loan
    LoanService.create_loan(session, user.id, bike.id, station.id)

    # Past loan (create + return)
    loan_closed = LoanService.create_loan(session, user.id, bike.id, station.id)
    # Fast-forward: mark as returned 30 minutes later
    station2 = Station(code="ST02", name="Estacion 2")
    session.add(station2)
    session.commit()
    session.refresh(station2)

    # Return the loan now to close it
    LoanService.return_loan(session, loan_closed.id, station2.id)

    view = CurrentLoanView(dummy_app)
    root = view.build()

    # Collect all Card controls in the root tree (helper)
    def collect_cards(ctrl):
        cards = []
        if isinstance(ctrl, ft.Card):
            cards.append(ctrl)
        if hasattr(ctrl, "controls"):
            for c in ctrl.controls:
                cards.extend(collect_cards(c))
        if hasattr(ctrl, "content") and ctrl.content is not None:
            cards.extend(collect_cards(ctrl.content))
        return cards

    all_cards = collect_cards(root)
    # Expect two cards: one open, one closed
    assert len(all_cards) == 2

    # Past loans section should not display the 'no past loans' message
    def collect_texts(ctrl):
        texts = []
        if isinstance(ctrl, ft.Text):
            texts.append(ctrl)
        if hasattr(ctrl, "controls"):
            for c in ctrl.controls:
                texts.extend(collect_texts(c))
        if hasattr(ctrl, "content") and ctrl.content is not None:
            texts.extend(collect_texts(ctrl.content))
        return texts

    all_texts = collect_texts(root)

    assert all(txt.value != "No hay préstamos pasados" for txt in all_texts) 