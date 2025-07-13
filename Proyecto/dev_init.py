#!/usr/bin/env python3
"""dev_init.py – Script de inicialización en modo desarrollo para VeciRun.

Pasos automatizados:
1. Verifica versión mínima de Python (>=3.11).
2. Instala dependencias desde requirements.txt.
3. Garantiza existencia de archivo .env y variable DATABASE_URL.
   •  Si no existe, crea uno apuntando a SQLite local (vecirun.db).
4. Ejecuta migraciones de Alembic (upgrade head).
5. Carga datos de ejemplo mediante populate_db.py y update_stations.py.
6. Arranca la aplicación (main.py) en modo interactivo.

El script es idempotente: puede ejecutarse múltiples veces sin efectos adversos.
"""
from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Final

# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

ROOT_DIR: Final[Path] = Path(__file__).resolve().parent
PY_CMD: Final[str] = sys.executable  # Respeta venv/instalación actual


def log(msg: str, *, emoji: str = "🔹") -> None:
    """Imprime mensajes uniformes."""
    print(f"{emoji} {msg}")


def run(command: str, *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    """Ejecuta un comando de shell y detiene el script si falla."""
    log(f"Ejecutando: {command}")
    subprocess.run(command, shell=True, check=True, cwd=cwd or ROOT_DIR, env=env)


# ---------------------------------------------------------------------------
# 1. Verificar versión de Python
# ---------------------------------------------------------------------------


def check_python_version(required: tuple[int, int] = (3, 11)) -> None:
    if sys.version_info < required:
        sys.exit(
            f"❌ Python {required[0]}.{required[1]} o superior es requerido. "
            f"Versión actual: {platform.python_version()}"
        )
    log(f"Versión de Python OK: {platform.python_version()}")


# ---------------------------------------------------------------------------
# 2. Instalar dependencias
# ---------------------------------------------------------------------------


def install_dependencies() -> None:
    req_file = ROOT_DIR / "requirements.txt"
    if not req_file.exists():
        log("No se encontró requirements.txt; se omite instalación.", emoji="⚠️")
        return

    # Se instala con --quiet para evitar spam excesivo en consola.
    run(f'"{PY_CMD}" -m pip install --upgrade pip', cwd=ROOT_DIR)
    run(f'"{PY_CMD}" -m pip install -r "{req_file}" --quiet', cwd=ROOT_DIR)
    log("Dependencias instaladas correctamente", emoji="✅")


# ---------------------------------------------------------------------------
# 3. Asegurar archivo .env y DATABASE_URL
# ---------------------------------------------------------------------------


def ensure_env_file() -> None:
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        log(".env ya existe – se respeta configuración actual", emoji="✅")
        return

    # Crea un .env por defecto que usa SQLite local.
    sqlite_path = ROOT_DIR / "vecirun.db"
    default_url = f"sqlite:///{sqlite_path}"
    env_path.write_text(f"DATABASE_URL={default_url}\n", encoding="utf-8")
    log("Se creó .env por defecto con SQLite", emoji="✅")


# ---------------------------------------------------------------------------
# 4. Ejecutar migraciones Alembic
# ---------------------------------------------------------------------------


def run_migrations() -> None:
    alembic_ini = ROOT_DIR / "alembic.ini"
    if not alembic_ini.exists():
        log("alembic.ini no encontrado; se crearán tablas vía ORM", emoji="⚠️")
        from database import create_tables  # type: ignore

        create_tables()
        return

    # Ejecutamos Alembic usando el intérprete actual (``PY_CMD``) para evitar
    # problemas con la variable *PATH* en Windows donde el ejecutable
    # ``alembic`` puede no estar disponible. De esta forma garantizamos que la
    # CLI se lance con el mismo entorno virtual en el que se instalaron las
    # dependencias.
    try:
        run(f'"{PY_CMD}" -m alembic upgrade head', cwd=ROOT_DIR)
    except subprocess.CalledProcessError as exc:
        sys.exit(f"❌ Falló la migración: {exc}")


# ---------------------------------------------------------------------------
# 5. Poblar datos de muestra
# ---------------------------------------------------------------------------


def load_sample_data() -> None:
    # populate_db.py ya maneja verificación de existencia de datos
    sample_scripts = [
        "populate_db.py",
        "update_stations.py",
    ]
    for script in sample_scripts:
        script_path = ROOT_DIR / script
        if script_path.exists():
            run(f'"{PY_CMD}" "{script_path}"')


# ---------------------------------------------------------------------------
# 6. Lanzar aplicación
# ---------------------------------------------------------------------------


def launch_app() -> None:
    log("Iniciando VeciRun… ¡Disfruta! 😊", emoji="🚀")
    os.execv(PY_CMD, [PY_CMD, str(ROOT_DIR / "main.py")])


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    check_python_version()
    install_dependencies()
    ensure_env_file()
    run_migrations()
    load_sample_data()
    launch_app()
