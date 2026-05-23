"""Auto-generador de plano de despiece de zapatas RC.

Produce:
    - Vista en planta con malla de armadura inferior y superior
    - Seccion tipica con armadura visible
    - Planilla de cantidades
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from .exceptions import DependencyError

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError as exc:  # pragma: no cover
    raise DependencyError("ezdxf requerido: pip install ezdxf") from exc

from .core import DXFDocument
from .column_rebar_detail import ColumnRebarBar, _place_text


@dataclass
class FootingRebarDetail:
    name: str
    Lx_mm: float
    Ly_mm: float
    h_mm: float
    cover_mm: float = 50.0
    bottom_x: ColumnRebarBar | None = None
    bottom_y: ColumnRebarBar | None = None
    top_x: ColumnRebarBar | None = None
    top_y: ColumnRebarBar | None = None
    column_b_mm: float = 400.0
    column_h_mm: float = 400.0
    project: str = ""


def render_footing_rebar_detail(detail: FootingRebarDetail,
                                path: str | Path) -> Path:
    path = Path(path)
    doc = DXFDocument(str(path))
    msp = doc._msp
    _draw_plan(msp, detail, x0=0, y0=0)
    _draw_section(msp, detail, x0=detail.Lx_mm + 800, y0=0)
    _draw_schedule(
        msp, detail,
        x0=detail.Lx_mm + 800,
        y0=-(detail.h_mm + 800),
    )
    doc.save()
    return path


def _bar_x_positions(L: float, cover: float, n: int) -> list[float]:
    if n <= 0:
        return []
    if n == 1:
        return [L / 2]
    step = (L - 2 * cover) / (n - 1)
    return [cover + i * step for i in range(n)]


def _draw_plan(msp, d: FootingRebarDetail, x0: float, y0: float) -> None:
    msp.add_lwpolyline(
        [(x0, y0), (x0 + d.Lx_mm, y0),
         (x0 + d.Lx_mm, y0 + d.Ly_mm),
         (x0, y0 + d.Ly_mm), (x0, y0)],
        close=True, dxfattribs={"layer": "CONCRETO"},
    )
    cx = x0 + d.Lx_mm / 2 - d.column_b_mm / 2
    cy = y0 + d.Ly_mm / 2 - d.column_h_mm / 2
    msp.add_lwpolyline(
        [(cx, cy), (cx + d.column_b_mm, cy),
         (cx + d.column_b_mm, cy + d.column_h_mm),
         (cx, cy + d.column_h_mm), (cx, cy)],
        close=True, dxfattribs={"layer": "CONCRETO", "color": 5},
    )
    if d.bottom_x:
        for xp in _bar_x_positions(d.Lx_mm, d.cover_mm, d.bottom_x.quantity):
            msp.add_line(
                (x0 + xp, y0 + d.cover_mm),
                (x0 + xp, y0 + d.Ly_mm - d.cover_mm),
                dxfattribs={"layer": "ARMADURA", "color": 1},
            )
    if d.bottom_y:
        for yp in _bar_x_positions(d.Ly_mm, d.cover_mm, d.bottom_y.quantity):
            msp.add_line(
                (x0 + d.cover_mm, y0 + yp),
                (x0 + d.Lx_mm - d.cover_mm, y0 + yp),
                dxfattribs={"layer": "ARMADURA", "color": 2},
            )
    _place_text(msp, "VISTA EN PLANTA",
                x0, y0 + d.Ly_mm + 200, height=200, layer="TEXTO")


def _draw_section(msp, d: FootingRebarDetail, x0: float, y0: float) -> None:
    msp.add_lwpolyline(
        [(x0, y0), (x0 + d.Lx_mm, y0),
         (x0 + d.Lx_mm, y0 + d.h_mm),
         (x0, y0 + d.h_mm), (x0, y0)],
        close=True, dxfattribs={"layer": "CONCRETO"},
    )
    if d.bottom_x:
        bd = d.bottom_x.diameter_mm
        for xp in _bar_x_positions(d.Lx_mm, d.cover_mm, d.bottom_x.quantity):
            msp.add_circle(
                (x0 + xp, y0 + d.cover_mm + bd / 2),
                radius=bd / 2,
                dxfattribs={"layer": "ARMADURA", "color": 1},
            )
    if d.top_x:
        bd = d.top_x.diameter_mm
        for xp in _bar_x_positions(d.Lx_mm, d.cover_mm, d.top_x.quantity):
            msp.add_circle(
                (x0 + xp, y0 + d.h_mm - d.cover_mm - bd / 2),
                radius=bd / 2,
                dxfattribs={"layer": "ARMADURA", "color": 3},
            )
    _place_text(msp, "SECCION A-A",
                x0, y0 + d.h_mm + 200, height=200, layer="TEXTO")


def _draw_schedule(msp, d: FootingRebarDetail,
                   x0: float, y0: float) -> None:
    header = ["POSICION", "MARCA", "D(mm)", "L(m)", "N", "kg"]
    rows: list[list[str]] = []
    total_kg = 0.0
    for label, bar in [("BOT-X", d.bottom_x), ("BOT-Y", d.bottom_y),
                       ("TOP-X", d.top_x), ("TOP-Y", d.top_y)]:
        if bar is None:
            continue
        rows.append([label, bar.mark, f"{int(bar.diameter_mm)}",
                     f"{bar.length_m:.2f}", str(bar.quantity),
                     f"{bar.weight_kg:.1f}"])
        total_kg += bar.weight_kg
    col_w = [800, 500, 500, 500, 400, 600]
    row_h = 200
    title_y = y0 + (len(rows) + 2) * row_h + 200
    _place_text(msp, f"PLANILLA ZAPATA {d.name}", x0, title_y,
                height=150, layer="TEXTO")
    y = title_y - 250
    x_acc = x0
    for i, h in enumerate(header):
        _place_text(msp, h, x_acc + 20, y, height=100, layer="TEXTO")
        msp.add_lwpolyline(
            [(x_acc, y - 50), (x_acc + col_w[i], y - 50),
             (x_acc + col_w[i], y + 150), (x_acc, y + 150),
             (x_acc, y - 50)],
            close=True, dxfattribs={"layer": "TEXTO"},
        )
        x_acc += col_w[i]
    for j, row in enumerate(rows):
        y_row = y - (j + 1) * row_h
        x_acc = x0
        for i, v in enumerate(row):
            _place_text(msp, v, x_acc + 20, y_row + 30,
                        height=80, layer="TEXTO")
            msp.add_lwpolyline(
                [(x_acc, y_row), (x_acc + col_w[i], y_row),
                 (x_acc + col_w[i], y_row + 150),
                 (x_acc, y_row + 150), (x_acc, y_row)],
                close=True, dxfattribs={"layer": "TEXTO"},
            )
            x_acc += col_w[i]
    y_tot = y - (len(rows) + 1) * row_h
    _place_text(msp, f"TOTAL = {total_kg:.1f} kg", x0, y_tot,
                height=120, layer="TEXTO")
