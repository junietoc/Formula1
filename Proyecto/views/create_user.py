import flet as ft

# ------------------------------------------
# Integración opcional con *flet-material*
# ------------------------------------------
try:
    import flet_material as fm  # type: ignore
except ModuleNotFoundError:  # Entorno sin flet-material (p.ej. CI)
    class _FMStub:  # noqa: D101
        class Buttons(ft.ElevatedButton):  # noqa: D101
            def __init__(self, *_, title: str = "", **kw):
                # Alineamos la API con flet-material: se puede pasar `title` o `text`.
                super().__init__(title or kw.pop("text", ""), **kw)

    fm = _FMStub()  # type: ignore

from models import UserRoleEnum, UserAffiliationEnum
from services import UserService

from .base import View


class CreateUserView(View):
    """Vista para la creación de un nuevo usuario (solo admins)."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        # Se pasa una referencia al objeto principal para acceder a db, page, etc.
        self.app = app

    # ---------------------------------------------------------------------
    # API pública
    # ---------------------------------------------------------------------
    def build(self) -> ft.Control:  # noqa: D401
        """Devuelve el contenido Flet para la creación de usuario."""
        page = self.app.page

        # ------------------------
        # Campos del formulario
        # ------------------------
        FIELD_W = 320

        self.cedula_field = ft.TextField(
            label="Cédula",
            hint_text="Ingrese la cédula",
            width=FIELD_W,
            prefix_icon=ft.icons.BADGE,
        )
        self.name_field = ft.TextField(
            label="Nombre Completo",
            hint_text="Ingrese el nombre completo",
            width=FIELD_W,
            prefix_icon=ft.icons.PERSON,
        )
        self.email_field = ft.TextField(
            label="Email",
            hint_text="Ingrese el email",
            width=FIELD_W,
            prefix_icon=ft.icons.EMAIL,
        )

        self.affiliation_dropdown = ft.Dropdown(
            label="Afiliación",
            width=FIELD_W,
            options=[
                ft.dropdown.Option("estudiante", "Estudiante"),
                ft.dropdown.Option("docente", "Docente"),
                ft.dropdown.Option("administrativo", "Administrativo"),
            ],
            prefix_icon=ft.icons.APARTMENT,
        )


        self.result_text = ft.Text("", color=ft.colors.GREEN, selectable=True)

        # ------------------------
        # Botón Crear (material o fallback)
        # ------------------------
        self.create_button = fm.Buttons(
            title="Crear Usuario",
            on_click=self._create_user,
            width=200,
            height=48,
        )

        # Deshabilitar inicialmente hasta que el formulario esté completo
        self.create_button.disabled = True
        self.create_button.style = ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREY_400)

        # --------------------------------------------------
        # Helper para habilitar / deshabilitar el botón
        # --------------------------------------------------

        def _update_create_button(_: ft.ControlEvent | None = None) -> None:  # noqa: D401
            complete = bool(
                self.cedula_field.value
                and self.name_field.value
                and self.email_field.value
                and self.affiliation_dropdown.value
            )
            self.create_button.disabled = not complete
            self.create_button.style = ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.GREEN if complete else ft.colors.GREY_400,
            )
            page.update()

        # Escuchar cambios en los campos
        for fld in [
            self.cedula_field,
            self.name_field,
            self.email_field,
            self.affiliation_dropdown,
        ]:
            fld.on_change = _update_create_button

        # ------------------------
        # Construir layout usando Card
        # ------------------------
        form_controls = ft.Column(
            [
                self.cedula_field,
                self.name_field,
                self.email_field,
                self.affiliation_dropdown,
                ft.Container(height=10),
                self.create_button,
            ],
            spacing=10,
        )

        form_card = ft.Card(
            elevation=2,
            content=ft.Container(content=form_controls, padding=20, width=FIELD_W + 40),
        )

        return ft.Column(
            [
                ft.Text("Crear Nuevo Usuario", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([form_card], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                self.result_text,
            ],
            scroll=ft.ScrollMode.AUTO,
            spacing=10,
        )

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _create_user(self, e: ft.ControlEvent) -> None:  # noqa: D401
        """Callback para el botón *Crear Usuario*."""
        page = self.app.page
        db = self.app.db

        try:
            # Validación mínima
            if not all(
                [
                    self.cedula_field.value,
                    self.name_field.value,
                    self.email_field.value,
                    self.affiliation_dropdown.value,
                ]
            ):
                self._set_result("Todos los campos son obligatorios", ft.colors.RED)
                return

            # Verificar duplicidad
            if UserService.get_user_by_cedula(db, self.cedula_field.value):
                self._set_result("Ya existe un usuario con esta cédula", ft.colors.RED)
                return

            # Crear usuario
            user = UserService.create_user(
                db,
                cedula=self.cedula_field.value,
                carnet="",  # carnet se genera automáticamente
                full_name=self.name_field.value,
                email=self.email_field.value,
                affiliation=UserAffiliationEnum(self.affiliation_dropdown.value),
                role=UserRoleEnum("usuario"), # Hard-code role to 'usuario'
            )

            self._set_result(f"Usuario creado exitosamente: {user.full_name}", ft.colors.GREEN)
            self._clear_fields()
        except Exception as ex:  # noqa: BLE001
            self._set_result(f"Error: {str(ex)}", ft.colors.RED)

        page.update()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _set_result(self, message: str, color: str) -> None:
        self.result_text.value = message
        self.result_text.color = color

    def _clear_fields(self) -> None:
        self.cedula_field.value = ""
        self.name_field.value = ""
        self.email_field.value = ""
        self.affiliation_dropdown.value = None
        # Deshabilitar botón hasta completar nuevamente el formulario
        if hasattr(self, "create_button"):
            self.create_button.disabled = True
            self.create_button.style = ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREY_400)
