"""
foundation_plan.py — Isolated footing plan DXF detail.
"""
from __future__ import annotations
from dataclasses import dataclass, field
import math
from .core import DXFDocument, Layer
from rebardxf._common.audit_status import CalculationStatus


@dataclass
class FootingData:
    """Single footing data for plan drawing.

    Parameters
    ----------
    label : str
        Footing label (e.g. 'Z-1').
    x, y : float
        Footing center coordinates in plan [mm].
    B, L, d : float
        Footing width (X), length (Y), and total depth [mm].
    As_x : float | None
        Required flexural steel per unit width in x-dir [mm²/m]. None -> NO_CALCULADO.
    As_y : float | None
        Required flexural steel per unit width in y-dir [mm²/m]. None -> NO_CALCULADO.
    db : float | None
        Bar diameter [mm]. None -> As reported but diameter undefined.
    fc : float | None
        Concrete compressive strength [MPa].
    Fy : float | None
        Steel yield strength [MPa].
    status : CalculationStatus
        Status of reinforcement calculation.
    design_code : str
        Standard for spacing limits: 'ACI318-19' (default) or 'EC2'.
    cover_mm : float
        Clear concrete cover [mm]. Default 75.0 mm per ACI 318-19 Table 20.5.1.3.1
        (cast against and permanently exposed to earth).
    d_agg_mm : float | None
        Nominal maximum aggregate size [mm]. None -> limitation declared,
        s_min uses bar-only clearance.
    s_max_override_mm : float | None
        Manual override for maximum bar spacing [mm].
    s_min_override_mm : float | None
        Manual override for minimum bar spacing [mm].
    s_commercial_step_mm : float
        Commercial spacing rounding step [mm]. Default 25.0 mm.
    notes : str
        Diagnostic notes or reasons for revision.
    """
    label: str
    x: float
    y: float
    B: float
    L: float
    d: float
    As_x: float | None = None
    As_y: float | None = None
    db: float | None = None
    fc: float | None = None
    Fy: float | None = None
    #: SIN default favorable a proposito. Tenerlo en `CALCULADO_CUMPLE` era la
    #: misma "omision = cumplimiento" que la Proof Obligation prohibe, escrita
    #: como default de dataclass: `FootingData` no se construye en produccion --es
    #: API PUBLICA de dibujo-- asi que cualquier consumidor que la instanciara con
    #: su armado obtenia un veredicto favorable sin haber auditado nada. Un objeto
    #: de dibujo describe QUE se dibuja; no acredita que el calculo se hiciera.
    #: `draw_foundation_plan` declara el estado explicitamente tras comprobar.
    status: CalculationStatus = CalculationStatus.NO_CALCULADO
    design_code: str = "ACI318-19"
    cover_mm: float = 75.0
    d_agg_mm: float | None = None
    s_max_override_mm: float | None = None
    s_min_override_mm: float | None = None
    s_commercial_step_mm: float = 25.0
    snap_to_commercial_step: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if self.As_x is None or self.As_y is None:
            self.status = CalculationStatus.NO_CALCULADO
            self.notes = "NO CALCULADO — ARMADO NO DEFINIDO"
        elif self.db is None:
            self.status = CalculationStatus.REQUIERE_REVISION
            self.notes = f"As={self.As_x:.0f}/{self.As_y:.0f} mm2/m — Ø NO DEFINIDO"


def layout_rebar_direction(
    dim_mm: float,
    depth_mm: float,
    As_mm2_m: float,
    db_mm: float,
    cover_mm: float,
    design_code: str = "ACI318-19",
    d_agg_mm: float | None = None,
    s_max_override_mm: float | None = None,
    s_min_override_mm: float | None = None,
    s_commercial_step_mm: float = 25.0,
    snap_to_commercial_step: bool = False,
) -> tuple[CalculationStatus, int, float, float, str]:
    """Calcula el despiece coordinado para una dirección de zapata.

    Retorna: (status, n_bars, s_dibujada_mm, s_rotulo_mm, reason)
    """
    if As_mm2_m <= 0 or db_mm <= 0:
        return CalculationStatus.NO_CALCULADO, 0, 0.0, 0.0, "Área o diámetro nulo"

    Ab = math.pi * (db_mm ** 2) / 4.0
    s_req = (Ab / As_mm2_m) * 1000.0

    # 1. Separación máxima (Decisión 1)
    if s_max_override_mm is not None:
        s_max = float(s_max_override_mm)
    elif design_code == "EC2":
        # EN 1992-1-1:2004 §9.3.1.1(3)
        s_max = min(3.0 * depth_mm, 400.0)
    else:
        # ACI 318-19 §13.3.2.1 / §7.7.2.3 / §8.7.2.2
        s_max = min(3.0 * depth_mm, 450.0)

    # 2. Separación mínima (Decisión 2)
    if s_min_override_mm is not None:
        s_min = float(s_min_override_mm)
    elif design_code == "EC2":
        # EN 1992-1-1:2004 §8.2: paso libre >= max(db, 20 mm, dg + 5 mm)
        clear_min = max(db_mm, 20.0)
        if d_agg_mm is not None:
            clear_min = max(clear_min, d_agg_mm + 5.0)
        s_min = db_mm + clear_min
    else:
        # ACI 318-19 §25.2.1: paso libre >= max(db, 25 mm, 4/3 d_agg)
        clear_min = max(db_mm, 25.0)
        if d_agg_mm is not None:
            clear_min = max(clear_min, (4.0 / 3.0) * d_agg_mm)
        s_min = db_mm + clear_min

    # Detección de imposibilidad (La trampa: no clampar con min/max)
    if s_req > s_max:
        return (
            CalculationStatus.REQUIERE_REVISION,
            0,
            s_req,
            s_max,
            f"s_req ({s_req:.0f}mm) > s_max ({s_max:.0f}mm) — aumentar db",
        )
    if s_req < s_min:
        return (
            CalculationStatus.REQUIERE_REVISION,
            0,
            s_req,
            s_min,
            f"s_req ({s_req:.0f}mm) < s_min ({s_min:.0f}mm) — congestión de armadura",
        )

    w_eff = dim_mm - 2.0 * cover_mm
    if w_eff <= 0:
        return (
            CalculationStatus.REQUIERE_REVISION,
            0,
            0.0,
            0.0,
            f"ancho útil <= 0 ({dim_mm}mm <= 2*{cover_mm}mm)",
        )

    # Número de espacios para que s_actual <= s_req (o al múltiplo comercial inferior si se activa)
    s_target = (
        math.floor(s_req / s_commercial_step_mm) * s_commercial_step_mm
        if (snap_to_commercial_step and s_commercial_step_mm > 0)
        else s_req
    )
    if s_target <= 0:
        s_target = s_req
    n_spaces = max(1, math.ceil(w_eff / s_target))
    n_bars = n_spaces + 1
    s_dib = w_eff / n_spaces
    s_rot = (
        float(math.floor(s_dib / s_commercial_step_mm) * s_commercial_step_mm)
        if (snap_to_commercial_step and s_commercial_step_mm > 0)
        else round(s_dib)
    )

    if s_dib < s_min:
        return (
            CalculationStatus.REQUIERE_REVISION,
            0,
            s_dib,
            s_min,
            f"s_dibujada ({s_dib:.0f}mm) < s_min ({s_min:.0f}mm)",
        )

    return CalculationStatus.CALCULADO_CUMPLE, n_bars, s_dib, float(s_rot), ""


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

            # Rebar evaluation and drawing
            # La condición mira los DATOS, no el estado. Antes decía
            # `f.status == NO_CALCULADO or f.As_x is None or f.As_y is None`, y las
            # dos mitades eran equivalentes: con el default del dataclass en
            # `CALCULADO_CUMPLE`, la única forma de llegar aquí en `NO_CALCULADO`
            # era que `__post_init__` lo hubiera puesto por ese mismo motivo --que
            # faltara As_x o As_y. Al quitar ese default favorable el estado nace
            # SIEMPRE en `NO_CALCULADO`, y esa mitad cortocircuitaba todos los
            # armados, incluidos los completos. Lo que decide si hay armado que
            # dibujar es si hay armado, y eso lo dice el dato.
            if f.As_x is None or f.As_y is None:
                doc.text((x0, y0 + f.L + 90),
                         "NO CALCULADO — ARMADO NO DEFINIDO",
                         height=25)
            elif f.db is None:
                f.status = CalculationStatus.REQUIERE_REVISION
                f.notes = f"As={f.As_x:.0f}/{f.As_y:.0f} mm2/m — Ø NO DEFINIDO"
                doc.text((x0, y0 + f.L + 90),
                         f"REQUIERE REVISION — {f.notes}",
                         height=25)
            else:
                st_x, nx, sx_dib, sx_rot, rx = layout_rebar_direction(
                    f.B, f.d, f.As_x, f.db, f.cover_mm, f.design_code,
                    f.d_agg_mm, f.s_max_override_mm, f.s_min_override_mm,
                    f.s_commercial_step_mm, f.snap_to_commercial_step,
                )
                st_y, ny, sy_dib, sy_rot, ry = layout_rebar_direction(
                    f.L, f.d, f.As_y, f.db, f.cover_mm, f.design_code,
                    f.d_agg_mm, f.s_max_override_mm, f.s_min_override_mm,
                    f.s_commercial_step_mm, f.snap_to_commercial_step,
                )

                if st_x == CalculationStatus.REQUIERE_REVISION or st_y == CalculationStatus.REQUIERE_REVISION:
                    f.status = CalculationStatus.REQUIERE_REVISION
                    reasons = [r for r in (rx, ry) if r]
                    f.notes = "; ".join(reasons)
                    doc.text((x0, y0 + f.L + 90),
                             f"REQUIERE REVISION — {f.notes}",
                             height=25)
                else:
                    f.status = CalculationStatus.CALCULADO_CUMPLE
                    if self.draw_rebar:
                        # X-direction bars (vertical lines distributed along B)
                        for i in range(nx):
                            xt = x0 + f.cover_mm + i * sx_dib
                            doc.line((xt, y0 + f.cover_mm), (xt, y0 + f.L - f.cover_mm),
                                     layer=Layer.REBAR, lineweight=0.15)
                        # Y-direction bars (horizontal lines distributed along L)
                        for j in range(ny):
                            yt = y0 + f.cover_mm + j * sy_dib
                            doc.line((x0 + f.cover_mm, yt), (x0 + f.B - f.cover_mm, yt),
                                     layer=Layer.REBAR, lineweight=0.15)
                    doc.text((x0, y0 + f.L + 90),
                             f"Ø{int(f.db)} c/{int(sx_rot)}+Ø{int(f.db)} c/{int(sy_rot)}",
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
            # La condición mira los DATOS, no el estado. Antes decía
            # `f.status == NO_CALCULADO or f.As_x is None or f.As_y is None`, y las
            # dos mitades eran equivalentes: con el default del dataclass en
            # `CALCULADO_CUMPLE`, la única forma de llegar aquí en `NO_CALCULADO`
            # era que `__post_init__` lo hubiera puesto por ese mismo motivo --que
            # faltara As_x o As_y. Al quitar ese default favorable el estado nace
            # SIEMPRE en `NO_CALCULADO`, y esa mitad cortocircuitaba todos los
            # armados, incluidos los completos. Lo que decide si hay armado que
            # dibujar es si hay armado, y eso lo dice el dato.
            if f.As_x is None or f.As_y is None:
                st = CalculationStatus.NO_CALCULADO
                notes = f.notes or "NO CALCULADO — ARMADO NO DEFINIDO"
            elif f.db is None:
                st = CalculationStatus.REQUIERE_REVISION
                notes = f"As={f.As_x:.0f}/{f.As_y:.0f} mm2/m — Ø NO DEFINIDO"
            else:
                st_x, nx, sx_dib, sx_rot, rx = layout_rebar_direction(
                    f.B, f.d, f.As_x, f.db, f.cover_mm, f.design_code,
                    f.d_agg_mm, f.s_max_override_mm, f.s_min_override_mm,
                    f.s_commercial_step_mm, f.snap_to_commercial_step,
                )
                st_y, ny, sy_dib, sy_rot, ry = layout_rebar_direction(
                    f.L, f.d, f.As_y, f.db, f.cover_mm, f.design_code,
                    f.d_agg_mm, f.s_max_override_mm, f.s_min_override_mm,
                    f.s_commercial_step_mm, f.snap_to_commercial_step,
                )
                if st_x == CalculationStatus.REQUIERE_REVISION or st_y == CalculationStatus.REQUIERE_REVISION:
                    st = CalculationStatus.REQUIERE_REVISION
                    notes = "; ".join([r for r in (rx, ry) if r])
                else:
                    st = CalculationStatus.CALCULADO_CUMPLE
                    notes = f.notes

            rows.append({
                "label": f.label,
                "B_m": round(f.B / 1000, 2),
                "L_m": round(f.L / 1000, 2),
                "d_m": round(f.d / 1000, 2),
                "As_x_mm2_m": round(f.As_x, 1) if f.As_x is not None else None,
                "As_y_mm2_m": round(f.As_y, 1) if f.As_y is not None else None,
                "db_mm": f.db if f.db is not None else None,
                "status": st.value if hasattr(st, "value") else str(st),
                "notes": notes,
            })
        return rows
