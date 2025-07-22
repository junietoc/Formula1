#!/usr/bin/env python3
"""
Script to populate the VeciRun database with initial data (stations, bicycles, users).
Run this once after setting up the project:

    python populate_db.py

It uses SQLAlchemy sessions defined in `database.py` and the declarative models
in `models.py`. Existing data will be left untouched – the script only inserts
records if their respective tables are empty.
"""

from database import create_tables, SessionLocal, engine  # type: ignore
from sample_data import populate_sample_data
from sqlalchemy.orm import Session
from models import (
    Base,
    Station,
    Bicycle,
    User,
    UserRoleEnum,
    UserAffiliationEnum,
    BikeStatusEnum,
)


def populate_stations(session: Session) -> None:
    """Ensure default stations are present, inserting any that are missing."""
    stations = [
        ("EST001", "Calle 26"),
        ("EST002", "Salida al Uriel Gutiérrez"),
        ("EST003", "Calle 53"),
        ("EST004", "Calle 45"),
        ("EST005", "Edificio Ciencia y Tecnología"),
    ]

    # Fetch existing codes to avoid duplicates
    existing_codes = {code for (code,) in session.query(Station.code).all()}

    inserted = 0
    for code, name in stations:
        if code not in existing_codes:
            session.add(Station(code=code, name=name))
            inserted += 1

    print(
        f"✅ Stations ensured: {len(stations)} total ({inserted} inserted, {len(stations)-inserted} existing)"
    )


def populate_bicycles(session: Session) -> None:
    """Ensure 40 bicycles are present, inserting any missing ones."""

    bicycles = [(f"BIKE{num:03d}", f"B{num:03d}") for num in range(1, 41)]

    existing_serials = {serial for (serial,) in session.query(Bicycle.serial_number).all()}

    # Ensure pending station inserts are flushed so they are visible in query
    session.flush()
    # Obtain list of station IDs to assign bikes to (round-robin)
    station_ids = [sid for (sid,) in session.query(Station.id).order_by(Station.code).all()]
    if not station_ids:
        raise RuntimeError("No stations found – run populate_stations first.")

    inserted = 0
    for idx, (serial, code) in enumerate(bicycles):
        if serial not in existing_serials:
            session.add(
                Bicycle(
                    serial_number=serial,
                    bike_code=code,
                    status=BikeStatusEnum.disponible,
                    current_station_id=station_ids[idx % len(station_ids)],
                )
            )
            inserted += 1

    print(f"✅ Bicycles ensured: 40 total ({inserted} inserted, {40 - inserted} existing)")


def populate_users(session: Session) -> None:
    """Ensure admin, 5 operators and 20 regular users exist (26 total)."""

    existing_cedulas = {cedula for (cedula,) in session.query(User.cedula).all()}

    to_add = []

    # Admin user
    if "12345678" not in existing_cedulas:
        to_add.append(
            User(
                cedula="12345678",
                carnet="USER_12345678",
                full_name="Administrador Sistema",
                email="admin@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.admin,
            )
        )

    # Operators
    operator_templates = [
        ("11111111", "Operador Calle 26"),
        ("22222222", "Operador Uriel Gutiérrez"),
        ("33333333", "Operador Calle 53"),
        ("44444444", "Operador Calle 45"),
        ("55555555", "Operador Ciencia y Tecnología"),
    ]

    for idx, (cedula, name) in enumerate(operator_templates, start=1):
        if cedula not in existing_cedulas:
            to_add.append(
                User(
                    cedula=cedula,
                    carnet=f"USER_{cedula}",
                    full_name=name,
                    email=f"operador{idx}@universidad.edu",
                    affiliation=UserAffiliationEnum.administrativo,
                    role=UserRoleEnum.operador,
                )
            )

    # Regular users (20)
    for i in range(20):
        cedula = f"{80000000 + i:08d}"
        if cedula not in existing_cedulas:
            to_add.append(
                User(
                    cedula=cedula,
                    carnet=f"USER_{cedula}",
                    full_name=f"Usuario Regular {i + 1}",
                    email=f"usuario{i + 1}@universidad.edu",
                    affiliation=UserAffiliationEnum.estudiante,
                    role=UserRoleEnum.usuario,
                    stars=3,
                )
            )

    session.add_all(to_add)

    print(f"✅ Users ensured: 26 total ({len(to_add)} inserted, {26 - len(to_add)} existing)")


# ---------------------------------------------------------------------------
# Database-reset helper
# ---------------------------------------------------------------------------


def reset_database() -> None:
    """Drop all existing tables and recreate them fresh from the models."""

    # Drop everything first
    Base.metadata.drop_all(bind=engine)

    # Re-create according to current models
    create_tables()

    print("🗑️  Existing tables dropped and schema recreated from models.")


def main() -> None:
    # Recreate the database schema from scratch (drop & create)
    reset_database()

    # Create a new session
    session = SessionLocal()
    try:
        populate_sample_data(session)

        session.commit()
        print("\n🎉 Database population finished successfully!")
    except Exception as exc:
        session.rollback()
        raise exc
    finally:
        session.close()


if __name__ == "__main__":
    main()
