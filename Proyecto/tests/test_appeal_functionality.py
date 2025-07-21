import flet as ft
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, timezone

import database  # Ensures global SessionLocal can be patched
from models import (
    Base,
    Sanction,
    SanctionStatusEnum,
    UserAffiliationEnum,
    UserRoleEnum,
    Incident,
    IncidentSeverityEnum,
    IncidentTypeEnum,
)
from services import UserService, LoanService, IncidentService
from views.current_loan import CurrentLoanView
from views.dashboard import DashboardView


# -------------------------------------------------------------
# Dummy stubs used by the UI views (copied from other test file)
# -------------------------------------------------------------

class _DummyPage:  # noqa: D101 – minimal stub
    def update(self):  # noqa: D401
        pass

    # SnackBar attribute can be set by the code under test
    snack_bar = None


class _DummyApp:  # noqa: D101
    def __init__(self, db_session):  # noqa: D401
        self.db = db_session
        self.page = _DummyPage()
        self.nav_rail = ft.NavigationRail()
        self.content_area = ft.Container()
        # UI state managed from outside
        self.current_user_role: str | None = None
        self.current_user_station: str | None = None
        self.current_user = None

    def clear_user_state(self):  # noqa: D401
        pass


# -------------------------------------------------------------
# Pytest fixtures
# -------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session():  # noqa: D401
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    # Patch *database* module to reuse this session
    database.SessionLocal = SessionLocal  # type: ignore
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def app(db_session):  # noqa: D401
    return _DummyApp(db_session)


# -------------------------------------------------------------
# Helpers
# -------------------------------------------------------------


def _traverse_controls(control):  # noqa: D401
    """Depth-first traversal generator for all nested controls."""
    yield control
    for attr in ("controls", "content"):
        child = getattr(control, attr, None)
        if child is None:
            continue
        if isinstance(child, list):
            for c in child:
                yield from _traverse_controls(c)
        else:
            yield from _traverse_controls(child)


def _create_user(session, *, cedula: str, role: UserRoleEnum):  # noqa: D401
    return UserService.create_user(
        session,
        cedula=cedula,
        carnet="",
        full_name="Usuario " + cedula,
        email=f"{cedula}@tests.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=role,
    )


# -------------------------------------------------------------
# Tests
# -------------------------------------------------------------


def test_cannot_appeal_twice_button_hidden(app, db_session):  # noqa: D401
    """Si la sanción ya posee *appeal_text*, el botón de apelación no debe mostrarse."""

    # Preparar datos
    user = _create_user(db_session, cedula="2001", role=UserRoleEnum.usuario)
    app.current_user = user

    # Se necesita prestar una bici para crear incidente
    station = None
    bike = None
    # Crear entidades mínimas para préstamo
    from models import Station, Bicycle, BikeStatusEnum

    station = Station(code="ST01", name="Estación 1")
    bike = Bicycle(serial_number="SN01", bike_code="BK01", status=BikeStatusEnum.disponible)
    db_session.add_all([station, bike])
    db_session.commit()
    db_session.refresh(station)
    db_session.refresh(bike)

    loan = LoanService.create_loan(db_session, user.id, bike.id, station.id)

    incident = IncidentService.create_incident(
        db_session,
        loan_id=loan.id,
        bike_id=bike.id,
        reporter_id=user.id,
        incident_type=IncidentTypeEnum.accidente,
        severity=IncidentSeverityEnum.leve,
        description="Prueba de incidente",
    )

    # Crear sanción ya apelada (rechazada o pendiente de respuesta)
    sanction = Sanction(
        user_id=user.id,
        incident_id=incident.id,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(days=2),
        status=SanctionStatusEnum.activa,  # sigue activa porque fue rechazada
        appeal_text="Motivo de prueba",
        appeal_response="",  # aún sin respuesta
    )
    db_session.add(sanction)
    db_session.commit()

    # Construir vista y abrir diálogo
    view = CurrentLoanView(app)
    view.build()
    view._show_incidents_dialog(loan)  # type: ignore – acceso a método privado

    dlg = app.page.dialog
    assert dlg.open is True

    # Recolectar botones elevados dentro del diálogo
    buttons = [c for c in _traverse_controls(dlg) if isinstance(c, ft.ElevatedButton)]
    assert all((btn.text or "") != "Apelar Sanción" for btn in buttons), (
        "Se mostró el botón de Apelar a pesar de que ya existía una apelación"
    )


def test_dialog_shows_rejected_and_accepted_labels(app, db_session):  # noqa: D401
    """El diálogo de incidentes debe mostrar 'Apelación rechazada' o 'Apelación aceptada'."""

    from models import Station, Bicycle, BikeStatusEnum

    user = _create_user(db_session, cedula="2002", role=UserRoleEnum.usuario)
    app.current_user = user

    station = Station(code="ST02", name="Estación 2")
    bike = Bicycle(serial_number="SN02", bike_code="BK02", status=BikeStatusEnum.disponible)
    db_session.add_all([station, bike])
    db_session.commit()

    loan = LoanService.create_loan(db_session, user.id, bike.id, station.id)

    # Crear incidente y dos sanciones, una rechazada, otra aceptada.
    incident_rej = IncidentService.create_incident(
        db_session,
        loan_id=loan.id,
        bike_id=bike.id,
        reporter_id=user.id,
        incident_type=IncidentTypeEnum.uso_indebido,
        severity=IncidentSeverityEnum.leve,
        description="Incidente 1",
    )

    incident_acc = IncidentService.create_incident(
        db_session,
        loan_id=loan.id,
        bike_id=bike.id,
        reporter_id=user.id,
        incident_type=IncidentTypeEnum.accidente,
        severity=IncidentSeverityEnum.media,
        description="Incidente 2",
    )

    now = datetime.now(timezone.utc)
    sanction_rej = Sanction(
        user_id=user.id,
        incident_id=incident_rej.id,
        start_at=now,
        end_at=now + timedelta(days=1),
        status=SanctionStatusEnum.activa,  # activa tras rechazo
        appeal_text="Solicitud rechazo",
        appeal_response="Rechazada",
    )

    sanction_acc = Sanction(
        user_id=user.id,
        incident_id=incident_acc.id,
        start_at=now,
        end_at=now + timedelta(days=1),
        status=SanctionStatusEnum.expirada,  # expirada por aceptación
        appeal_text="Solicitud aceptada",
        appeal_response="Aceptada",
    )

    db_session.add_all([sanction_rej, sanction_acc])
    db_session.commit()

    view = CurrentLoanView(app)
    view.build()
    view._show_incidents_dialog(loan)  # type: ignore

    dlg = app.page.dialog
    texts = [c for c in _traverse_controls(dlg) if isinstance(c, ft.Text)]
    # Buscar ambos mensajes
    has_rej = any("apelación rechazada" in (t.value or "").lower() for t in texts)
    has_acc = any("apelación aceptada" in (t.value or "").lower() for t in texts)
    assert has_rej and has_acc, "No se mostraron los textos de aceptación/rechazo correctamente"


def test_appeal_banner_only_shown_to_incident_reporter(app, db_session):  # noqa: D401
    """El banner de apelaciones debe mostrarse solo al admin que reportó el incidente."""

    # Crear dos administradores
    admin1 = _create_user(db_session, cedula="3001", role=UserRoleEnum.admin)
    admin2 = _create_user(db_session, cedula="3002", role=UserRoleEnum.admin)

    # Crear usuario sancionado
    sanc_user = _create_user(db_session, cedula="3003", role=UserRoleEnum.usuario)

    # Crear incidente reportado por admin1
    incident = Incident(
        loan_id=None,
        bike_id=None,
        reporter_id=admin1.id,
        type=IncidentTypeEnum.accidente,
        severity=1,
        description="Incident",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(incident)
    db_session.commit()

    # Crear sanción apelada sobre ese incidente
    sanction = Sanction(
        user_id=sanc_user.id,
        incident_id=incident.id,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(days=2),
        status=SanctionStatusEnum.apelada,
        appeal_text="Apelación pendiente",
    )
    db_session.add(sanction)
    db_session.commit()

    # Caso A: admin1 debe ver el banner
    app.current_user = admin1
    app.current_user_role = "admin"
    root_a = DashboardView(app).build()
    texts_a = [c for c in _traverse_controls(root_a) if isinstance(c, ft.Text)]
    banner_present_a = any("apelación(es) de sanción" in (t.value or "").lower() for t in texts_a)
    assert banner_present_a, "El admin que reportó el incidente no vio el banner de apelaciones"

    # Caso B: admin2 NO debe ver el banner
    app.current_user = admin2
    root_b = DashboardView(app).build()
    texts_b = [c for c in _traverse_controls(root_b) if isinstance(c, ft.Text)]
    banner_present_b = any("apelación(es) de sanción" in (t.value or "").lower() for t in texts_b)
    assert not banner_present_b, "Otro admin vio indebidamente el banner de apelaciones" 