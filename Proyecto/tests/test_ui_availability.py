import importlib
import types

import flet as ft
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Station, Bicycle, BikeStatusEnum

# ---------------------------------------------------------------------------
# Stubs & helpers
# ---------------------------------------------------------------------------


class _DummyElevatedButton:  # noqa: D101 – simple stub
    """Lightweight replacement that stores the *on_click* callback provided."""

    last_callback = None  # type: ignore

    def __init__(self, *args, on_click=None, **kwargs):  # noqa: D401
        self.on_click = on_click
        _DummyElevatedButton.last_callback = on_click


class _ImmediateTimer:  # noqa: D101 – executes the callback right away
    """Replacement for *threading.Timer* that runs the function synchronously."""

    def __init__(self, _interval, function):  # noqa: D401
        self.function = function

    def start(self):  # noqa: D401
        self.function()


# Patch *ft.ElevatedButton* globally before importing the view module so that the
# view uses the stub instead of the real control (avoids heavy Flet deps).
ft.ElevatedButton = _DummyElevatedButton  # type: ignore

# Import the AvailabilityView **after** patching so it picks up the stub.
av_module = importlib.import_module("views.availability")
# Monkey-patch the *Timer* used inside the module so overlay animations execute
# instantly in the tests.
av_module.Timer = _ImmediateTimer  # type: ignore

AvailabilityView = av_module.AvailabilityView  # convenience alias


# ---------------------------------------------------------------------------
# Dummy application & page objects
# ---------------------------------------------------------------------------


class DummyPage:  # noqa: D101 – minimal stub
    def update(self):  # noqa: D401
        pass


class DummyApp:  # noqa: D101 – exposes only the attributes the view needs
    def __init__(self, db_session):  # noqa: D401
        self.db = db_session
        self.page = DummyPage()
        self.content_area = ft.Container()


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def db_session():  # noqa: D401
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _create_station_with_bikes(db, code: str, bike_qty: int = 0):  # noqa: D401
    """Helper that persists a station (and *bike_qty* available bikes)"""

    station = Station(code=code, name=f"Estación {code[-3:]}")
    db.add(station)
    db.commit()
    db.refresh(station)

    for idx in range(bike_qty):
        bike = Bicycle(
            serial_number=f"SN-{code}-{idx}",
            bike_code=f"B{code[-3:]}{idx}",
            status=BikeStatusEnum.disponible,
            current_station=station,
        )
        db.add(bike)
    db.commit()
    return station


@pytest.fixture(scope="function")
def app(db_session):  # noqa: D401
    return DummyApp(db_session)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_map_contains_expected_pins(db_session, app):  # noqa: D401
    """The map must render the five predefined pins with correct station codes."""

    expected_codes = {"EST001", "EST002", "EST003", "EST004", "EST005"}
    # Persist stations so *AvailabilityView* finds them in the DB (bike counts are irrelevant here)
    for code in expected_codes:
        _create_station_with_bikes(db_session, code)

    view = AvailabilityView(app)
    root_control = view.build()

    # root_control is a Stack with a single Column as its first control
    content_column = root_control.controls[0]
    # The map stack is the sixth element inside the column (index 5)
    map_stack = content_column.controls[5]

    # Pins are controls 1-5 inside the stack (0 = image, -1 = overlay)
    pin_codes = {c.data for c in map_stack.controls[1:-1]}
    assert pin_codes == expected_codes, "Los pines en el mapa no coinciden con los códigos esperados"


def test_overlay_shows_station_info_on_pin_click(db_session, app):  # noqa: D401
    """Clicking a pin should display an overlay with station info and bike count."""

    # Create one station with two available bikes
    _create_station_with_bikes(db_session, "EST001", bike_qty=2)

    view = AvailabilityView(app)
    root_control = view.build()

    content_column = root_control.controls[0]
    map_stack = content_column.controls[5]

    pin = map_stack.controls[1]  # First pin corresponds to EST001
    overlay = map_stack.controls[-1]  # The overlay Card is the last control

    # Pre-condition: overlay hidden
    assert overlay.visible is False

    # Simulate the click event (provide a minimal event object with .control attribute)
    event = types.SimpleNamespace(control=pin)
    pin.on_click(event)

    # Post-condition: overlay should now be visible with station details
    assert overlay.visible is True, "El overlay no se hizo visible tras el clic en el pin"

    # The first child inside the Column is a ListTile with the station name & code
    list_tile = overlay.content.content.controls[0]
    station_name = list_tile.title.value  # type: ignore
    station_code_text = list_tile.subtitle.value  # type: ignore

    assert "EST001" in station_code_text, "El código de estación no aparece en el overlay"
    assert station_name.startswith("Estación"), "El nombre de la estación no es correcto"

    # Bike count text should mention "2 bicicletas disponibles"
    bike_count_row = overlay.content.content.controls[1].content  # Container -> Row
    count_text = bike_count_row.controls[1].value  # Text control inside the row
    assert "2 bicicletas disponibles" in count_text, "El número de bicicletas disponibles es incorrecto"


def test_refresh_button_reloads_view(db_session, app):  # noqa: D401
    """The *Actualizar* button must rebuild the view and replace *content_area.content*."""

    _create_station_with_bikes(db_session, "EST001")

    view = AvailabilityView(app)
    view.build()

    # Dependemos de que otros tests puedan haber parcheado ``ft.ElevatedButton`` a otro
    # stub distinto. Para ser robustos recuperamos el callback desde la clase que esté
    # actualmente asignada en *ft.ElevatedButton*.
    refresh_callback = getattr(ft.ElevatedButton, "last_callback", None)  # type: ignore
    assert callable(refresh_callback), "No se capturó el callback del botón de refresco"

    # Execute the callback (simulate button press)
    refresh_callback(None)

    # The content area of the app should now contain a freshly built AvailabilityView (ft.Stack)
    assert isinstance(app.content_area.content, ft.Stack), "La vista no se recargó correctamente tras presionar Actualizar" 