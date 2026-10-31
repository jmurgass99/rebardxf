"""Auto-generador de plano de despiece de armadura para columnas RC.

Produce un layout DXF completo con:
    - Vista en alzado (columna entera mostrando longitudes de barras)
    - Sección transversal en base, media altura y cabeza
    - Planilla (tabla) con designación, diámetro, longitud, peso, cantidad
    - Cajetín opcional con datos del proyecto

Compatible con AutoCAD R2010+ via ezdxf.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from pathlib import Path

from .exceptions import DependencyError

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
except ImportError as exc:  # pragma: no cover
    raise DependencyError("ezdxf requerido: pip install ezdxf") from exc

from .core import DXFDocument


@dataclass(frozen=True)
class ColumnRebarBar:
    """Una marca de barra (mark) usada en la columna."""
    mark: str
    diameter_mm: float
    length_m: float
    quantity: int
    shape: str = "L1"

    @property
    def weight_kg(self) -> float:
        """Peso = rho * A * L con rho=7850 kg/m^3 y A=pi*d^2/4."""
        A = math.pi * (self.diameter_mm / 1000.0) ** 2 / 4.0
        return 7850.0 * A * self.length_m * self.quantity


@dataclass
class ColumnRebarDetail:
    """Definición completa del despiece de una columna."""
    name: str
    b_mm: float
    h_mm: float
    H_mm: float
    cover_mm: float = 40.0
    longitudinal: list[ColumnRebarBar] = field(default_factory=list)
    stirrups: list[ColumnRebarBar] = field(default_factory=list)
    project: str = ""
    drawn_by: str = ""


def render_column_rebar_detail(detail: ColumnRebarDetail, path: str | Path) -> Path:
    """Genera el DXF completo en ``path``."""
    path = Path(path)
    doc = DXFDocument(str(path))
    msp = doc._msp
    _draw_elevation(msp, detail, x0=0, y0=0)
    _draw_sections(msp, detail, x0=detail.b_mm + 800, y0=0)
    _draw_schedule(
        msp, detail,
        x0=detail.b_mm + 800,
        y0=-(detail.H_mm + 500),
    )
    _draw_titleblock(msp, detail, x0=0, y0=-(detail.H_mm + 800))
    doc.save()
    return path


def _place_text(msp, content: str, x: float, y: float, height: float,
                layer: str) -> None:
    """Add a TEXT entity at (x, y) with given height/layer."""
    t = msp.add_text(content, dxfattribs={"layer": layer, "height": height})
    try:
        t.set_placement((x, y), align=TextEntityAlignment.LEFT)
    except Exception:  # pragma: no cover
        t.dxf.insert = (x, y)


def _draw_elevation(msp, d: ColumnRebarDetail, x0: float, y0: float) -> None:
    """Vista frontal de la columna con altura H y barras longitudinales."""
    layer_c = "CONCRETO"
    layer_a = "ARMADURA"
    msp.add_lwpolyline(
        [(x0, y0), (x0 + d.b_mm, y0), (x0 + d.b_mm, y0 + d.H_mm),
         (x0, y0 + d.H_mm), (x0, y0)],
        close=True,
        dxfattribs={"layer": layer_c, "color": 7},
    )
    if d.longitudinal:
        n = len(d.longitudinal)
        usable = d.b_mm - 2 * d.cover_mm
        spacing = usable / max(n - 1, 1) if n > 1 else 0.0
        for i, bar in enumerate(d.longitudinal):
            x_bar = x0 + d.cover_mm + (i * spacing if n > 1 else usable / 2)
            msp.add_line(
                (x_bar, y0 + d.cover_mm),
                (x_bar, y0 + d.H_mm - d.cover_mm),
                dxfattribs={"layer": layer_a, "color": 1},
            )
            _place_text(
                msp, f"{bar.mark}-{int(bar.diameter_mm)}",
                x_bar - 5, y0 + d.H_mm + 100,
                height=80, layer="TEXTO",
            )
    _place_text(msp, f"H = {int(d.H_mm)} mm", x0, y0 - 200,
                height=120, layer="COTAS")
    _place_text(msp, f"ALZADO {d.name}", x0, y0 + d.H_mm + 400,
                height=200, layer="TEXTO")


def _draw_sections(msp, d: ColumnRebarDetail, x0: float, y0: float) -> None:
    """Tres secciones transversales (base, media, cabeza)."""
    sec_size = max(d.b_mm, d.h_mm)
    gap = 200
    for i, label in enumerate(["BASE", "MEDIA", "CABEZA"]):
        cx = x0
        cy = y0 + i * (sec_size + gap + 400)
        msp.add_lwpolyline(
            [(cx, cy), (cx + d.b_mm, cy), (cx + d.b_mm, cy + d.h_mm),
             (cx, cy + d.h_mm), (cx, cy)],
            close=True, dxfattribs={"layer": "CONCRETO"},
        )
        if d.longitudinal:
            bar_d = d.longitudinal[0].diameter_mm
            half_b = d.b_mm / 2 - d.cover_mm - bar_d / 2
            half_h = d.h_mm / 2 - d.cover_mm - bar_d / 2
            cx0, cy0 = cx + d.b_mm / 2, cy + d.h_mm / 2
            for sx in (-1, 1):
                for sy in (-1, 1):
                    msp.add_circle(
                        (cx0 + sx * half_b, cy0 + sy * half_h),
                        radius=bar_d / 2,
                        dxfattribs={"layer": "ARMADURA", "color": 1},
                    )
            # Estribo (recuadro al recubrimiento) si hay estribos definidos
            if d.stirrups:
                msp.add_lwpolyline(
                    [(cx + d.cover_mm, cy + d.cover_mm),
                     (cx + d.b_mm - d.cover_mm, cy + d.cover_mm),
                     (cx + d.b_mm - d.cover_mm, cy + d.h_mm - d.cover_mm),
                     (cx + d.cover_mm, cy + d.h_mm - d.cover_mm),
                     (cx + d.cover_mm, cy + d.cover_mm)],
                    close=True,
                    dxfattribs={"layer": "ESTRIBO", "color": 3},
                )
        _place_text(msp, label, cx, cy + d.h_mm + 100,
                    height=100, layer="TEXTO")


def _draw_schedule(msp, d: ColumnRebarDetail,
                   x0: float, y0: float) -> None:
    """Tabla con: marca, diametro, longitud, cantidad, peso."""
    header = ["MARCA", "D(mm)", "L(m)", "N", "kg"]
    col_w = [600, 600, 600, 400, 600]
    row_h = 200
    all_bars = list(d.longitudinal) + list(d.stirrups)
    title_y = y0 + (len(all_bars) + 2) * row_h + 200
    _place_text(msp, "PLANILLA DE ARMADURA", x0, title_y,
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
    total_kg = 0.0
    for j, bar in enumerate(all_bars):
        y_row = y - (j + 1) * row_h
        x_acc = x0
        vals = [bar.mark, f"{int(bar.diameter_mm)}",
                f"{bar.length_m:.2f}", str(bar.quantity),
                f"{bar.weight_kg:.1f}"]
        for i, v in enumerate(vals):
            _place_text(msp, v, x_acc + 20, y_row + 30,
                        height=80, layer="TEXTO")
            msp.add_lwpolyline(
                [(x_acc, y_row), (x_acc + col_w[i], y_row),
                 (x_acc + col_w[i], y_row + 150),
                 (x_acc, y_row + 150), (x_acc, y_row)],
                close=True, dxfattribs={"layer": "TEXTO"},
            )
            x_acc += col_w[i]
        total_kg += bar.weight_kg
    y_tot = y - (len(all_bars) + 1) * row_h
    _place_text(msp, f"TOTAL = {total_kg:.1f} kg", x0, y_tot,
                height=120, layer="TEXTO")


def _draw_titleblock(msp, d: ColumnRebarDetail,
                     x0: float, y0: float) -> None:
    """Cajetin simple con datos del proyecto."""
    w, h = 2400, 600
    msp.add_lwpolyline(
        [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h),
         (x0, y0 + h), (x0, y0)],
        close=True, dxfattribs={"layer": "CAJETIN"},
    )
    lines = [
        f"Proyecto: {d.project or '-'}",
        f"Elemento: {d.name}",
        f"Dimensiones: {int(d.b_mm)}x{int(d.h_mm)} mm | H = {int(d.H_mm)} mm",
        f"Recubrimiento: {int(d.cover_mm)} mm",
        f"Dibujado por: {d.drawn_by or '-'}",
    ]
    for i, line in enumerate(lines):
        _place_text(msp, line, x0 + 20, y0 + h - 100 - i * 100,
                    height=80, layer="TEXTO")
