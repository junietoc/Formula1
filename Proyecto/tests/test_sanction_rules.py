import pytest
import flet as ft
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

from models import (
    Base,
    User,
    Station,
    Bicycle,
    BikeStatusEnum,
    UserAffiliationEnum,
    UserRoleEnum,
    Sanction,
    SanctionStatusEnum,
    ReturnReport,
    LoanStatusEnum,
)

from services import UserService, StationService, BicycleService, LoanService
from views.return_report_view import ReturnReportView

# ---------------------------------------------------------------------------
# Helper stubs & utilities
# ---------------------------------------------------------------------------

# Stub ElevatedButton to avoid Flet runtime requirements in headless tests
class _DummyElevatedButton:  # noqa: D101
    last_callback = None

    def __init__(self, *_, on_click=None, **__):  # noqa: D401
        self.on_click = on_click
        _DummyElevatedButton.last_callback = on_click

# Patch once imported
ft.ElevatedButton = _DummyElevatedButton  # type: ignore


def _create_station(db, code: str) -> Station:  # noqa: D401
    st = Station(code=code, name=f"Estación {code}")
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def _create_bike(db, serial: str, code: str, station: Station | None = None) -> Bicycle:  # noqa: D401
    bike = Bicycle(serial_number=serial, bike_code=code, status=BikeStatusEnum.disponible)
    if station:
        bike.current_station_id = station.id
    db.add(bike)
    db.commit()
    db.refresh(bike)
    return bike


class _DummyPage:  # noqa: D101
    def update(self):
        pass

    def window_to_front(self):
        pass


class _DummyApp:  # noqa: D101
    def __init__(self, db_session):
        self.db = db_session
        self.page = _DummyPage()
        self.content_area = type("_", (), {"content": None})()
        # atributos de estado que usan las vistas
        self.current_user_role = None
        self.current_user_station = None
        self.current_user = None

    def clear_user_state(self):
        pass


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


# ---------------------------------------------------------------------------
# Tests – Loan sanction restrictions
# ---------------------------------------------------------------------------

def test_create_loan_fails_when_user_has_active_sanction(db_session):  # noqa: D401
    """LoanService.create_loan debe lanzar ValueError si el usuario tiene una sanción activa."""

    # Crear datos mínimos
    user = UserService.create_user(
        db_session,
        cedula="1111",
        carnet="",
        full_name="Usuario Sancionado",
        email="u@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )

    station = _create_station(db_session, "EST001")
    bike = _create_bike(db_session, "SER1", "B001")

    # Crear sanción activa: hoy dentro del rango
    now = datetime.utcnow()
    sanction = Sanction(
        user_id=user.id,
        incident_id=None,  # Para pruebas no necesitamos incidente real
        operator_id=None,
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=2),
        status=SanctionStatusEnum.activa,
    )
    db_session.add(sanction)
    db_session.commit()

    # Intentar crear préstamo
    with pytest.raises(ValueError):
        LoanService.create_loan(
            db_session,
            user_id=user.id,
            bike_id=bike.id,
            station_out_id=station.id,
            station_in_id=station.id,
        )


def test_create_loan_when_sanction_expired_is_allowed(db_session):  # noqa: D401
    """Si la sanción está expirada (fecha fin pasada), debe permitir el préstamo."""
    user = UserService.create_user(
        db_session,
        cedula="2222",
        carnet="",
        full_name="Usuario Libre",
        email="x@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )

    station = _create_station(db_session, "EST002")
    bike = _create_bike(db_session, "SER2", "B002")

    past_sanction = Sanction(
        user_id=user.id,
        incident_id=None,
        operator_id=None,
        start_at=datetime.utcnow() - timedelta(days=10),
        end_at=datetime.utcnow() - timedelta(days=5),
        status=SanctionStatusEnum.expirada,
    )
    db_session.add(past_sanction)
    db_session.commit()

    # No debería lanzar excepción
    loan = LoanService.create_loan(
        db_session,
        user_id=user.id,
        bike_id=bike.id,
        station_out_id=station.id,
        station_in_id=station.id,
    )
    assert loan.status == LoanStatusEnum.abierto


# ---------------------------------------------------------------------------
# Tests – ReturnReportView filtrado por estación
# ---------------------------------------------------------------------------

def _count_cards(ctrl):  # noqa: D401
    import flet as _ft
    cards = []
    if isinstance(ctrl, _ft.Card):
        cards.append(ctrl)
    for attr in ("controls", "content"):
        if hasattr(ctrl, attr):
            child = getattr(ctrl, attr)
            if child is None:
                continue
            if isinstance(child, list):
                for c in child:
                    cards.extend(_count_cards(c))
                
            else:
                cards.extend(_count_cards(child))
    return cards


def test_return_report_view_filters_by_admin_station(db_session):  # noqa: D401
    """El administrador sólo debe ver reportes asociados a su estación."""

    # Preparar datos
    station1 = _create_station(db_session, "EST001")
    station2 = _create_station(db_session, "EST002")

    bike1 = _create_bike(db_session, "SER10", "B010")
    bike2 = _create_bike(db_session, "SER20", "B020")

    # Crear usuario y préstamos con reportes
    user = UserService.create_user(
        db_session,
        cedula="3333",
        carnet="",
        full_name="User Report",
        email="r@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )

    # Loan associated to station1 (out)
    loan1 = LoanService.create_loan(
        db_session,
        user_id=user.id,
        bike_id=bike1.id,
        station_out_id=station1.id,
        station_in_id=station2.id,
    )

    # Loan associated to station2 (out) – should be hidden for admin of station1
    loan2 = LoanService.create_loan(
        db_session,
        user_id=user.id,
        bike_id=bike2.id,
        station_out_id=station2.id,
        station_in_id=station2.id,
    )

    # Crear reportes de devolución básicos
    rr1 = ReturnReport(loan_id=loan1.id, total_incident_days=0, created_by=user.id)
    rr2 = ReturnReport(loan_id=loan2.id, total_incident_days=0, created_by=user.id)
    db_session.add_all([rr1, rr2])
    db_session.commit()

    # Configurar app como admin de station1
    app = _DummyApp(db_session)
    app.current_user_role = "admin"
    app.current_user_station = "EST001"

    view = ReturnReportView(app)
    control = view.build()

    cards = _count_cards(control)

    assert len(cards) == 1, "El administrador debe ver sólo los reportes de su estación" 