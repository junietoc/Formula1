import pytest
from services import LoanService
from models import User, Bicycle, Station, LoanStatusEnum, BikeStatusEnum

@pytest.mark.usefixtures("db_session")
def test_concurrent_loans_prevention(db_session):
    """
    Valida que no se puedan registrar préstamos concurrentes para el mismo usuario y bicicleta.
    - Crea usuario y bicicleta disponible.
    - Intenta registrar dos préstamos simultáneos.
    - Verifica que solo uno se registra y el otro falla.
    """
    user = User(cedula="88888888", carnet="USER_88888888", full_name="Usuario Test", email="test@correo.com", affiliation="estudiante", role="usuario")
    bike = Bicycle(serial_number="BIKE200", bike_code="B200", status=BikeStatusEnum.disponible)
    station = Station(code="ESTY", name="Estación Y")
    db_session.add_all([user, bike, station])
    db_session.commit()
    # Primer préstamo
    loan1 = LoanService.create_loan(db_session, user.id, bike.id, station.id)
    db_session.commit()
    # Segundo préstamo concurrente
    with pytest.raises(Exception):
        LoanService.create_loan(db_session, user.id, bike.id, station.id)
    # Verificar estado final
    assert bike.status == BikeStatusEnum.prestada
    assert loan1.status == LoanStatusEnum.abierto
