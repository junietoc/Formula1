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
from .base import View


class CurrentLoanView(View):
    """View that lets a *regular* user check their active loan(s)."""

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
        # No active loans – return friendly message
        # ------------------------------------------------------------------
        if not open_loans:
            return ft.Column(
                [
                    ft.Text(
                        "No tienes préstamos vigentes.",
                        size=18,
                        color=ft.colors.GREY_700,
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )

        # ------------------------------------------------------------------
        # Build list of current loans (should usually be 0 or 1)
        # ------------------------------------------------------------------
        loan_tiles: list[ft.Control] = []
        for loan in open_loans:
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

            tile = ft.ListTile(
                leading=ft.Icon(ft.icons.DIRECTIONS_BIKE, color=ft.colors.BLUE),
                title=ft.Text(f"Bicicleta: {bike_code}"),
                subtitle=ft.Text(
                    f"Salida: {station_out} | Hora: {time_out_str}",
                ),
                trailing=ft.Column(
                    [
                        ft.Text("Destino:"),
                        ft.Text(dest_station, weight=ft.FontWeight.BOLD),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
            )
            loan_tiles.append(tile)

        return ft.Column(
            [
                ft.Text(
                    "Préstamo(s) vigente(s)",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                ft.Column(
                    loan_tiles,
                    spacing=5,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        ) 