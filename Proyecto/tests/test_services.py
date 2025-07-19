import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base,
    UserRoleEnum,
    UserAffiliationEnum,
    BikeStatusEnum,
    LoanStatusEnum,
    User,
    Bicycle,
    Station,
)
from services import UserService, BicycleService, StationService, LoanService

# -----------------------
# Fixtures
# -----------------------


@pytest.fixture(scope="function")
def session():
    """Creates a new in-memory SQLite database for each test function."""
    # In-memory SQLite is fast and requires no external services
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create all tables
    Base.metadata.create_all(engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------
# Helper factories
# -----------------------


def _create_station(db, code: str, name: str) -> Station:
    station = Station(code=code, name=name)
    db.add(station)
    db.commit()
    db.refresh(station)
    return station


def _create_bicycle(
    db, serial: str, code: str, status: BikeStatusEnum = BikeStatusEnum.disponible
) -> Bicycle:
    bike = Bicycle(serial_number=serial, bike_code=code, status=status)
    db.add(bike)
    db.commit()
    db.refresh(bike)
    return bike


# -----------------------
# UserService tests
# -----------------------


def test_create_user_generates_carnet_when_empty(session):
    user = UserService.create_user(
        session,
        cedula="987654",
        carnet="",  # empty carnet should be auto-generated
        full_name="Test User",
        email="test@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )

    assert user.carnet == "USER_987654"
    # Should be retrievable via cedula
    fetched = UserService.get_user_by_cedula(session, "987654")
    assert fetched.id == user.id


def test_get_user_by_carnet(session):
    user = UserService.create_user(
        session,
        cedula="123123",
        carnet="CUSTOM_CARNET",
        full_name="Another User",
        email="another@example.com",
        affiliation=UserAffiliationEnum.docente,
        role=UserRoleEnum.usuario,
    )

    fetched = UserService.get_user_by_carnet(session, "CUSTOM_CARNET")
    assert fetched.id == user.id


# -----------------------
# BicycleService tests
# -----------------------


def test_get_available_bicycles_filters_by_status(session):
    bike_available = _create_bicycle(session, "S001", "B001", BikeStatusEnum.disponible)
    _create_bicycle(session, "S002", "B002", BikeStatusEnum.prestada)
    _create_bicycle(session, "S003", "B003", BikeStatusEnum.mantenimiento)

    available = BicycleService.get_available_bicycles(session)
    assert len(available) == 1
    assert bike_available in available


# -----------------------
# StationService tests
# -----------------------


def test_get_station_by_code(session):
    station = _create_station(session, "EST001", "Calle 26")

    fetched = StationService.get_station_by_code(session, "EST001")
    assert fetched.id == station.id


# -----------------------
# LoanService tests
# -----------------------


def test_loan_lifecycle(session):
    """End-to-end test: create loan -> verify open -> return loan -> verify closed."""
    # Prepare data
    user = UserService.create_user(
        session,
        cedula="555555",
        carnet="",
        full_name="Loan User",
        email="loan@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )
    bike = _create_bicycle(session, "S010", "B010", BikeStatusEnum.disponible)
    station_out = _create_station(session, "EST100", "Salida")
    station_in = _create_station(session, "EST200", "Llegada")

    # --- Create loan ---
    loan = LoanService.create_loan(
        session,
        user_id=user.id,
        bike_id=bike.id,
        station_out_id=station_out.id,
        station_in_id=station_in.id,
    )

    # Assertions after creating loan
    assert loan.status == LoanStatusEnum.abierto
    session.refresh(bike)
    assert bike.status == BikeStatusEnum.prestada

    open_loans = LoanService.get_open_loans_by_user(session, user.id)
    assert loan in open_loans

    by_cedula = LoanService.get_open_loans_by_user_cedula(session, user.cedula)
    assert loan in by_cedula

    # --- Return loan ---
    returned = LoanService.return_loan(
        session,
        loan_id=loan.id,
        station_in_id=station_in.id,
    )

    assert returned.status == LoanStatusEnum.cerrado
    assert returned.time_in is not None

    session.refresh(bike)
    assert bike.status == BikeStatusEnum.disponible

    # After closing, there should be no open loans
    assert LoanService.get_open_loans_by_user(session, user.id) == []

    # Attempting to return again should raise ValueError
    with pytest.raises(ValueError):
        LoanService.return_loan(session, loan.id, station_in.id)


def test_bicycle_station_updates_on_loan_return(session):
    """La bicicleta debe cambiar su estación actual correctamente durante el ciclo de préstamo."""
    # Preparar datos
    user = UserService.create_user(
        session,
        cedula="222222",
        carnet="",
        full_name="Station Test User",
        email="station@example.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )

    station_out = _create_station(session, "EST300", "Salida 300")
    station_in = _create_station(session, "EST400", "Llegada 400")

    bike = _create_bicycle(
        session,
        serial="S300",
        code="B300",
        status=BikeStatusEnum.disponible,
    )
    # La bicicleta inicia en station_out
    bike.current_station_id = station_out.id
    session.commit()

    # --- Crear préstamo ---
    loan = LoanService.create_loan(
        session,
        user_id=user.id,
        bike_id=bike.id,
        station_out_id=station_out.id,
        station_in_id=station_in.id,
    )

    # Al iniciar el préstamo la bicicleta ya no debe estar en ninguna estación
    session.refresh(bike)
    assert bike.current_station_id is None, "La bicicleta debería estar sin estación durante el préstamo"

    # --- Registrar devolución ---
    LoanService.return_loan(session, loan_id=loan.id, station_in_id=station_in.id)

    # La bicicleta debe quedar asociada a la estación de llegada
    session.refresh(bike)
    assert (
        bike.current_station_id == station_in.id
    ), "La bicicleta no se asignó correctamente a la estación de llegada"
