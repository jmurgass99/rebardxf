"""Cuadro de pilares clásico de hormigón armado (RC Column Schedule Grid) en DXF.

Genera el cuadro clásico estructural:
    - Matriz de plantas (pisos) vs designación de columnas (P-1, P-2, ...)
    - En cada celda: sección gráfica dibujada a escala (contorno de hormigón, estribo, armadura longitudinal)
    - Especificación textual: dimensiones (b x h), armado longitudinal (e.g. 8Ø20), estribado (e.g. Ø10 c/15cm)
    - Bloque de tabla estructurada en AutoCAD con recuento exacto de entidades DXF.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

import ezdxf
from ezdxf.enums import TextEntityAlignment


@dataclass(frozen=True)
class ColumnStorySpec:
    """Especificación de una columna en un piso determinado."""
    column_tag: str     # e.g. "P-1", "C-1"
    story_name: str     # e.g. "Planta 1", "Piso 2 a 3"
    b_mm: float
    h_mm: float
    n_bars: int
    db_mm: float
    stirrup_db_mm: float = 10.0
    stirrup_spacing_mm: float = 150.0
    cover_mm: float = 40.0


@dataclass(frozen=True)
class ColumnScheduleStats:
    total_columns: int
    total_stories: int
    total_cells: int
    line_entities: int
    text_entities: int
    circle_entities: int
    total_entities: int


class ColumnScheduleDrawer:
    """Generador del cuadro clásico de pilares en formato DXF."""

    def __init__(
        self,
        columns: Sequence[str],
        stories: Sequence[str],
        specs: dict[tuple[str, str], ColumnStorySpec],
        cell_width: float = 1200.0,
        cell_height: float = 1000.0,
        header_height: float = 300.0,
        story_col_width: float = 800.0,
    ) -> None:
        self.columns = list(columns)
        self.stories = list(stories)
        self.specs = specs
        self.cell_w = cell_width
        self.cell_h = cell_height
        self.hdr_h = header_height
        self.story_w = story_col_width

    def draw_to_doc(self, doc: ezdxf.document.Drawing) -> ColumnScheduleStats:
        msp = doc.modelspace()

        # Asegurar capas estándar
        if "S-COL-LINE" not in doc.layers:
            doc.layers.add("S-COL-LINE", color=7)
        if "S-COL-CONC" not in doc.layers:
            doc.layers.add("S-COL-CONC", color=4)
        if "S-COL-REBAR" not in doc.layers:
            doc.layers.add("S-COL-REBAR", color=1)
        if "S-COL-TEXT" not in doc.layers:
            doc.layers.add("S-COL-TEXT", color=2)

        n_cols = len(self.columns)
        n_stories = len(self.stories)
        total_width = self.story_w + n_cols * self.cell_w
        total_height = self.hdr_h + n_stories * self.cell_h

        line_count = 0
        text_count = 0
        circle_count = 0

        def _add_line(p1: tuple[float, float], p2: tuple[float, float], layer: str = "S-COL-LINE"):
            nonlocal line_count
            msp.add_line(p1, p2, dxfattribs={"layer": layer})
            line_count += 1

        def _add_text(txt: str, pos: tuple[float, float], h: float = 40.0, layer: str = "S-COL-TEXT", align=TextEntityAlignment.MIDDLE_CENTER):
            nonlocal text_count
            t = msp.add_text(txt, dxfattribs={"layer": layer, "height": h})
            t.set_placement(pos, align=align)
            text_count += 1

        def _add_circle(center: tuple[float, float], radius: float, layer: str = "S-COL-REBAR"):
            nonlocal circle_count
            msp.add_circle(center, radius, dxfattribs={"layer": layer})
            circle_count += 1

        # 1. Cuadrícula de la tabla (Bordes horizontales y verticales)
        # Líneas horizontales
        _add_line((0, 0), (total_width, 0))
        _add_line((0, self.hdr_h), (total_width, self.hdr_h))
        for row_idx in range(1, n_stories + 1):
            y = self.hdr_h + row_idx * self.cell_h
            _add_line((0, y), (total_width, y))

        # Líneas verticales
        _add_line((0, 0), (0, total_height))
        _add_line((self.story_w, 0), (self.story_w, total_height))
        for col_idx in range(1, n_cols + 1):
            x = self.story_w + col_idx * self.cell_w
            _add_line((x, 0), (x, total_height))

        # 2. Encabezados de Columnas (P-1, P-2, ...)
        _add_text("NIVEL / PILAR", (self.story_w / 2.0, self.hdr_h / 2.0), h=50.0)
        for j, col_tag in enumerate(self.columns):
            cx = self.story_w + j * self.cell_w + self.cell_w / 2.0
            _add_text(col_tag, (cx, self.hdr_h / 2.0), h=55.0)

        # 3. Contenido de las Celdas por Planta (Planta vs Columna)
        for i, story_name in enumerate(reversed(self.stories)):  # Plantas superiores arriba
            row_y0 = self.hdr_h + (n_stories - 1 - i) * self.cell_h
            row_cy = row_y0 + self.cell_h / 2.0

            # Etiqueta de la planta
            _add_text(story_name, (self.story_w / 2.0, row_cy), h=45.0)

            for j, col_tag in enumerate(self.columns):
                cell_x0 = self.story_w + j * self.cell_w
                cell_cx = cell_x0 + self.cell_w / 2.0

                key = (story_name, col_tag)
                spec = self.specs.get(key)
                if spec is None:
                    _add_text("-", (cell_cx, row_cy), h=40.0)
                    continue

                # Dibujo en miniatura de la sección (Escala 1:1 dibujado centrado en la mitad superior de la celda)
                sec_cx = cell_cx
                sec_cy = row_y0 + self.cell_h * 0.60
                bw = spec.b_mm
                bh = spec.h_mm

                # Factor de escala gráfico para que quepa en la celda
                max_dim = max(bw, bh)
                target_dim = self.cell_h * 0.45
                s_factor = target_dim / max(max_dim, 100.0)

                scaled_b = bw * s_factor
                scaled_h = bh * s_factor
                x_left = sec_cx - scaled_b / 2.0
                x_right = sec_cx + scaled_b / 2.0
                y_bot = sec_cy - scaled_h / 2.0
                y_top = sec_cy + scaled_h / 2.0

                # Contorno de hormigón
                _add_line((x_left, y_bot), (x_right, y_bot), layer="S-COL-CONC")
                _add_line((x_right, y_bot), (x_right, y_top), layer="S-COL-CONC")
                _add_line((x_right, y_top), (x_left, y_top), layer="S-COL-CONC")
                _add_line((x_left, y_top), (x_left, y_bot), layer="S-COL-CONC")

                # Estribo perimetral
                c_scaled = spec.cover_mm * s_factor
                sx_left = x_left + c_scaled
                sx_right = x_right - c_scaled
                sy_bot = y_bot + c_scaled
                sy_top = y_top - c_scaled
                _add_line((sx_left, sy_bot), (sx_right, sy_bot), layer="S-COL-REBAR")
                _add_line((sx_right, sy_bot), (sx_right, sy_top), layer="S-COL-REBAR")
                _add_line((sx_right, sy_top), (sx_left, sy_top), layer="S-COL-REBAR")
                _add_line((sx_left, sy_top), (sx_left, sy_bot), layer="S-COL-REBAR")

                # Barras de esquina
                bar_r = max(spec.db_mm * s_factor / 2.0, 4.0)
                _add_circle((sx_left, sy_bot), bar_r)
                _add_circle((sx_right, sy_bot), bar_r)
                _add_circle((sx_right, sy_top), bar_r)
                _add_circle((sx_left, sy_top), bar_r)

                # Barras intermedias si n_bars > 4
                extra_bars = spec.n_bars - 4
                if extra_bars > 0:
                    for eb in range(1, extra_bars + 1):
                        frac = eb / (extra_bars + 1)
                        # Distribuir en las caras principales
                        bx = sx_left + frac * (sx_right - sx_left)
                        _add_circle((bx, sy_bot), bar_r)
                        _add_circle((bx, sy_top), bar_r)

                # Rótulos textuales inferiores en la celda
                txt_y1 = row_y0 + self.cell_h * 0.22
                txt_y2 = row_y0 + self.cell_h * 0.10
                dim_str = f"{int(bw)} x {int(bh)} cm" if bw < 100 else f"{int(bw/10)}x{int(bh/10)}"
                rebar_str = f"{spec.n_bars}Ø{int(spec.db_mm)}"
                stirrup_str = f"e: Ø{int(spec.stirrup_db_mm)} c/{int(spec.stirrup_spacing_mm/10)}cm"

                _add_text(f"{dim_str} - {rebar_str}", (cell_cx, txt_y1), h=32.0)
                _add_text(stirrup_str, (cell_cx, txt_y2), h=26.0)

        total_ents = line_count + text_count + circle_count
        return ColumnScheduleStats(
            total_columns=n_cols,
            total_stories=n_stories,
            total_cells=n_cols * n_stories,
            line_entities=line_count,
            text_entities=text_count,
            circle_entities=circle_count,
            total_entities=total_ents,
        )

    def render_to_file(self, filepath: str | Path) -> ColumnScheduleStats:
        doc = ezdxf.new("R2010")
        stats = self.draw_to_doc(doc)
        doc.saveas(str(filepath))
        return stats


__all__ = [
    "ColumnStorySpec",
    "ColumnScheduleStats",
    "ColumnScheduleDrawer",
]
