from sqlalchemy.orm import Session
from models import (
    Station,
    Bicycle,
    User,
    UserRoleEnum,
    UserAffiliationEnum,
    BikeStatusEnum,
)


def populate_sample_data(session: Session, *, num_bikes: int = 40) -> None:
    """Inserta estaciones, bicicletas y usuarios de ejemplo si aún no existen.

    La función es idempotente: se limita a crear los registros que falten.
    """

    # ------------------
    # Estaciones
    # ------------------
    stations = [
        ("EST001", "Calle 26"),
        ("EST002", "Salida al Uriel Gutiérrez"),
        ("EST003", "Calle 53"),
        ("EST004", "Calle 45"),
        ("EST005", "Edificio Ciencia y Tecnología"),
    ]
    existing_codes = {code for (code,) in session.query(Station.code).all()}
    for code, name in stations:
        if code not in existing_codes:
            session.add(Station(code=code, name=name))
    session.flush()

    # ------------------
    # Bicicletas
    # ------------------
    existing_serials = {serial for (serial,) in session.query(Bicycle.serial_number).all()}
    station_ids = [sid for (sid,) in session.query(Station.id).order_by(Station.code).all()]
    if not station_ids:
        session.commit()
        station_ids = [sid for (sid,) in session.query(Station.id).order_by(Station.code).all()]

    for idx in range(num_bikes):
        serial = f"BIKE{idx+1:03d}"
        code = f"B{idx+1:03d}"
        if serial in existing_serials:
            continue
        session.add(
            Bicycle(
                serial_number=serial,
                bike_code=code,
                status=BikeStatusEnum.disponible,
                current_station_id=station_ids[idx % len(station_ids)],
            )
        )

    # ------------------
    # Usuarios
    # ------------------
    existing_cedulas = {cedula for (cedula,) in session.query(User.cedula).all()}

    # Admin
    if "12345678" not in existing_cedulas:
        session.add(
            User(
                cedula="12345678",
                carnet="USER_12345678",
                full_name="Administrador Sistema",
                email="admin@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.admin,
            )
        )

    # Operadores
    operator_templates = [
        ("11111111", "Operador Calle 26"),
        ("22222222", "Operador Uriel Gutiérrez"),
        ("33333333", "Operador Calle 53"),
        ("44444444", "Operador Calle 45"),
        ("55555555", "Operador Ciencia y Tecnología"),
    ]
    for cedula, name in operator_templates:
        if cedula not in existing_cedulas:
            session.add(
                User(
                    cedula=cedula,
                    carnet=f"USER_{cedula}",
                    full_name=name,
                    email=f"operador_{cedula}@universidad.edu",
                    affiliation=UserAffiliationEnum.administrativo,
                    role=UserRoleEnum.operador,
                )
            )

    # Usuarios regulares (20)
    for i in range(20):
        cedula = f"{80000000 + i:08d}"
        if cedula in existing_cedulas:
            continue
        session.add(
            User(
                cedula=cedula,
                carnet=f"USER_{cedula}",
                full_name=f"Usuario Regular {i + 1}",
                email=f"usuario{i + 1}@universidad.edu",
                affiliation=UserAffiliationEnum.estudiante,
                role=UserRoleEnum.usuario,
            )
        )

    session.commit()
