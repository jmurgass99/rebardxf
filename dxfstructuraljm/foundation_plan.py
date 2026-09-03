"""
foundation_plan.py — Isolated footing plan DXF detail.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
from .core import DXFDocument, Layer
from jmstructural_common.audit_status import CalculationStatus


@dataclass
class FootingData:
    """Single footing data for plan drawing."""
    label: str        # 'Z-1'
    x: float          # center x in plan [mm]
    y: float          # center y in plan [mm]
    B: float          # width [mm]
    L: float          # length [mm]
    d: float          # depth [mm]
    As_x: float | None = None  # steel per unit width in x-dir [mm²/m]
    As_y: float | None = None  # steel per unit width in y-dir [mm²/m]
    db: float | None = None    # bar diameter [mm]
    fc: float | None = None
    Fy: float | None = None
    status: CalculationStatus = CalculationStatus.CALCULADO_CUMPLE

    def __post_init__(self) -> None:
        if self.As_x is None or self.As_y is None:
            self.status = CalculationStatus.NO_CALCULADO


@dataclass
class FoundationPlan:
    """
    Foundation plan DXF drawing with multiple isolated footings.

    Parameters
    ----------
    footings : list[FootingData]
    column_size : float  square column size [mm] (shown at centroid)
    draw_rebar : bool  draw rebar pattern inside footings
    """
    footings: list[FootingData]
    column_size: float = 400.0
    draw_rebar: bool = True

    def draw(self, output_path: str = "foundation_plan.dxf") -> DXFDocument:
        """Generate the foundation plan DXF."""
        doc = DXFDocument(output_path)

        for f in self.footings:
            # Footing outline
            x0 = f.x - f.B / 2
            y0 = f.y - f.L / 2
            doc.rectangle(x0, y0, f.B, f.L, layer=Layer.CONCRETE, lineweight=0.50)
            doc.hatch_concrete([
                (x0, y0), (x0 + f.B, y0),
                (x0 + f.B, y0 + f.L), (x0, y0 + f.L)
            ])

            # Column stub (at centroid)
            cs2 = self.column_size / 2
            doc.rectangle(f.x - cs2, f.y - cs2,
                          self.column_size, self.column_size,
                          layer=Layer.CONCRETE, lineweight=0.70)

            # Rebar pattern (simplified: lines across footing)
            if self.draw_rebar and f.status != CalculationStatus.NO_CALCULADO:
                cover = 75.0  # typical footing cover
                n_x = max(3, int(f.B / 200))   # one bar per 200mm approx
                n_y = max(3, int(f.L / 200))
                # X-direction bars (horizontal lines)
                for i in range(n_x):
                    xt = x0 + cover + i * (f.B - 2 * cover) / max(n_x - 1, 1)
                    doc.line((xt, y0 + cover), (xt, y0 + f.L - cover),
                             layer=Layer.REBAR, lineweight=0.15)
                # Y-direction bars (vertical lines)
                for j in range(n_y):
                    yt = y0 + cover + j * (f.L - 2 * cover) / max(n_y - 1, 1)
                    doc.line((x0 + cover, yt), (x0 + f.B - cover, yt),
                             layer=Layer.REBAR, lineweight=0.15)

            # Axis lines (cross at centroid)
            ax_len = max(f.B, f.L) * 0.6
            doc.line((f.x - ax_len, f.y), (f.x + ax_len, f.y),
                     layer=Layer.AXIS, lineweight=0.09)
            doc.line((f.x, f.y - ax_len), (f.x, f.y + ax_len),
                     layer=Layer.AXIS, lineweight=0.09)

            # Label
            doc.text((x0 + 30, y0 + f.L + 20), f.label, height=40)
            doc.text((x0, y0 + f.L + 60),
                     f"{f.B/1000:.2f}×{f.L/1000:.2f}×{f.d/1000:.2f}m",
                     height=30)
            # Rebar note
            if f.status == CalculationStatus.NO_CALCULADO:
                doc.text((x0, y0 + f.L + 90),
                         "NO CALCULADO — ARMADO NO DEFINIDO",
                         height=25)
            elif f.db is None:
                # El área SÍ se calculó pero el diámetro no se eligió. El
                # `else 16.0` que había aquí estampaba un Ø16 que nadie decidió
                # —el mismo literal recién eliminado de
                # `footing_drawings.py:48`— mientras el cuadro de zapatas decía
                # `db: None` tres centímetros más allá: el mismo documento
                # afirmando y negando el dato, y el dibujo es lo que lee quien
                # ferralla. Se rotula lo que SÍ se sabe.
                doc.text((x0, y0 + f.L + 90),
                         f"As={f.As_x:.0f}/{f.As_y:.0f} mm2/m — Ø NO DEFINIDO",
                         height=25)
            else:
                doc.text((x0, y0 + f.L + 90),
                         f"Ø{int(f.db)} c/{int(f.B/(int(f.B/200)+1))}+Ø{int(f.db)} c/{int(f.L/(int(f.L/200)+1))}",
                         height=25)

            # Dimension lines
            doc.dimension_linear((x0, y0 - 80), (x0 + f.B, y0 - 80),
                                  dim_line_offset=0)

        doc.save()
        return doc

    def schedule_table(self) -> list[dict]:
        """Return footing schedule table data."""
        rows = []
        for f in self.footings:
            rows.append({
                "label": f.label,
                "B_m": round(f.B / 1000, 2),
                "L_m": round(f.L / 1000, 2),
                "d_m": round(f.d / 1000, 2),
                "As_x_mm2_m": round(f.As_x, 1) if f.As_x is not None else None,
                "As_y_mm2_m": round(f.As_y, 1) if f.As_y is not None else None,
                "db_mm": f.db if f.db is not None else None,
                "status": f.status.value if hasattr(f.status, "value") else str(f.status),
            })
        return rows
