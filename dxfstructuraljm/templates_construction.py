"""
Plantillas constructivas estándar (geometría sin ezdxf — para tests).

Tipologías:
    - footing_isolated: zapata aislada (planta + corte)
    - beam_section_rebar: corte transversal de viga con armado
    - column_section: corte de columna con estribos
    - wall_section: corte de muro de cortante con armado
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FootingTemplateInput:
    B_mm: float = 2500
    L_mm: float = 2500
    H_mm: float = 600
    col_b_mm: float = 400
    col_h_mm: float = 400
    cover_mm: float = 50


@dataclass(frozen=True)
class TemplateGeometry:
    rectangles: list[tuple[float, float, float, float]] = field(default_factory=list)
    circles: list[tuple[float, float, float]] = field(default_factory=list)
    texts: list[dict[str, Any]] = field(default_factory=list)
    lines: list[tuple[float, float, float, float]] = field(default_factory=list)


def build_footing_template(inp: FootingTemplateInput) -> TemplateGeometry:
    g = TemplateGeometry(rectangles=[], circles=[], texts=[], lines=[])
    # Planta zapata
    g.rectangles.append((0, 0, inp.B_mm, inp.L_mm))
    # Columna centrada
    cx = (inp.B_mm - inp.col_b_mm) / 2
    cy = (inp.L_mm - inp.col_h_mm) / 2
    g.rectangles.append((cx, cy, inp.col_b_mm, inp.col_h_mm))
    # Refuerzo en cuadrícula (puntos)
    nb_x, nb_y = 8, 8
    cover = inp.cover_mm
    for i in range(nb_x):
        x = cover + (inp.B_mm - 2 * cover) * i / (nb_x - 1)
        for j in range(nb_y):
            y = cover + (inp.L_mm - 2 * cover) * j / (nb_y - 1)
            g.circles.append((x, y, 8.0))  # φ16 representado como círculo
    # Cotas
    g.texts.append({"pos": (inp.B_mm / 2, -150), "text": f"{inp.B_mm:.0f}",
                     "height": 60})
    g.texts.append({"pos": (-200, inp.L_mm / 2), "text": f"{inp.L_mm:.0f}",
                     "height": 60})
    return g


@dataclass(frozen=True)
class TitleBlockA1Input:
    project_name: str
    drawing_number: str
    revision: str = "0"
    author: str = "JM"
    scale: str = "1:50"


def build_title_block_a1(inp: TitleBlockA1Input) -> TemplateGeometry:
    """Cajetín A1 estándar (594 x 841 mm) — sólo bloque inferior derecho."""
    g = TemplateGeometry()
    # Bloque 180x80 esquina inferior derecha
    bx, by = 411, 0  # 591-180
    g.rectangles.append((bx, by, 180, 80))
    # Subdivisiones
    g.lines.append((bx, by + 20, bx + 180, by + 20))
    g.lines.append((bx, by + 40, bx + 180, by + 40))
    g.lines.append((bx, by + 60, bx + 180, by + 60))
    # Textos
    g.texts.extend([
        {"pos": (bx + 5, by + 65), "text": inp.project_name, "height": 3.5},
        {"pos": (bx + 5, by + 45), "text": f"Plano: {inp.drawing_number}",
         "height": 2.5},
        {"pos": (bx + 5, by + 25), "text": f"Esc {inp.scale}", "height": 2.5},
        {"pos": (bx + 100, by + 25), "text": f"Rev {inp.revision}",
         "height": 2.5},
        {"pos": (bx + 5, by + 5),  "text": f"Por: {inp.author}",
         "height": 2.5},
    ])
    return g


@dataclass(frozen=True)
class BeamSectionTemplateInput:
    b_mm: float = 300
    h_mm: float = 500
    cover_mm: float = 40
    n_top: int = 3
    n_bot: int = 3
    bar_dia_mm: float = 16
    stirrup_dia_mm: float = 10
    stirrup_spacing_mm: float = 200


def build_beam_section_template(inp: BeamSectionTemplateInput) -> TemplateGeometry:
    """Corte transversal de viga con armado longitudinal y estribos."""
    g = TemplateGeometry(rectangles=[], circles=[], texts=[], lines=[])

    # Contorno exterior de la sección
    g.rectangles.append((0, 0, inp.b_mm, inp.h_mm))

    # Estribo (rectángulo interior descontando recubrimiento)
    sx = inp.cover_mm
    sy = inp.cover_mm
    sw = inp.b_mm - 2 * inp.cover_mm
    sh = inp.h_mm - 2 * inp.cover_mm
    g.rectangles.append((sx, sy, sw, sh))

    # Barras superiores — centros a distancia cover del borde
    bar_r = inp.bar_dia_mm / 2.0
    top_y = inp.h_mm - inp.cover_mm
    for i in range(inp.n_top):
        if inp.n_top == 1:
            x = inp.b_mm / 2.0
        else:
            x = inp.cover_mm + (inp.b_mm - 2 * inp.cover_mm) * i / (inp.n_top - 1)
        g.circles.append((x, top_y, bar_r))

    # Barras inferiores
    bot_y = inp.cover_mm
    for i in range(inp.n_bot):
        if inp.n_bot == 1:
            x = inp.b_mm / 2.0
        else:
            x = inp.cover_mm + (inp.b_mm - 2 * inp.cover_mm) * i / (inp.n_bot - 1)
        g.circles.append((x, bot_y, bar_r))

    # Acotaciones
    g.texts.append({"pos": (inp.b_mm / 2, -150), "text": f"{inp.b_mm:.0f}",
                     "height": 60})
    g.texts.append({"pos": (-200, inp.h_mm / 2), "text": f"{inp.h_mm:.0f}",
                     "height": 60})
    # Anotaciones de armado
    g.texts.append({"pos": (inp.b_mm + 50, top_y),
                     "text": f"{inp.n_top}⌀{inp.bar_dia_mm:.0f}",
                     "height": 40})
    g.texts.append({"pos": (inp.b_mm + 50, bot_y),
                     "text": f"{inp.n_bot}⌀{inp.bar_dia_mm:.0f}",
                     "height": 40})
    g.texts.append({"pos": (inp.b_mm / 2, inp.h_mm + 80),
                     "text": f"Est ⌀{inp.stirrup_dia_mm:.0f}@{inp.stirrup_spacing_mm:.0f}",
                     "height": 40})
    return g


@dataclass(frozen=True)
class ColumnSectionTemplateInput:
    b_mm: float = 400
    h_mm: float = 400
    cover_mm: float = 40
    n_bars_x: int = 3
    n_bars_y: int = 3
    bar_dia_mm: float = 20
    tie_dia_mm: float = 10
    tie_spacing_mm: float = 200


def build_column_section_template(inp: ColumnSectionTemplateInput) -> TemplateGeometry:
    """Corte transversal de columna con estribos y armado perimetral."""
    g = TemplateGeometry(rectangles=[], circles=[], texts=[], lines=[])

    # Contorno exterior
    g.rectangles.append((0, 0, inp.b_mm, inp.h_mm))

    # Estribo / zuncho
    tx = inp.cover_mm
    ty = inp.cover_mm
    tw = inp.b_mm - 2 * inp.cover_mm
    th = inp.h_mm - 2 * inp.cover_mm
    g.rectangles.append((tx, ty, tw, th))

    bar_r = inp.bar_dia_mm / 2.0

    # Generar posiciones de barras en el perímetro (sin duplicar esquinas)
    # Fila inferior (y = cover): n_bars_x barras
    for i in range(inp.n_bars_x):
        if inp.n_bars_x == 1:
            x = inp.b_mm / 2.0
        else:
            x = inp.cover_mm + (inp.b_mm - 2 * inp.cover_mm) * i / (inp.n_bars_x - 1)
        g.circles.append((x, inp.cover_mm, bar_r))

    # Fila superior (y = h - cover): n_bars_x barras
    for i in range(inp.n_bars_x):
        if inp.n_bars_x == 1:
            x = inp.b_mm / 2.0
        else:
            x = inp.cover_mm + (inp.b_mm - 2 * inp.cover_mm) * i / (inp.n_bars_x - 1)
        g.circles.append((x, inp.h_mm - inp.cover_mm, bar_r))

    # Columnas laterales izq/der (sin esquinas, ya contadas arriba)
    for j in range(1, inp.n_bars_y - 1):
        y = inp.cover_mm + (inp.h_mm - 2 * inp.cover_mm) * j / (inp.n_bars_y - 1)
        # Lado izquierdo
        g.circles.append((inp.cover_mm, y, bar_r))
        # Lado derecho
        g.circles.append((inp.b_mm - inp.cover_mm, y, bar_r))

    # Acotaciones
    g.texts.append({"pos": (inp.b_mm / 2, -150), "text": f"{inp.b_mm:.0f}",
                     "height": 60})
    g.texts.append({"pos": (-200, inp.h_mm / 2), "text": f"{inp.h_mm:.0f}",
                     "height": 60})

    total_bars = 2 * inp.n_bars_x + 2 * (inp.n_bars_y - 2)
    g.texts.append({"pos": (inp.b_mm + 50, inp.h_mm / 2),
                     "text": f"{total_bars}⌀{inp.bar_dia_mm:.0f}",
                     "height": 40})
    g.texts.append({"pos": (inp.b_mm / 2, inp.h_mm + 80),
                     "text": f"Est ⌀{inp.tie_dia_mm:.0f}@{inp.tie_spacing_mm:.0f}",
                     "height": 40})
    return g


@dataclass(frozen=True)
class WallSectionTemplateInput:
    length_mm: float = 3000
    thickness_mm: float = 200
    cover_mm: float = 40
    boundary_bars: int = 4
    web_bars: int = 6
    bar_dia_mm: float = 16


def build_wall_section_template(inp: WallSectionTemplateInput) -> TemplateGeometry:
    """Corte transversal de muro de cortante con elementos de borde y alma."""
    g = TemplateGeometry(rectangles=[], circles=[], texts=[], lines=[])

    # Contorno del muro
    g.rectangles.append((0, 0, inp.length_mm, inp.thickness_mm))

    # Elementos de borde — zona en cada extremo del largo
    # Longitud del boundary element ~ 2 * thickness (convención)
    bz_len = 2 * inp.thickness_mm
    # Borde izquierdo
    g.rectangles.append((0, 0, bz_len, inp.thickness_mm))
    # Borde derecho
    g.rectangles.append((inp.length_mm - bz_len, 0, bz_len, inp.thickness_mm))

    bar_r = inp.bar_dia_mm / 2.0

    # Barras en elemento de borde izquierdo — distribuidas en 2 filas
    n_rows = 2
    n_per_row = (inp.boundary_bars + 1) // 2  # mitad superior, mitad inferior
    n_last_row = inp.boundary_bars - n_per_row

    row_ys = [inp.cover_mm, inp.thickness_mm - inp.cover_mm]

    for row_idx, (n_in_row, ry) in enumerate(
        zip([n_per_row, n_last_row], row_ys)
    ):
        for i in range(n_in_row):
            if n_in_row == 1:
                x = bz_len / 2.0
            else:
                x = inp.cover_mm + (bz_len - 2 * inp.cover_mm) * i / (n_in_row - 1)
            g.circles.append((x, ry, bar_r))

    # Barras en elemento de borde derecho (espejado)
    offset_r = inp.length_mm - bz_len
    for row_idx, (n_in_row, ry) in enumerate(
        zip([n_per_row, n_last_row], row_ys)
    ):
        for i in range(n_in_row):
            if n_in_row == 1:
                x = bz_len / 2.0
            else:
                x = inp.cover_mm + (bz_len - 2 * inp.cover_mm) * i / (n_in_row - 1)
            g.circles.append((offset_r + x, ry, bar_r))

    # Barras de alma — distribuidas a lo largo del muro entre los bordes
    web_start = bz_len
    web_end = inp.length_mm - bz_len
    mid_y = inp.thickness_mm / 2.0
    for i in range(inp.web_bars):
        if inp.web_bars == 1:
            x = (web_start + web_end) / 2.0
        else:
            x = web_start + (web_end - web_start) * i / (inp.web_bars - 1)
        g.circles.append((x, mid_y, bar_r))

    # Acotaciones
    g.texts.append({"pos": (inp.length_mm / 2, -150),
                     "text": f"{inp.length_mm:.0f}", "height": 60})
    g.texts.append({"pos": (-200, inp.thickness_mm / 2),
                     "text": f"{inp.thickness_mm:.0f}", "height": 60})
    g.texts.append({"pos": (bz_len / 2, inp.thickness_mm + 80),
                     "text": f"Borde: {inp.boundary_bars}⌀{inp.bar_dia_mm:.0f}",
                     "height": 40})
    g.texts.append({"pos": (inp.length_mm / 2, inp.thickness_mm + 80),
                     "text": f"Alma: {inp.web_bars}⌀{inp.bar_dia_mm:.0f}",
                     "height": 40})
    return g


@dataclass(frozen=True)
class SheetA1LayoutInput:
    """Parámetros para generar una lámina A1 completa envolviendo planos."""
    project_name: str
    drawing_title: str
    drawing_number: str
    revision: str = "0"
    author: str = "JM"
    scale: str = "1:50"
    sheet_width_mm: float = 841.0
    sheet_height_mm: float = 594.0
    margin_mm: float = 10.0


def build_a1_sheet_with_titleblock(
    inp: SheetA1LayoutInput,
    drawings: list[tuple[TemplateGeometry, tuple[float, float]]] | None = None,
) -> TemplateGeometry:
    """Genera la lámina A1 con marco exterior, margen normativo, cajetín y dibujos incrustados."""
    g = TemplateGeometry()

    w = inp.sheet_width_mm
    h = inp.sheet_height_mm
    m = inp.margin_mm

    # 1. Borde exterior de papel
    g.rectangles.append((0.0, 0.0, w, h))

    # 2. Margen interior de dibujo (10 mm)
    g.rectangles.append((m, m, w - 2 * m, h - 2 * m))

    # 3. Cajetín normalizado A1 en esquina inferior derecha (180 x 80 mm)
    tb_w, tb_h = 180.0, 80.0
    tb_x = w - m - tb_w
    tb_y = m

    g.rectangles.append((tb_x, tb_y, tb_w, tb_h))
    # Divisiones horizontales del cajetín
    g.lines.append((tb_x, tb_y + 20.0, tb_x + tb_w, tb_y + 20.0))
    g.lines.append((tb_x, tb_y + 40.0, tb_x + tb_w, tb_y + 40.0))
    g.lines.append((tb_x, tb_y + 60.0, tb_x + tb_w, tb_y + 60.0))
    # Divisiones verticales
    g.lines.append((tb_x + 90.0, tb_y, tb_x + 90.0, tb_y + 40.0))

    # Textos del cajetín
    g.texts.extend([
        {"pos": (tb_x + 5.0, tb_y + 65.0), "text": f"PROYECTO: {inp.project_name}", "height": 3.5},
        {"pos": (tb_x + 5.0, tb_y + 45.0), "text": f"PLANO: {inp.drawing_title} ({inp.drawing_number})", "height": 3.0},
        {"pos": (tb_x + 5.0, tb_y + 25.0), "text": f"ESCALA: {inp.scale}", "height": 2.5},
        {"pos": (tb_x + 95.0, tb_y + 25.0), "text": f"REV: {inp.revision}", "height": 2.5},
        {"pos": (tb_x + 5.0, tb_y + 5.0), "text": f"AUTOR: {inp.author}", "height": 2.5},
        {"pos": (tb_x + 95.0, tb_y + 5.0), "text": "SOFTWARE: JMSTRUCTURAL", "height": 2.5},
    ])

    # 4. Incrustar detalles y planos dentro del área útil de la lámina
    if drawings:
        for geom, (ox, oy) in drawings:
            for rx, ry, rw, rh in geom.rectangles:
                g.rectangles.append((ox + rx, oy + ry, rw, rh))
            for cx, cy, cr in geom.circles:
                g.circles.append((ox + cx, oy + cy, cr))
            for x1, y1, x2, y2 in geom.lines:
                g.lines.append((ox + x1, oy + y1, ox + x2, oy + y2))
            for t in geom.texts:
                t_pos = t.get("pos", (0.0, 0.0))
                g.texts.append({
                    "pos": (ox + t_pos[0], oy + t_pos[1]),
                    "text": t.get("text", ""),
                    "height": t.get("height", 2.5),
                })

    return g


def render_a1_sheet_to_dxf(sheet_geom: TemplateGeometry, out_path: str) -> None:
    """Renderiza la geometría de lámina A1 a un archivo DXF AutoCAD R2010."""
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # Capas
    if "BORDER" not in doc.layers:
        doc.layers.add("BORDER", color=7)
    if "GEOMETRY" not in doc.layers:
        doc.layers.add("GEOMETRY", color=3)
    if "REBAR" not in doc.layers:
        doc.layers.add("REBAR", color=1)
    if "TEXT" not in doc.layers:
        doc.layers.add("TEXT", color=2)

    # Rectángulos
    for x, y, rw, rh in sheet_geom.rectangles:
        pts = [(x, y), (x + rw, y), (x + rw, y + rh), (x, y + rh), (x, y)]
        for p1, p2 in zip(pts[:-1], pts[1:]):
            msp.add_line(p1, p2, dxfattribs={"layer": "BORDER"})

    # Líneas
    for x1, y1, x2, y2 in sheet_geom.lines:
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": "BORDER"})

    # Círculos
    for cx, cy, cr in sheet_geom.circles:
        msp.add_circle((cx, cy), cr, dxfattribs={"layer": "REBAR"})

    # Textos
    for t in sheet_geom.texts:
        pos = t.get("pos", (0.0, 0.0))
        txt = t.get("text", "")
        h = t.get("height", 2.5)
        msp.add_text(txt, dxfattribs={"layer": "TEXT", "height": h}).set_placement(pos)

    doc.saveas(out_path)


__all__ = [
    "FootingTemplateInput", "TitleBlockA1Input", "TemplateGeometry",
    "build_footing_template", "build_title_block_a1",
    "BeamSectionTemplateInput", "build_beam_section_template",
    "ColumnSectionTemplateInput", "build_column_section_template",
    "WallSectionTemplateInput", "build_wall_section_template",
    "SheetA1LayoutInput", "build_a1_sheet_with_titleblock",
    "render_a1_sheet_to_dxf",
]

