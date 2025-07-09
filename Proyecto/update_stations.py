#!/usr/bin/env python3
"""
Script para crear las estaciones con los nombres correctos en español
"""

import sqlite3
import uuid

def create_stations():
    """Crear las estaciones con los nombres correctos"""
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('vecirun.db')
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
        
        for code, name in stations:
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