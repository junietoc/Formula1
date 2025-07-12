import types
import flet as ft
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database  # noqa: F401 – needed to patch SessionLocal

from models import Base, Station, Bicycle, BikeStatusEnum

# -------------------------------------------------
#   Stub de ElevatedButton (igual al usado en tests/test_ui_loan.py)
# -------------------------------------------------


class _DummyElevatedButton:  # noqa: D101
    last_callback = None

    def __init__(self, *_, on_click=None, **__):  # noqa: D401
        self.on_click = on_click
        _DummyElevatedButton.last_callback = on_click


# Parchar antes de importar la app principal para que cualquier referencia
# use el stub y evitemos dependencias de Flet en los tests.
ft.ElevatedButton = _DummyElevatedButton  # type: ignore

from main import VeciRunApp  # noqa: E402  (import después de parchar)


def _extract_text_values(ctrl):  # noqa: D401
    """Recorre un árbol de controles Flet y extrae los valores de *ft.Text*."""
    import flet as _ft  # Importación local para evitar problemas de orden

    texts: list[str] = []
    if isinstance(ctrl, _ft.Text):
        # Algunos textos relevantes están en ``value`` y otros en ``text``
        val = getattr(ctrl, "value", None) or getattr(ctrl, "text", None)
        if isinstance(val, str):
            texts.append(val)

    # Explorar atributos típicos que contienen hijos
    for attr in ("controls", "content"):
        if hasattr(ctrl, attr):
            child = getattr(ctrl, attr)
            if child is None:
                continue
            if isinstance(child, list):
                for c in child:
                    texts.extend(_extract_text_values(c))
            else:
                texts.extend(_extract_text_values(child))
    return texts


def test_loan_view_filters_bikes_by_admin_station():  # noqa: D401
    """LoanView solo debe mostrar bicicletas cuya estación coincide con la asignada."""

    # ------------------------------
    # Preparar BD en memoria
    # ------------------------------
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = TestingSessionLocal()

    # Crear estaciones
    est1 = Station(code="EST001", name="Calle 26")
    est2 = Station(code="EST002", name="Otra")
    db.add_all([est1, est2])
    db.commit()

    # Crear bicicletas disponibles en ambas estaciones
    bike1 = Bicycle(
        serial_number="S001",
        bike_code="B001",
        status=BikeStatusEnum.disponible,
        current_station=est1,
    )
    bike2 = Bicycle(
        serial_number="S002",
        bike_code="B002",
        status=BikeStatusEnum.disponible,
        current_station=est2,
    )
    db.add_all([bike1, bike2])
    db.commit()

    # Parchear el SessionLocal usado por el proyecto
    database.SessionLocal = TestingSessionLocal  # type: ignore

    # ------------------------------
    # Inicializar la app y vista
    # ------------------------------
    app = VeciRunApp()
    app.db = db  # Reemplazar la sesión por la de pruebas
    app.current_user_station = "EST001"  # Simular admin en estación EST001

    # Dummy page para métodos update()
    dummy_page = types.SimpleNamespace(update=lambda *_, **__: None)
    app.content_area = types.SimpleNamespace(content=None)

    # Renderizar la vista de préstamo
    app.refresh_loan_view(dummy_page)

    # Extraer los códigos de bicicletas mostrados en la UI
    loan_view_control = app.content_area.content
    text_values = _extract_text_values(loan_view_control)

    # Filtrar posibles textos que sean códigos de bicicleta ("B###")
    bike_codes_in_ui = {t for t in text_values if t.startswith("B")}

    assert "B001" in bike_codes_in_ui, "La bicicleta de la estación asignada debe mostrarse"
    assert "B002" not in bike_codes_in_ui, "Las bicicletas de otras estaciones no deben mostrarse" 