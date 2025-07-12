#!/usr/bin/env python3
"""
Script para crear las estaciones con los nombres correctos en español
"""

import sqlite3
import uuid
from config import DB_FILENAME

def create_stations() -> None:
    """Crear las estaciones con los nombres correctos"""
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(str(DB_FILENAME))
        cursor = conn.cursor()
        
        print("🔄 Creando estaciones...")
        
        # Crear cada estación con el nombre correcto
        stations = [
            ("EST001", "Calle 26"),
            ("EST002", "Salida al Uriel Gutiérrez"),
            ("EST003", "Calle 53"),
            ("EST004", "Calle 45"),
            ("EST005", "Edificio Ciencia y Tecnología"),
        ]
        
        # Obtener códigos existentes para evitar duplicados
        cursor.execute("SELECT code FROM stations")
        existing_codes = {row[0] for row in cursor.fetchall()}

        for code, name in stations:
            if code in existing_codes:
                print(f"⚠️  {code} ya existe – se omite")
                continue

            station_id = str(uuid.uuid4())
            cursor.execute(
                "INSERT INTO stations (id, code, name) VALUES (?, ?, ?)",
                (station_id, code, name)
            )
            print(f"✅ Creada {code}: {name}")
        
        # Verificar que se crearon correctamente
        cursor.execute("SELECT code, name FROM stations ORDER BY code")
        created_stations = cursor.fetchall()
        
        print("\n📊 Estaciones creadas:")
        print("-" * 40)
        for code, name in created_stations:
            print(f"  {code}: {name}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Creación completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_stations() 