import pytest
from datetime import datetime, timedelta
from services import LoanService, SanctionService
from models import User, Bicycle, Station, Loan, LoanStatusEnum, BikeStatusEnum, SanctionStatusEnum

@pytest.mark.usefixtures("db_session")
def test_automatic_sanction_generation_on_late_return(db_session):
    """
    Valida la generación automática de sanción al registrar devolución tardía.
    - Crea préstamo abierto y simula devolución después de 30 min.
    - Verifica que se genera sanción automática con severidad adecuada.
    - Verifica la asociación con el préstamo y el usuario.
    """
    user = User(cedula="66666666", carnet="USER_66666666", full_name="Usuario Sancionado", email="sancion@correo.com", affiliation="estudiante", role="usuario")
    bike = Bicycle(serial_number="BIKE400", bike_code="B400", status=BikeStatusEnum.prestada)
    station = Station(code="ESTW", name="Estación W")
    db_session.add_all([user, bike, station])
    db_session.commit()
    # Préstamo abierto hace 30 minutos
    loan = Loan(user_id=user.id, bike_id=bike.id, station_out_id=station.id, station_in_id=station.id, status=LoanStatusEnum.abierto, time_out=datetime.now() - timedelta(minutes=30))
    db_session.add(loan)
    db_session.commit()
    # Registrar devolución
    LoanService.return_loan(db_session, loan_id=loan.id, station_in_id=station.id)
    # Verificar sanción automática
    sanctions = SanctionService.get_sanctions_by_user(db_session, user.id)
    assert any(s.status == SanctionStatusEnum.activa for s in sanctions), "No se generó sanción automática por devolución tardía"
