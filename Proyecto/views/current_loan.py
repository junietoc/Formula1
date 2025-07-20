from __future__ import annotations

import flet as ft

# -------------------------------------------------------------------
# Optional integration with *flet-material* for consistent styling
# -------------------------------------------------------------------
try:
    import flet_material as fm  # type: ignore
except ModuleNotFoundError:  # CI or environments without flet-material
    class _FMStub:  # noqa: D101
        pass

    fm = _FMStub()  # type: ignore

from services import LoanService
from models import LoanStatusEnum
from .base import View


class CurrentLoanView(View):
    """View that lets a *regular* user check their active loan."""

    def __init__(self, app: "VeciRunApp") -> None:  # noqa: F821
        self.app = app

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build(self) -> ft.Control:  # noqa: D401
        db = self.app.db

        # ------------------------------------------------------------------
        # Mostrar TODOS los préstamos (historial completo) del usuario
        # ------------------------------------------------------------------
        from datetime import datetime

        user = getattr(self.app, "current_user", None)
        if user is None:
            return ft.Text("Error: ningún usuario autenticado.", color=ft.colors.RED, size=16)

        # Obtener el historial completo de préstamos (abiertos y cerrados)
        loans = LoanService.get_loans_by_user(db, user.id)

        # ------------------------------------------------------------------
        # Sin préstamos registrados
        # ------------------------------------------------------------------
        if not loans:
            return ft.Column(
                [
                    ft.Icon(ft.icons.DIRECTIONS_BIKE, size=64, color=ft.colors.GREY_400),
                    ft.Text(
                        "No tienes préstamos registrados",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.GREY_700,
                    ),
                    ft.Text(
                        "Cuando solicites tu primera bicicleta, aparecerá aquí.",
                        size=16,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )

        # Colores asociados a cada estado de préstamo
        status_colors = {
            LoanStatusEnum.abierto: ft.colors.GREEN,
            LoanStatusEnum.cerrado: ft.colors.BLUE,
            LoanStatusEnum.tardio: ft.colors.ORANGE,
            LoanStatusEnum.perdido: ft.colors.RED,
        }

        # --------------------------------------------------
        # Helper para construir una tarjeta de préstamo
        # --------------------------------------------------
        def build_loan_card(loan):
            bike_code = loan.bike.bike_code if loan.bike else "N/A"
            station_out = (
                f"{loan.station_out.code} - {loan.station_out.name}" if loan.station_out else "N/A"
            )
            station_in = (
                f"{loan.station_in.code} - {loan.station_in.name}" if loan.station_in else "Pendiente"
            )

            time_out_str = loan.time_out.strftime("%d/%m/%Y %H:%M") if loan.time_out else "N/A"
            time_in_str = loan.time_in.strftime("%d/%m/%Y %H:%M") if loan.time_in else "Pendiente"

            # Duración
            if loan.status == LoanStatusEnum.abierto and loan.time_out:
                delta = datetime.now() - loan.time_out
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
            elif loan.time_in and loan.time_out:
                delta = loan.time_in - loan.time_out
                hours = int(delta.total_seconds() // 3600)
                minutes = int((delta.total_seconds() % 3600) // 60)
                duration_str = f"{hours}h {minutes}m"
            else:
                duration_str = "N/A"

            status_text = loan.status.value.title()
            status_color = status_colors.get(loan.status, ft.colors.GREY)

            return ft.Card(
                content=ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.BLUE),
                                    ft.Text(
                                        f"Bicicleta: {bike_code}",
                                        weight=ft.FontWeight.BOLD,
                                        size=16,
                                    ),
                                    ft.Container(expand=True),
                                    ft.Container(
                                        content=ft.Text(status_text, color=ft.colors.WHITE),
                                        bgcolor=status_color,
                                        padding=ft.padding.all(8),
                                        border_radius=ft.border_radius.all(12),
                                    ),
                                ]
                            ),
                            ft.Divider(),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Estación de salida:", weight=ft.FontWeight.BOLD),
                                            ft.Text(station_out),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Estación de llegada:", weight=ft.FontWeight.BOLD),
                                            ft.Text(station_in),
                                        ],
                                        expand=True,
                                    ),
                                ]
                            ),
                            ft.Row(
                                [
                                    ft.Column(
                                        [
                                            ft.Text("Fecha de salida:", weight=ft.FontWeight.BOLD),
                                            ft.Text(time_out_str),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Fecha de llegada:", weight=ft.FontWeight.BOLD),
                                            ft.Text(time_in_str),
                                        ],
                                        expand=True,
                                    ),
                                    ft.Column(
                                        [
                                            ft.Text("Duración:", weight=ft.FontWeight.BOLD),
                                            ft.Text(duration_str),
                                        ],
                                        expand=True,
                                    ),
                                ]
                            ),
                        ]
                    ),
                    padding=ft.padding.all(16),
                ),
                margin=ft.margin.only(bottom=10),
            )

        # --------------------------------------------------
        # Separar préstamos actuales y pasados
        # --------------------------------------------------
        open_loans = [ln for ln in loans if ln.status == LoanStatusEnum.abierto]
        past_loans = [ln for ln in loans if ln.status != LoanStatusEnum.abierto]

        # --------------------------------------------------
        # Sección "Préstamo Actual"
        # --------------------------------------------------
        if open_loans:
            current_section = [build_loan_card(open_loans[0])]
        else:
            current_section = [
                ft.Container(
                    content=ft.Text(
                        "No hay ningún préstamo activo",
                        size=16,
                        color=ft.colors.GREY_600,
                    ),
                    padding=ft.padding.all(12),
                )
            ]

        # --------------------------------------------------
        # Sección "Préstamos Pasados"
        # --------------------------------------------------
        past_cards = [build_loan_card(ln) for ln in past_loans] if past_loans else [
            ft.Text("No hay préstamos pasados", size=16, color=ft.colors.GREY_600)
        ]

        return ft.Column(
            [
                # Header y contenido del préstamo actual
                ft.Text(
                    "Préstamo Actual",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_700,
                ),
                ft.Divider(),
                *current_section,
                ft.Container(height=20),
                # Header y contenido de préstamos pasados
                ft.Text(
                    "Préstamos Pasados",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_700,
                ),
                ft.Divider(),
                ft.Column(past_cards, spacing=10),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ) 