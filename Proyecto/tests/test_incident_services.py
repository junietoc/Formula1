import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base,
    UserRoleEnum,
    UserAffiliationEnum,
    BikeStatusEnum,
    LoanStatusEnum,
    IncidentTypeEnum,
    IncidentSeverityEnum,
    User,
    Bicycle,
    Station,
    Loan,
    Incident,
    ReturnReport,
)
from services import UserService, BicycleService, StationService, LoanService, IncidentService

# -----------------------
# Fixtures
# -----------------------


@pytest.fixture(scope="function")
def session():
    """Creates a new in-memory SQLite database for each test function."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)

    # Create all tables
    Base.metadata.create_all(engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def sample_data(session):
    """Create sample data for incident tests."""
    # Create admin user
    admin = UserService.create_user(
        session,
        cedula="123456",
        carnet="ADMIN_123456",
        full_name="Admin Test",
        email="admin@test.com",
        affiliation=UserAffiliationEnum.administrativo,
        role=UserRoleEnum.admin,
    )
    
    # Create regular user
    user = UserService.create_user(
        session,
        cedula="789012",
        carnet="USER_789012",
        full_name="User Test",
        email="user@test.com",
        affiliation=UserAffiliationEnum.estudiante,
        role=UserRoleEnum.usuario,
    )
    
    # Create station
    station = Station(code="EST001", name="Test Station")
    session.add(station)
    session.commit()
    
    # Create bicycle
    bike = Bicycle(
        serial_number="SN123",
        bike_code="B001",
        status=BikeStatusEnum.disponible,
        current_station_id=station.id,
    )
    session.add(bike)
    session.commit()
    
    # Create loan
    loan = Loan(
        user_id=user.id,
        bike_id=bike.id,
        station_out_id=station.id,
        station_in_id=station.id,
        status=LoanStatusEnum.cerrado,
        time_out=datetime.now(timezone(timedelta(hours=-5))) - timedelta(hours=2),
        time_in=datetime.now(timezone(timedelta(hours=-5))),
    )
    session.add(loan)
    session.commit()
    
    return {
        "admin": admin,
        "user": user,
        "station": station,
        "bike": bike,
        "loan": loan,
    }


# -----------------------
# IncidentService tests
# -----------------------


def test_create_incident_success(session, sample_data):
    """Test creating a basic incident successfully."""
    data = sample_data
    
    incident = IncidentService.create_incident(
        db=session,
        loan_id=data["loan"].id,
        bike_id=data["bike"].id,
        reporter_id=data["admin"].id,
        incident_type=IncidentTypeEnum.deterioro,
        severity=IncidentSeverityEnum.media,
        description="Bicicleta con frenos desgastados",
    )
    
    assert incident.id is not None
    assert incident.loan_id == data["loan"].id
    assert incident.bike_id == data["bike"].id
    assert incident.reporter_id == data["admin"].id
    assert incident.type == IncidentTypeEnum.deterioro
    assert incident.severity == 2  # media = 2
    assert incident.description == "Bicicleta con frenos desgastados"
    assert incident.created_at is not None


def test_create_automatic_late_incident_severity_calculation(session, sample_data):
    """Test automatic incident creation with different severity levels based on delay time."""
    data = sample_data
    
    # Test different delay times and expected severities
    test_cases = [
        (30, 1),      # 30 min = leve (1) - ≤ 45 min
        (60, 2),      # 1 hour = media (2) - > 45 min, ≤ 5 hours (300 min)
        (240, 2),     # 4 hours = media (2) - > 45 min, ≤ 5 hours (300 min)
        (360, 3),     # 6 hours = grave (3) - > 5 hours (300 min), ≤ 24 hours (1440 min)
        (1200, 3),    # 20 hours = grave (3) - > 5 hours, ≤ 24 hours
        (1500, 4),    # 25 hours = maxima (4) - > 24 hours (1440 min)
    ]
    
    for i, (minutes_late, expected_severity_int) in enumerate(test_cases):
        # Create a new loan for each test to avoid conflicts
        new_loan = Loan(
            user_id=data["user"].id,
            bike_id=data["bike"].id,
            station_out_id=data["station"].id,
            station_in_id=data["station"].id,
            status=LoanStatusEnum.cerrado,
            time_out=datetime.now(timezone(timedelta(hours=-5))) - timedelta(hours=2),
            time_in=datetime.now(timezone(timedelta(hours=-5))),
        )
        session.add(new_loan)
        session.commit()
        
        incident = IncidentService.create_automatic_late_incident(
            db=session,
            loan_id=new_loan.id,
            bike_id=data["bike"].id,
            reporter_id=data["admin"].id,
            minutes_late=minutes_late,
        )
        
        assert incident.type == IncidentTypeEnum.uso_indebido
        assert incident.severity == expected_severity_int, f"Failed for {minutes_late} minutes: expected {expected_severity_int}, got {incident.severity}"
        assert f"Devolución tardía: {minutes_late} minutos de retraso" in incident.description


def test_create_return_report_with_incidents(session, sample_data):
    """Test creating a return report with multiple incidents and correct day calculation."""
    data = sample_data
    
    # Create multiple incidents with different severities
    incident1 = IncidentService.create_incident(
        db=session,
        loan_id=data["loan"].id,
        bike_id=data["bike"].id,
        reporter_id=data["admin"].id,
        incident_type=IncidentTypeEnum.accidente,
        severity=IncidentSeverityEnum.leve,
        description="Accidente menor",
    )
    
    incident2 = IncidentService.create_incident(
        db=session,
        loan_id=data["loan"].id,
        bike_id=data["bike"].id,
        reporter_id=data["admin"].id,
        incident_type=IncidentTypeEnum.deterioro,
        severity=IncidentSeverityEnum.grave,
        description="Deterioro grave",
    )
    
    incident3 = IncidentService.create_incident(
        db=session,
        loan_id=data["loan"].id,
        bike_id=data["bike"].id,
        reporter_id=data["admin"].id,
        incident_type=IncidentTypeEnum.otro,
        severity=IncidentSeverityEnum.maxima,
        description="Otro incidente",
    )
    
    incidents = [incident1, incident2, incident3]
    
    # Create return report
    report = IncidentService.create_return_report(
        db=session,
        loan_id=data["loan"].id,
        created_by=data["admin"].id,
        incidents=incidents,
    )
    
    # Verify report
    assert report.id is not None
    assert report.loan_id == data["loan"].id
    assert report.created_by == data["admin"].id
    assert report.created_at is not None
    
    # Calculate expected total days: 1 (leve) + 7 (grave) + 30 (maxima) = 38
    expected_total_days = 1 + 7 + 30
    assert report.total_incident_days == expected_total_days
    
    # Verify incidents are associated with the report
    for incident in incidents:
        session.refresh(incident)
        assert incident.return_report_id == report.id


def test_get_incidents_by_loan(session, sample_data):
    """Test retrieving incidents by loan ID."""
    data = sample_data
    
    # Create incidents for the loan
    incident1 = IncidentService.create_incident(
        db=session,
        loan_id=data["loan"].id,
        bike_id=data["bike"].id,
        reporter_id=data["admin"].id,
        incident_type=IncidentTypeEnum.accidente,
        severity=IncidentSeverityEnum.leve,
        description="Accidente 1",
    )
    
    incident2 = IncidentService.create_incident(
        db=session,
        loan_id=data["loan"].id,
        bike_id=data["bike"].id,
        reporter_id=data["admin"].id,
        incident_type=IncidentTypeEnum.deterioro,
        severity=IncidentSeverityEnum.media,
        description="Deterioro 1",
    )
    
    # Create another loan and incident (should not be returned)
    other_loan = Loan(
        user_id=data["user"].id,
        bike_id=data["bike"].id,
        station_out_id=data["station"].id,
        status=LoanStatusEnum.cerrado,
    )
    session.add(other_loan)
    session.commit()
    
    other_incident = IncidentService.create_incident(
        db=session,
        loan_id=other_loan.id,
        bike_id=data["bike"].id,
        reporter_id=data["admin"].id,
        incident_type=IncidentTypeEnum.otro,
        severity=IncidentSeverityEnum.leve,
        description="Otro incidente",
    )
    
    # Get incidents for the original loan
    incidents = IncidentService.get_incidents_by_loan(session, data["loan"].id)
    
    assert len(incidents) == 2
    assert incident1 in incidents
    assert incident2 in incidents
    assert other_incident not in incidents


def test_get_return_report_by_loan(session, sample_data):
    """Test retrieving return report by loan ID."""
    data = sample_data
    
    # Create a return report
    report = IncidentService.create_return_report(
        db=session,
        loan_id=data["loan"].id,
        created_by=data["admin"].id,
    )
    
    # Retrieve the report
    retrieved_report = IncidentService.get_return_report_by_loan(session, data["loan"].id)
    
    assert retrieved_report is not None
    assert retrieved_report.id == report.id
    assert retrieved_report.loan_id == data["loan"].id
    
    # Test with non-existent loan
    import uuid
    non_existent_report = IncidentService.get_return_report_by_loan(session, uuid.uuid4())
    assert non_existent_report is None


def test_severity_days_mapping():
    """Test that severity to days mapping is correct."""
    assert IncidentService.SEVERITY_DAYS[1] == 1   # leve
    assert IncidentService.SEVERITY_DAYS[2] == 3   # media
    assert IncidentService.SEVERITY_DAYS[3] == 7   # grave
    assert IncidentService.SEVERITY_DAYS[4] == 30  # maxima


def test_severity_enum_conversion():
    """Test conversion between enum and integer values."""
    # Test enum to int conversion
    assert IncidentService.SEVERITY_ENUM_TO_INT[IncidentSeverityEnum.leve] == 1
    assert IncidentService.SEVERITY_ENUM_TO_INT[IncidentSeverityEnum.media] == 2
    assert IncidentService.SEVERITY_ENUM_TO_INT[IncidentSeverityEnum.grave] == 3
    assert IncidentService.SEVERITY_ENUM_TO_INT[IncidentSeverityEnum.maxima] == 4
    
    # Test int to enum conversion
    assert IncidentService.SEVERITY_INT_TO_ENUM[1] == IncidentSeverityEnum.leve
    assert IncidentService.SEVERITY_INT_TO_ENUM[2] == IncidentSeverityEnum.media
    assert IncidentService.SEVERITY_INT_TO_ENUM[3] == IncidentSeverityEnum.grave
    assert IncidentService.SEVERITY_INT_TO_ENUM[4] == IncidentSeverityEnum.maxima 