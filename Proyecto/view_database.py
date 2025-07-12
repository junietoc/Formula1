#!/usr/bin/env python3
"""
Script para ver el contenido de la base de datos
"""

import sqlite3
from tabulate import tabulate
from config import DB_FILENAME


def view_database():
    """Ver el contenido de la base de datos"""
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect(str(DB_FILENAME))
        cursor = conn.cursor()

        print("🗄️  CONTENIDO DE LA BASE DE DATOS")
        print("=" * 50)

        # Ver tablas disponibles
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        print(f"📋 Tablas encontradas: {len(tables)}")
        for table in tables:
            print(f"   - {table[0]}")
        print()

        # Ver contenido de cada tabla
        for table in tables:
            table_name = table[0]
            print(f"📊 TABLA: {table_name.upper()}")
            print("-" * 30)

            # Obtener datos
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            if rows:
                # Obtener nombres de columnas
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]

                # Mostrar datos en formato tabla
                print(tabulate(rows, headers=columns, tablefmt="grid"))
                print(f"Total de registros: {len(rows)}")
            else:
                print("(Tabla vacía)")

            print("\n")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


def view_specific_table(table_name):
    """Ver una tabla específica"""
    try:
        conn = sqlite3.connect(str(DB_FILENAME))
        cursor = conn.cursor()

        print(f"📊 TABLA: {table_name.upper()}")
        print("-" * 30)

        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if rows:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            print(tabulate(rows, headers=columns, tablefmt="grid"))
            print(f"Total de registros: {len(rows)}")
        else:
            print("(Tabla vacía)")

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Ver tabla específica
        table_name = sys.argv[1]
        view_specific_table(table_name)
    else:
        # Ver toda la base de datos
        view_database()
