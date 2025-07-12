import types
import pytest

# Import the target app after patching flet.ElevatedButton to a lightweight stub
import flet as ft

class _DummyElevatedButton:
    """Lightweight stub that simply stores the most recent on_click callback."""

    last_callback = None  # class-level reference to latest provided callback

    def __init__(self, *args, on_click=None, **kwargs):
        # Save callback both on the instance and at class level for easy retrieval
        self.on_click = on_click
        _DummyElevatedButton.last_callback = on_click

# Apply monkeypatch at import-time so main.py uses the stub
ft.ElevatedButton = _DummyElevatedButton  # type: ignore

from main import VeciRunApp  # noqa: E402  (import after patching ft)


def test_register_loan_callback_no_unbound_error():
    """Ensure that executing the register_loan callback does not raise UnboundLocalError."""

    # -- Arrange --
    app = VeciRunApp()

    # Minimal dummy page object with an update method (called inside refresh_loan_view)
    dummy_page = types.SimpleNamespace(update=lambda *args, **kwargs: None)

    # Provide a dummy content_area so refresh_loan_view can assign to it when run outside Flet
    app.content_area = types.SimpleNamespace(content=None)

    # Render the loan view; this will create the _DummyElevatedButton and store the callback
    app.refresh_loan_view(dummy_page)

    # Retrieve the callback stored by the stub button
    callback = ft.ElevatedButton.last_callback  # type: ignore

    # Sanity check: callback should be callable
    assert callable(callback)

    # -- Act & Assert --
    # Executing the callback should NOT raise UnboundLocalError (or any other exception) now
    try:
        callback(None)  # Pass dummy event
    except UnboundLocalError as exc:
        pytest.fail(f"UnboundLocalError raised: {exc}") 