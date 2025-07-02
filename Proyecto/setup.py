#!/usr/bin/env python3
"""
Setup script for Bike Loan System
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
            Station(code="EST001", name="Estación Central"),
            Station(code="EST002", name="Estación Norte"),
            Station(code="EST003", name="Estación Sur"),
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
            carnet="ADMIN001",
            full_name="Administrador Sistema",
            email="admin@universidad.edu",
            affiliation=UserAffiliationEnum.administrativo,
            role=UserRoleEnum.admin
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Usuario administrador creado")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error creando datos de muestra: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Configurando Sistema de Préstamo de Bicicletas")
    print("=" * 50)
    
    # Test database connection
    if not test_database_connection():
        print("\n💡 Asegúrate de que:")
        print("   1. PostgreSQL esté ejecutándose")
        print("   2. La base de datos 'bike_loan_db' exista")
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
    print("   - EST001: Estación Central")
    print("   - EST002: Estación Norte")
    print("   - EST003: Estación Sur")
    print("\n🎯 Para ejecutar la aplicación:")
    print("   python main.py")

if __name__ == "__main__":
    main() 