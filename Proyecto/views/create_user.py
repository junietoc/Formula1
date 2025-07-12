import flet as ft

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
        self.cedula_field = ft.TextField(
            label="Cédula",
            hint_text="Ingrese la cédula",
            width=300,
        )
        self.name_field = ft.TextField(
            label="Nombre Completo",
            hint_text="Ingrese el nombre completo",
            width=300,
        )
        self.email_field = ft.TextField(
            label="Email",
            hint_text="Ingrese el email",
            width=300,
        )

        self.affiliation_dropdown = ft.Dropdown(
            label="Afiliación",
            width=300,
            options=[
                ft.dropdown.Option("estudiante", "Estudiante"),
                ft.dropdown.Option("docente", "Docente"),
                ft.dropdown.Option("administrativo", "Administrativo"),
            ],
        )

        self.role_dropdown = ft.Dropdown(
            label="Rol",
            width=300,
            options=[
                ft.dropdown.Option("usuario", "Usuario"),
                ft.dropdown.Option("operador", "Operador"),
                ft.dropdown.Option("admin", "Administrador"),
            ],
            value="usuario",
        )

        self.result_text = ft.Text("", color=ft.colors.GREEN)

        create_button = ft.ElevatedButton(
            "Crear Usuario",
            on_click=self._create_user,
            style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.BLUE),
        )

        return ft.Column(
            [
                ft.Text("Crear Nuevo Usuario", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.cedula_field,
                self.name_field,
                self.email_field,
                self.affiliation_dropdown,
                self.role_dropdown,
                ft.Container(height=20),
                create_button,
                ft.Container(height=20),
                self.result_text,
            ],
            scroll=ft.ScrollMode.AUTO,
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
                role=UserRoleEnum(self.role_dropdown.value),
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
        self.role_dropdown.value = "usuario"
