#!/usr/bin/env python3
"""
Setup script for VeciRun
Automates initial database setup and sample data creation
"""

import os
import sys
from sqlalchemy import create_engine, text
from config import DATABASE_URL
from database import create_tables
from models import User
from sample_data import populate_sample_data
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session


def test_database_connection() -> bool:
    """Test database connection"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Conexión a base de datos exitosa")
        return True
    except Exception as e:
        print(f"❌ Error de conexión a base de datos: {e}")
        return False


def create_database_tables() -> bool:
    """Create database tables"""
    try:
        create_tables()
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False


def create_sample_data() -> bool:
    """Create sample data for testing"""
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Idempotent population
        populate_sample_data(db)
        db.close()
        return True

    except Exception as e:
        print(f"❌ Error creando datos de muestra: {e}")
        return False


def main() -> None:
    """Main setup function"""
    print("🚀 Configurando VeciRun")
    print("=" * 50)

    # Test database connection
    if not test_database_connection():
        print("\n💡 Asegúrate de que:")
        print("   1. PostgreSQL esté ejecutándose")
        print("   2. La base de datos 'vecirun_db' exista")
        print("   3. Las credenciales en config.py sean correctas")
        sys.exit(1)

    # Create tables
    if not create_database_tables():
        print("\n💡 Verifica que tengas permisos para crear tablas")
        sys.exit(1)

    # Create sample data
    if not create_sample_data():
        print("\n💡 Los datos de muestra no se pudieron crear")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("✅ Configuración completada exitosamente!")
    print("\n📋 Datos de acceso:")
    print("   Usuario Admin:")
    print("   - Cédula: 12345678")
    print("   - Carnet: ADMIN001")
    print("   - Email: admin@universidad.edu")
    print("\n🚲 Bicicletas disponibles:")
    print("   - B001, B002, B003")
    print("\n🏢 Estaciones:")
    print("   - EST001: Calle 26")
    print("   - EST002: Salida al Uriel Gutiérrez")
    print("   - EST003: Calle 53")
    print("   - EST004: Calle 45")
    print("   - EST005: Edificio Ciencia y Tecnología")
    print("\n🎯 Para ejecutar la aplicación:")
    print("   python main.py")


if __name__ == "__main__":
    main()
