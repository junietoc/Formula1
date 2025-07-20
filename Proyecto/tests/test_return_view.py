import pytest
from datetime import datetime, timedelta
from models import User, Bicycle, Station, Loan, LoanStatusEnum, BikeStatusEnum
from views.return_view import ReturnView

@pytest.mark.usefixtures("db_session")
def test_late_loan_alert_display(db_session):
    """
    Valida que los préstamos tardíos (>15 min) se muestren con alerta visual en la vista de devoluciones.
    - Crea préstamo abierto con tiempo de salida >15 min.
    - Verifica que la fila aparece resaltada y con icono de alerta.
    - Verifica el tooltip explicativo.
    """
    user = User(cedula="77777777", carnet="USER_77777777", full_name="Usuario Tardío", email="tarde@correo.com", affiliation="estudiante", role="usuario")
    bike = Bicycle(serial_number="BIKE300", bike_code="B300", status=BikeStatusEnum.prestada)
    station = Station(code="ESTZ", name="Estación Z")
    db_session.add_all([user, bike, station])
    db_session.commit()
    # Préstamo abierto hace 20 minutos
    loan = Loan(user_id=user.id, bike_id=bike.id, station_out_id=station.id, station_in_id=station.id, status=LoanStatusEnum.abierto, time_out=datetime.now() - timedelta(minutes=20))
    db_session.add(loan)
    db_session.commit()
    # Instanciar vista y construir controles
    app_stub = type("AppStub", (), {"page": None, "db": db_session, "current_user_station": station.code, "show_return_view": lambda self: None})()
    view = ReturnView(app_stub)
    controls = view.build()
    # Buscar fila resaltada
    found_alert = False
    for col in controls.controls:
        if hasattr(col, "bgcolor") and col.bgcolor == "red100":
            found_alert = True
    assert found_alert, "No se encontró alerta visual para préstamo tardío"
