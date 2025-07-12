from abc import ABC, abstractmethod
import flet as ft

class View(ABC):
    """Clase base que define la interfaz de todas las vistas.

    Cada vista debe implementar el método `build` y devolver un objeto
    `ft.Control` que será colocado dentro del contenedor principal del
    aplicativo (VeciRunApp.content_area).
    """

    @abstractmethod
    def build(self) -> ft.Control:  # noqa: D401
        """Construye y devuelve el contenido Flet para la vista."""
        raise NotImplementedError 