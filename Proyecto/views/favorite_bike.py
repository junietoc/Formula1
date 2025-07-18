import flet as ft
from services import FavoriteBikeService, UserService
from models import UserRoleEnum
from .base import View


class FavoriteBikeView(View):
    """Vista para gestionar bicicletas favoritas de usuarios."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app
        self.current_user = getattr(self.app, "current_user", None)
        self.current_user_cedula = self.current_user.cedula if self.current_user else None

    def build(self) -> ft.Control:
        page = self.app.page
        db = self.app.db

        # Verificar si hay un usuario logueado
        if not self.current_user:
            return ft.Column(
                [
                    ft.Container(height=50),
                    ft.Text(
                        "Debe iniciar sesión para acceder a esta funcionalidad",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.RED_700,
                    ),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        text="Ir al Inicio",
                        icon=ft.icons.HOME,
                        on_click=lambda e: self.app.show_dashboard_view(),
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        page = self.app.page
        db = self.app.db

        # Título de la página
        title = ft.Text(
            "Mi Bicicleta Favorita",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.BLUE_900,
        )

        # Información del usuario actual
        user_info = ft.Text(
            f"Usuario: {self.current_user.full_name} - Cédula: {self.current_user.cedula}",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.colors.GREY_700,
        )

        # Contenedor para mostrar la bicicleta favorita actual
        self.favorite_bike_container = ft.Container(
            padding=20,
            content=ft.Text("Cargando...", color=ft.colors.GREY_600),
        )

        # Contenedor para mostrar las bicicletas disponibles para elegir
        self.available_bikes_container = ft.Container(
            padding=20,
            content=ft.Text("Cargando bicicletas disponibles...", color=ft.colors.GREY_600),
        )

        # Botón para quitar bicicleta favorita
        self.remove_favorite_button = ft.ElevatedButton(
            text="Quitar Bicicleta Favorita",
            icon=ft.icons.FAVORITE_BORDER,
            color=ft.colors.RED,
            on_click=self.remove_favorite_bike,
            visible=False,
        )

        # Cargar datos iniciales
        self.load_favorite_bike()
        self.load_available_bikes()

        return ft.Column(
            [
                ft.Container(height=20),
                title,
                ft.Container(height=10),
                user_info,
                ft.Container(height=20),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Bicicleta Favorita Actual",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE_700,
                                ),
                                ft.Container(height=10),
                                self.favorite_bike_container,
                                self.remove_favorite_button,
                            ]
                        ),
                        padding=20,
                    ),
                    elevation=4,
                ),
                ft.Container(height=20),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    "Bicicletas Disponibles para Elegir",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE_700,
                                ),
                                ft.Container(height=10),
                                ft.Text(
                                    "Solo puedes elegir entre las bicicletas que has usado anteriormente:",
                                    size=14,
                                    color=ft.colors.GREY_600,
                                ),
                                ft.Container(height=10),
                                self.available_bikes_container,
                            ]
                        ),
                        padding=20,
                    ),
                    elevation=4,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )

    def load_favorite_bike(self):
        """Cargar la bicicleta favorita actual del usuario"""
        if not self.current_user_cedula:
            self.favorite_bike_container.content = ft.Text(
                "No se pudo cargar la información del usuario",
                color=ft.colors.RED,
            )
            self.app.page.update()
            return

        db = self.app.db
        favorite_bike = FavoriteBikeService.get_user_favorite_bike_by_cedula(db, self.current_user_cedula)

        if favorite_bike:
            # Mostrar información de la bicicleta favorita
            station_info = f"Estación: {favorite_bike.current_station.code} - {favorite_bike.current_station.name}" if favorite_bike.current_station else "Estación: No disponible"
            
            self.favorite_bike_container.content = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.icons.FAVORITE, color=ft.colors.RED, size=24),
                            ft.Text(
                                f"Bicicleta {favorite_bike.bike_code}",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.colors.GREEN_700,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Text(f"Serie: {favorite_bike.serial_number}", size=14),
                    ft.Text(station_info, size=14),
                    ft.Text(f"Estado: {favorite_bike.status.value.title()}", size=14),
                ],
                spacing=8,
            )
            self.remove_favorite_button.visible = True
        else:
            # No tiene bicicleta favorita
            self.favorite_bike_container.content = ft.Column(
                [
                    ft.Icon(ft.icons.FAVORITE_BORDER, color=ft.colors.GREY, size=48),
                    ft.Text(
                        "No tienes una bicicleta favorita seleccionada",
                        size=16,
                        color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        "Elige una de las bicicletas que has usado anteriormente",
                        size=14,
                        color=ft.colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )
            self.remove_favorite_button.visible = False

        self.app.page.update()

    def load_available_bikes(self):
        """Cargar las bicicletas disponibles para elegir como favorita"""
        if not self.current_user_cedula:
            self.available_bikes_container.content = ft.Text(
                "No se pudo cargar la información del usuario",
                color=ft.colors.RED,
            )
            self.app.page.update()
            return

        db = self.app.db
        used_bikes = FavoriteBikeService.get_bikes_used_by_user_cedula(db, self.current_user_cedula)
        current_favorite = FavoriteBikeService.get_user_favorite_bike_by_cedula(db, self.current_user_cedula)

        if not used_bikes:
            self.available_bikes_container.content = ft.Column(
                [
                    ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.GREY, size=48),
                    ft.Text(
                        "No has usado ninguna bicicleta aún",
                        size=16,
                        color=ft.colors.GREY_600,
                    ),
                    ft.Text(
                        "Necesitas usar una bicicleta antes de poder elegirla como favorita",
                        size=14,
                        color=ft.colors.GREY_500,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )
        else:
            bike_cards = []
            for bike in used_bikes:
                # Verificar si la bicicleta ya es favorita de alguien
                is_favorite_of_other = FavoriteBikeService.is_bike_favorite(db, bike.id)
                is_current_favorite = current_favorite and current_favorite.id == bike.id
                
                # Determinar si se puede seleccionar
                can_select = not is_favorite_of_other or is_current_favorite
                
                # Información de la estación
                station_info = f"Estación: {bike.current_station.code} - {bike.current_station.name}" if bike.current_station else "Estación: No disponible"
                
                # Estado del botón
                button_text = "Ya es tu favorita" if is_current_favorite else "Elegir como favorita"
                button_color = ft.colors.GREEN if is_current_favorite else ft.colors.BLUE
                button_disabled = not can_select or is_current_favorite
                
                # Mensaje de estado
                status_text = ""
                if is_current_favorite:
                    status_text = "✓ Tu bicicleta favorita"
                elif is_favorite_of_other:
                    status_text = "✗ Favorita de otro usuario"
                else:
                    status_text = "Disponible para elegir"

                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Row(
                                    [
                                        ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.BLUE_700, size=24),
                                        ft.Text(
                                            f"Bicicleta {bike.bike_code}",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                        ),
                                    ],
                                    spacing=10,
                                ),
                                ft.Text(f"Serie: {bike.serial_number}", size=14),
                                ft.Text(station_info, size=14),
                                ft.Text(f"Estado: {bike.status.value.title()}", size=14),
                                ft.Text(status_text, size=12, color=ft.colors.GREY_600),
                                ft.Container(height=10),
                                ft.ElevatedButton(
                                    text=button_text,
                                    icon=ft.icons.FAVORITE if is_current_favorite else ft.icons.FAVORITE_BORDER,
                                    color=button_color,
                                    disabled=button_disabled,
                                    on_click=lambda e, b=bike: self.set_favorite_bike(b) if not is_current_favorite else None,
                                ),
                            ],
                            spacing=8,
                        ),
                        padding=15,
                    ),
                    elevation=2,
                )
                bike_cards.append(card)

            self.available_bikes_container.content = ft.Column(
                bike_cards,
                spacing=10,
            )

        self.app.page.update()

    def set_favorite_bike(self, bike):
        """Establecer una bicicleta como favorita"""
        if not self.current_user_cedula:
            return

        db = self.app.db
        success = FavoriteBikeService.set_favorite_bike_by_cedula(db, self.current_user_cedula, bike.id)

        if success:
            # Mostrar mensaje de éxito
            self.app.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"¡Bicicleta {bike.bike_code} establecida como favorita!"),
                    action="OK",
                    action_color=ft.colors.GREEN,
                )
            )
            # Recargar datos
            self.load_favorite_bike()
            self.load_available_bikes()
        else:
            # Mostrar mensaje de error
            self.app.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("No se pudo establecer la bicicleta como favorita. Verifica que no sea favorita de otro usuario."),
                    action="OK",
                    action_color=ft.colors.RED,
                )
            )

    def remove_favorite_bike(self, e):
        """Quitar la bicicleta favorita actual"""
        if not self.current_user_cedula:
            return

        db = self.app.db
        success = FavoriteBikeService.remove_favorite_bike_by_cedula(db, self.current_user_cedula)

        if success:
            # Mostrar mensaje de éxito
            self.app.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Bicicleta favorita removida exitosamente"),
                    action="OK",
                    action_color=ft.colors.GREEN,
                )
            )
            # Recargar datos
            self.load_favorite_bike()
            self.load_available_bikes()
        else:
            # Mostrar mensaje de error
            self.app.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("No se pudo remover la bicicleta favorita"),
                    action="OK",
                    action_color=ft.colors.RED,
                )
            ) 