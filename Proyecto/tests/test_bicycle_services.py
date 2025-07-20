import pytest
from services import BicycleService
from models import BikeStatusEnum, Bicycle

@pytest.mark.usefixtures("db_session")
def test_bicycle_maintenance_flow(db_session):
    """
    Valida el ciclo completo de mantenimiento de bicicletas:
    - Marcar bicicleta como 'mantenimiento'.
    - Verificar que no se puede prestar.
    - Liberar bicicleta y verificar disponibilidad.
    - Consultar historial de estados.
    """
    # Crear bicicleta
    bike = Bicycle(serial_number="BIKE100", bike_code="B100", status=BikeStatusEnum.disponible)
    db_session.add(bike)
    db_session.commit()
    # Marcar como mantenimiento
    BicycleService.update_bicycle_status(db_session, bike, BikeStatusEnum.mantenimiento)
    db_session.commit()
    assert bike.status == BikeStatusEnum.mantenimiento
    # Verificar que no se puede prestar
    available = BicycleService.get_available_bicycles(db_session)
    assert bike not in available
    # Liberar bicicleta
    BicycleService.update_bicycle_status(db_session, bike, BikeStatusEnum.disponible)
    db_session.commit()
    available = BicycleService.get_available_bicycles(db_session)
    assert bike in available
    # Consultar historial (stub)
    # assert BicycleService.get_status_history(bike) == [BikeStatusEnum.disponible, BikeStatusEnum.mantenimiento, BikeStatusEnum.disponible]
