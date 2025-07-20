import pytest
from services import StationService
from models import Station, Bicycle, BikeStatusEnum

@pytest.mark.usefixtures("db_session")
def test_station_capacity_enforcement(db_session):
    """
    Valida que la capacidad máxima de bicicletas por estación se respete.
    - Crea una estación con capacidad limitada.
    - Intenta asignar más bicicletas de las permitidas.
    - Verifica que la consulta de disponibilidad respeta la capacidad.
    """
    # Crear estación con capacidad 2
    station = Station(code="ESTX", name="Estación Test", capacity=2)
    db_session.add(station)
    db_session.commit()
    # Asignar dos bicicletas
    bikes = [Bicycle(serial_number=f"BIKE{i}", bike_code=f"B{i}", status=BikeStatusEnum.disponible) for i in range(2)]
    for bike in bikes:
        bike.station_id = station.id
        db_session.add(bike)
    db_session.commit()
    # Intentar asignar una tercera bicicleta
    bike3 = Bicycle(serial_number="BIKE3", bike_code="B3", status=BikeStatusEnum.disponible, station_id=station.id)
    db_session.add(bike3)
    with pytest.raises(Exception):
        StationService.assign_bicycle_to_station(db_session, bike3, station)
    # Verificar que solo hay 2 bicicletas asignadas
    assigned = StationService.get_bicycles_in_station(db_session, station.id)
    assert len(assigned) == 2
