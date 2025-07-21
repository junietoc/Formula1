import flet as ft
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

import database  # Ensures the global SessionLocal can be overridden if needed
from models import (
    Base,
    Sanction,
    SanctionStatusEnum,
    UserAffiliationEnum,
    UserRoleEnum,
)
from services import UserService, LoanService, IncidentService
from views.dashboard import DashboardView
from views.current_loan import CurrentLoanView
from models import (
    Station,
    Bicycle,
    BikeStatusEnum,
    IncidentSeverityEnum,
    IncidentTypeEnum,
)


# ---------------------------------------------------------------------------
# Dummy app & page stubs (minimal attributes used by *DashboardView*)
# ---------------------------------------------------------------------------

class _DummyPage:  # noqa: D101 – simple stub
    def update(self):  # noqa: D401
        pass


class _DummyApp:  # noqa: D101 – exposes just what the view needs
    def __init__(self, db_session):  # noqa: D401
        self.db = db_session
        self.page = _DummyPage()
        self.nav_rail = ft.NavigationRail()
        self.content_area = ft.Container()
        # State mutated by other parts of the UI
        self.current_user_role = None
        self.current_user_station = None
        self.current_user = None

    # The view calls this method on logout – keep it as a no-op here
    def clear_user_state(self):  # noqa: D401
        pass


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session():  # noqa: D401
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    # Replace *SessionLocal* in the *database* module so the app uses this same session
    database.SessionLocal = SessionLocal  # type: ignore
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def app(db_session):  # noqa: D401
    return _DummyApp(db_session)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_regular_user(session):  # noqa: D401
    """Persist a standard regular user and return it."""
    return UserService.create_user(
        session,
        cedula="1001",
        carnet="",
        full_name="Usuario Regular",
        email="user@tests.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )


def _traverse_controls(control):  # noqa: D401
    """Recursively yield all controls inside *control* (DFS)."""
    yield control
    # Common attributes that may hold children
    for attr in ("controls", "content"):
        child = getattr(control, attr, None)
        if child is None:
            continue
        # If the attribute itself is a list of controls
        if isinstance(child, list):
            for c in child:
                yield from _traverse_controls(c)
        else:
            # Single nested control
            yield from _traverse_controls(child)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_dashboard_shows_active_sanction_banner(app, db_session):  # noqa: D401
    """When the logged-in user has an *active* sanction, a banner must appear."""

    user = _create_regular_user(db_session)
    app.current_user = user  # Simulate logged-in user

    now = datetime.now(timezone.utc)
    sanction = Sanction(
        user_id=user.id,
        start_at=now - timedelta(hours=1),
        end_at=now + timedelta(hours=2),
        status=SanctionStatusEnum.activa,
    )
    db_session.add(sanction)
    db_session.commit()

    root = DashboardView(app).build()

    # Collect all Text controls and look for the banner message
    texts = [ctrl for ctrl in _traverse_controls(root) if isinstance(ctrl, ft.Text)]
    assert any("sanción activa" in (txt.value or "").lower() for txt in texts), (
        "El banner de sanción no se mostró para una sanción activa"
    )


def test_dashboard_hides_banner_when_no_active_sanction(app, db_session):  # noqa: D401
    """If the user has *no active* sanction, the banner must NOT appear."""

    user = _create_regular_user(db_session)
    app.current_user = user

    # Optional: insert an expired sanction to ensure filtering works
    now = datetime.now(timezone.utc)
    past_sanction = Sanction(
        user_id=user.id,
        start_at=now - timedelta(days=5),
        end_at=now - timedelta(days=3),
        status=SanctionStatusEnum.expirada,
    )
    db_session.add(past_sanction)
    db_session.commit()

    root = DashboardView(app).build()

    texts = [ctrl for ctrl in _traverse_controls(root) if isinstance(ctrl, ft.Text)]
    assert all("sanción activa" not in (txt.value or "").lower() for txt in texts), (
        "Se mostró un banner de sanción a pesar de no tener sanciones activas"
    ) 


# ---------------------------------------------------------------------------
# Extra helpers for *CurrentLoanView* dialog tests
# ---------------------------------------------------------------------------


def _create_station_and_bike(session):  # noqa: D401
    """Persist a station plus one available bicycle and return both."""
    station = Station(code="ST01", name="Estación 1")
    bike = Bicycle(serial_number="SN01", bike_code="BK01", status=BikeStatusEnum.disponible)
    session.add_all([station, bike])
    session.commit()
    session.refresh(station)
    session.refresh(bike)
    return station, bike


# ---------------------------------------------------------------------------
# Dialog-related tests
# ---------------------------------------------------------------------------


def test_incident_dialog_shows_sanction_details(app, db_session):  # noqa: D401
    """The incidents dialog should list sanction details when present."""

    # Setup entities
    user = _create_regular_user(db_session)
    app.current_user = user
    station, bike = _create_station_and_bike(db_session)

    loan = LoanService.create_loan(db_session, user.id, bike.id, station.id)

    # Create an incident and an associated sanction
    incident = IncidentService.create_incident(
        db_session,
        loan_id=loan.id,
        bike_id=bike.id,
        reporter_id=user.id,
        incident_type=IncidentTypeEnum.accidente,
        severity=IncidentSeverityEnum.media,
        description="Incidente de prueba",
    )

    now = datetime.now(timezone.utc)
    sanction = Sanction(
        user_id=user.id,
        incident_id=incident.id,
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=1),
        status=SanctionStatusEnum.activa,
    )
    db_session.add(sanction)
    db_session.commit()

    # Build view and invoke the private dialog helper
    view = CurrentLoanView(app)
    view.build()  # Ensure internal state/dummy build done
    view._show_incidents_dialog(loan)  # type: ignore – private method access for test

    dlg = app.page.dialog
    assert dlg.open is True, "El diálogo no se abrió tras invocar _show_incidents_dialog"

    # Inspect texts inside the dialog for sanction status
    texts = [ctrl for ctrl in _traverse_controls(dlg) if isinstance(ctrl, ft.Text)]
    assert any(sanction.status.value in (txt.value or "") for txt in texts), (
        "El estado de la sanción no aparece en el diálogo de incidentes"
    )


def test_incident_dialog_handles_no_sanction(app, db_session):  # noqa: D401
    """If an incident has no sanction, the dialog should show an informative message."""

    user = _create_regular_user(db_session)
    app.current_user = user
    station, bike = _create_station_and_bike(db_session)

    loan = LoanService.create_loan(db_session, user.id, bike.id, station.id)

    IncidentService.create_incident(
        db_session,
        loan_id=loan.id,
        bike_id=bike.id,
        reporter_id=user.id,
        incident_type=IncidentTypeEnum.uso_indebido,
        severity=IncidentSeverityEnum.leve,
        description="Incidente sin sanción",
    )

    view = CurrentLoanView(app)
    view.build()
    view._show_incidents_dialog(loan)  # type: ignore

    dlg = app.page.dialog
    assert dlg.open is True

    texts = [ctrl for ctrl in _traverse_controls(dlg) if isinstance(ctrl, ft.Text)]
    assert any("sin sanción asociada" in (txt.value or "").lower() for txt in texts), (
        "El diálogo no indicó la ausencia de sanción cuando debía"
    ) 