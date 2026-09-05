"""Bridge dxfstructuraljm <- fastsap: dibuja DXF del armado de seccion RC.

Toma el resultado de un diseno de seccion (cuantia, barras, estribos)
calculado en fastsap (section_analysis / rc_design services) y genera
el DXF de la seccion transversal con barras + estribos a escala.

Cliente fastsap duck-typed: la seccion llega como dataclass simple
(RCSectionDesign), no se importa fastsap.
"""
from __future__ import annotations
import logging
import math
from dataclasses import dataclass, field

try:
    import ezdxf
    from ezdxf import colors as dxf_colors
    _HAS_EZDXF = True
except ImportError:
    _HAS_EZDXF = False
    ezdxf = None  # type: ignore

log = logging.getLogger("dxfstructuraljm.fastsap_bridge")


@dataclass(frozen=True)
class RebarBar:
    """Una barra longitudinal."""
    x_mm: float            # posicion X dentro de la seccion
    y_mm: float            # posicion Y
    diameter_mm: float


@dataclass(frozen=True)
class RCSectionDesign:
    """Diseno de una seccion RC rectangular (input duck-typed desde fastsap)."""
    section_id: str
    b_mm: float            # ancho
    h_mm: float            # peralte
    cover_mm: float        # recubrimiento al estribo
    bars: tuple[RebarBar, ...]
    tie_diameter_mm: float
    tie_spacing_mm: float
    concrete_fc_MPa: float = 30.0
    steel_fy_MPa: float = 500.0


@dataclass
class DXFBridgeResult:
    section_id: str
    dxf_path: str
    n_bars: int
    total_As_mm2: float
    notes: list[str] = field(default_factory=list)


def _rectangular_bar_layout(b, h, cover, n_x, n_y, bar_dia, tie_dia):
    """Genera barras en perimetro: n_x por fila superior/inferior, n_y por columna lateral."""
    # Posicion del centro de la primera barra desde el borde
    edge_offset = cover + tie_dia + bar_dia / 2
    bars = []

    # Filas superior e inferior
    if n_x >= 2:
        x_positions = [edge_offset + i * (b - 2 * edge_offset) / (n_x - 1) for i in range(n_x)]
    else:
        x_positions = [b / 2]

    for x in x_positions:
        bars.append(RebarBar(x_mm=x, y_mm=edge_offset, diameter_mm=bar_dia))
        bars.append(RebarBar(x_mm=x, y_mm=h - edge_offset, diameter_mm=bar_dia))

    # Columnas laterales (sin duplicar esquinas ya incluidas)
    if n_y > 2:
        y_positions = [edge_offset + i * (h - 2 * edge_offset) / (n_y - 1) for i in range(1, n_y - 1)]
        for y in y_positions:
            bars.append(RebarBar(x_mm=edge_offset, y_mm=y, diameter_mm=bar_dia))
            bars.append(RebarBar(x_mm=b - edge_offset, y_mm=y, diameter_mm=bar_dia))

    return tuple(bars)


def build_rectangular_section_design(section_id: str, b_mm: float, h_mm: float, cover_mm: float,
                                          n_bars_x: int, n_bars_y: int, bar_dia_mm: float,
                                          tie_dia_mm: float, tie_spacing_mm: float,
                                          fc_MPa: float = 30.0, fy_MPa: float = 500.0) -> RCSectionDesign:
    """Helper para construir RCSectionDesign desde parametros simples."""
    if any(v <= 0 for v in (b_mm, h_mm, cover_mm, bar_dia_mm, tie_dia_mm, tie_spacing_mm)):
        raise ValueError("dimensiones deben ser positivas")
    if n_bars_x < 2 or n_bars_y < 2:
        raise ValueError("n_bars_x y n_bars_y deben ser >= 2")
    if cover_mm + tie_dia_mm + bar_dia_mm >= min(b_mm, h_mm) / 2:
        raise ValueError("cover+tie+bar excede media seccion: imposible armar")

    bars = _rectangular_bar_layout(b_mm, h_mm, cover_mm, n_bars_x, n_bars_y,
                                       bar_dia_mm, tie_dia_mm)
    return RCSectionDesign(
        section_id=section_id, b_mm=b_mm, h_mm=h_mm, cover_mm=cover_mm,
        bars=bars, tie_diameter_mm=tie_dia_mm, tie_spacing_mm=tie_spacing_mm,
        concrete_fc_MPa=fc_MPa, steel_fy_MPa=fy_MPa,
    )


def draw_section_dxf(design: RCSectionDesign, output_path: str,
                       scale: float = 1.0, add_dimensions: bool = True, add_annotations: bool = True):
    """Genera el DXF de la seccion transversal con barras + estribo.

    Args:
        design: RCSectionDesign
        output_path: ruta del archivo .dxf a escribir
        scale: factor de escala (1.0 = unidades mm = 1:1)
        add_dimensions: si True, dibuja cotas b y h
        add_annotations: si True, escribe etiqueta con cuantia y fc/fy

    Returns:
        DXFBridgeResult con path + summary.

    Raises:
        ImportError si ezdxf no esta disponible.
        ValueError si la seccion no tiene barras.
    """
    if not _HAS_EZDXF:
        raise ImportError("ezdxf no esta instalado; pip install ezdxf>=1.0")
    if not design.bars:
        raise ValueError("design sin barras: nada que dibujar")

    doc = ezdxf.new(dxfversion="R2018")
    msp = doc.modelspace()

    # Capas
    doc.layers.add(name="CONCRETE", color=8)
    doc.layers.add(name="REBAR", color=1)        # rojo
    doc.layers.add(name="TIE", color=3)          # verde
    doc.layers.add(name="DIM", color=2)          # amarillo
    doc.layers.add(name="TEXT", color=7)         # blanco

    s = scale
    b = design.b_mm * s
    h = design.h_mm * s
    c = design.cover_mm * s
    td = design.tie_diameter_mm * s

    # Contorno de hormigon (rectangulo exterior)
    msp.add_lwpolyline(
        [(0, 0), (b, 0), (b, h), (0, h), (0, 0)],
        dxfattribs={"layer": "CONCRETE", "const_width": 0},
    )

    # Estribo (rectangulo redondeado simplificado: solo lineas rectas interior)
    e = c + td / 2
    msp.add_lwpolyline(
        [(e, e), (b - e, e), (b - e, h - e), (e, h - e), (e, e)],
        dxfattribs={"layer": "TIE"},
    )

    # Barras longitudinales (circulos)
    for bar in design.bars:
        msp.add_circle(
            center=(bar.x_mm * s, bar.y_mm * s),
            radius=(bar.diameter_mm / 2) * s,
            dxfattribs={"layer": "REBAR"},
        )
        # Relleno aproximado con un hatch (skipear si falla)
        try:
            hatch = msp.add_hatch(color=1, dxfattribs={"layer": "REBAR"})
            edge_path = hatch.paths.add_edge_path()
            edge_path.add_arc(
                center=(bar.x_mm * s, bar.y_mm * s),
                radius=(bar.diameter_mm / 2) * s,
                start_angle=0, end_angle=360, ccw=True,
            )
        except Exception:
            pass

    # Cotas
    if add_dimensions:
        dim_offset = 0.15 * max(b, h)
        # Cota horizontal b
        msp.add_text(
            f"b = {design.b_mm:.0f} mm",
            dxfattribs={"layer": "DIM", "height": 0.04 * max(b, h)},
        ).set_placement((b / 2, -dim_offset))
        # Cota vertical h
        msp.add_text(
            f"h = {design.h_mm:.0f} mm",
            dxfattribs={"layer": "DIM", "height": 0.04 * max(b, h)},
        ).set_placement((-dim_offset, h / 2))

    # Anotaciones
    total_As = sum(math.pi * (bar.diameter_mm / 2) ** 2 for bar in design.bars)
    Ac = design.b_mm * design.h_mm
    rho = total_As / Ac

    if add_annotations:
        ann = [
            f"Section: {design.section_id}",
            f"{len(design.bars)} bars phi{int(design.bars[0].diameter_mm)} mm",
            f"As = {total_As:.0f} mm2 (rho = {rho*100:.2f}%)",
            f"Stirrups phi{int(design.tie_diameter_mm)}@{int(design.tie_spacing_mm)} mm",
            f"fc = {design.concrete_fc_MPa:.0f} MPa, fy = {design.steel_fy_MPa:.0f} MPa",
        ]
        for i, line in enumerate(ann):
            msp.add_text(
                line, dxfattribs={"layer": "TEXT", "height": 0.035 * max(b, h)},
            ).set_placement((b + 0.1 * b, h - i * 0.06 * h))

    doc.saveas(output_path)
    log.info("DXF generado: %s (%d barras, As=%.0f mm2)", output_path, len(design.bars), total_As)

    return DXFBridgeResult(
        section_id=design.section_id,
        dxf_path=str(output_path),
        n_bars=len(design.bars),
        total_As_mm2=float(total_As),
        notes=[
            f"As_total = {total_As:.0f} mm2",
            f"rho = {rho*100:.3f}%",
            f"{len(design.bars)} barras phi{int(design.bars[0].diameter_mm)}",
        ],
    )
