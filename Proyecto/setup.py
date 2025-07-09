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
from models import User, Bicycle, Station, UserRoleEnum, UserAffiliationEnum, BikeStatusEnum
from sqlalchemy.orm import sessionmaker

def test_database_connection():
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

def create_database_tables():
    """Create database tables"""
    try:
        create_tables()
        print("✅ Tablas creadas exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error creando tablas: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if data already exists
        if db.query(User).first():
            print("ℹ️  Datos de muestra ya existen, saltando creación")
            return True
        
        # Create sample stations
        stations = [
            Station(code="EST001", name="Calle 26"),
            Station(code="EST002", name="Salida al Uriel Gutiérrez"),
            Station(code="EST003", name="Calle 53"),
            Station(code="EST004", name="Calle 45"),
            Station(code="EST005", name="Edificio Ciencia y Tecnología"),
        ]
        
        for station in stations:
            db.add(station)
        db.commit()
        print("✅ Estaciones de muestra creadas")
        
        # Create sample bicycles
        bicycles = [
            Bicycle(serial_number="BIKE001", bike_code="B001", status=BikeStatusEnum.disponible),
            Bicycle(serial_number="BIKE002", bike_code="B002", status=BikeStatusEnum.disponible),
            Bicycle(serial_number="BIKE003", bike_code="B003", status=BikeStatusEnum.disponible),
        ]
        
        for bicycle in bicycles:
            db.add(bicycle)
        db.commit()
        print("✅ Bicicletas de muestra creadas")
        
        # Create sample admin user
        admin_user = User(
            cedula="12345678",
            carnet="USER_12345678",
            full_name="Administrador Sistema",
            email="admin@universidad.edu",
            affiliation=UserAffiliationEnum.administrativo,
            role=UserRoleEnum.admin
        )
        
        # Create 5 operator users, one for each station
        operator_users = [
            User(
                cedula="11111111",
                carnet="USER_11111111",
                full_name="Operador Calle 26",
                email="operador1@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="22222222",
                carnet="USER_22222222",
                full_name="Operador Uriel Gutiérrez",
                email="operador2@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="33333333",
                carnet="USER_33333333",
                full_name="Operador Calle 53",
                email="operador3@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="44444444",
                carnet="USER_44444444",
                full_name="Operador Calle 45",
                email="operador4@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            ),
            User(
                cedula="55555555",
                carnet="USER_55555555",
                full_name="Operador Ciencia y Tecnología",
                email="operador5@universidad.edu",
                affiliation=UserAffiliationEnum.administrativo,
                role=UserRoleEnum.operador
            )
        ]
        
        db.add(admin_user)
        db.add_all(operator_users)
        db.commit()
        print("✅ Usuario administrador creado")
        print("✅ 5 usuarios operadores creados")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creando datos de muestra: {e}")
        return False

def main():
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