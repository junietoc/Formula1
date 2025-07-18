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
        page = self.app.page
        db = self.app.db

        user = getattr(self.app, "current_user", None)
        if user is None:
            # Guard-rail: should never happen for a regular user session
            return ft.Text("Error: ningún usuario autenticado.", color=ft.colors.RED, size=16)

        open_loans = LoanService.get_open_loans_by_user(db, user.id)

        # ------------------------------------------------------------------
        # No active loans – show message
        # ------------------------------------------------------------------
        if not open_loans:
            return ft.Column(
                [
                    ft.Icon(
                        ft.icons.DIRECTIONS_BIKE,
                        size=64,
                        color=ft.colors.GREY_400,
                    ),
                    ft.Text(
                        "No hay ningún préstamo activo",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.GREY_700,
                    ),
                    ft.Text(
                        "Actualmente no tienes ninguna bicicleta prestada.",
                        size=16,
                        color=ft.colors.GREY_600,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        "Para solicitar un préstamo, ve a la sección 'Solicitar Préstamo'.",
                        size=14,
                        color=ft.colors.GREY_500,
                        text_align=ft.TextAlign.CENTER,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )

        # ------------------------------------------------------------------
        # Show current active loan (should usually be 1)
        # ------------------------------------------------------------------
        loan = open_loans[0]  # Get the first (and should be only) active loan
        
        bike_code = loan.bike.bike_code if loan.bike else "-"
        station_out = (
            f"{loan.station_out.code} - {loan.station_out.name}"
            if loan.station_out
            else "-"
        )
        time_out_str = loan.time_out.strftime("%d/%m/%Y %H:%M") if loan.time_out else "-"
        dest_station = (
            f"{loan.station_in.code} - {loan.station_in.name}"
            if loan.station_in
            else "(por definir)"
        )

        # Calculate duration since loan started
        duration_str = "N/A"
        if loan.time_out:
            from datetime import datetime
            now = datetime.now()
            duration = now - loan.time_out
            hours = int(duration.total_seconds() // 3600)
            minutes = int((duration.total_seconds() % 3600) // 60)
            duration_str = f"{hours}h {minutes}m"

        return ft.Column(
            [
                ft.Text(
                    "Mi Préstamo Actual",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_700,
                ),
                ft.Divider(),
                ft.Container(
                    content=ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.BLUE, size=32),
                                    ft.Text(
                                        f"Bicicleta: {bike_code}",
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.BLUE_700,
                                    ),
                                ]),
                                ft.Divider(),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("Estación de Salida:", weight=ft.FontWeight.BOLD, size=14),
                                        ft.Text(station_out, size=16),
                                    ], expand=True),
                                    ft.Column([
                                        ft.Text("Estación de Destino:", weight=ft.FontWeight.BOLD, size=14),
                                        ft.Text(dest_station, size=16),
                                    ], expand=True),
                                ]),
                                ft.Divider(),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("Fecha y Hora de Salida:", weight=ft.FontWeight.BOLD, size=14),
                                        ft.Text(time_out_str, size=16),
                                    ], expand=True),
                                    ft.Column([
                                        ft.Text("Tiempo Transcurrido:", weight=ft.FontWeight.BOLD, size=14),
                                        ft.Text(duration_str, size=16, color=ft.colors.ORANGE_700),
                                    ], expand=True),
                                ]),
                                ft.Container(height=20),
                                ft.Container(
                                    content=ft.Text(
                                        "Para devolver la bicicleta, ve a la sección 'Registrar Devolución'",
                                        size=14,
                                        color=ft.colors.GREY_600,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    bgcolor=ft.colors.GREY_100,
                                    padding=ft.padding.all(12),
                                    border_radius=ft.border_radius.all(8),
                                ),
                            ]),
                            padding=ft.padding.all(20),
                        ),
                        elevation=8,
                    ),
                    margin=ft.margin.only(bottom=20),
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ) 