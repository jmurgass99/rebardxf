"""
frame_elevation.py — Detallado de alzado de pórtico estructural de hormigón armado por eje.

Genera planos de alzado de pórtico con geometría de columnas y vigas, armado longitudinal,
estribado detallado en zonas críticas y centrales, ejes de replanteo, niveles de piso y
secciones transversales asociadas.

Derivación analítica exacta de entidades DXF:
=============================================
Para un pórtico con N_bays vanos y N_stories pisos:
  1. Ejes verticales (Grids):
     - Líneas de eje: N_axes = N_bays + 1
     - Burbujas de eje: N_axes círculos
     - Textos de etiqueta de eje: N_axes textos
  2. Niveles horizontales (Levels):
     - Líneas de nivel: N_levels = N_stories + 1
     - Textos de cota de nivel: N_levels textos
  3. Columnas (Contornos de hormigón):
     - N_cols = N_axes * N_stories
     - Líneas de contorno por columna: 2 verticales (izquierda y derecha)
     - Total líneas contorno columnas = 2 * N_cols
  4. Vigas (Contornos de hormigón):
     - N_beams = N_bays * N_stories
     - Líneas de contorno por viga: 2 horizontales (superior e inferior entre caras de columnas)
     - Total líneas contorno vigas = 2 * N_beams
  5. Armado longitudinal de columnas:
     - 2 líneas verticales por columna = 2 * N_cols líneas
  6. Estribos de columnas:
     - Por cada columna (de altura libre H_clear = H - beam_h):
       n_crit = int(col_lc_crit // col_s_crit)  (en base y cabeza)
       n_cent = max(0, int((H_clear - 2 * col_lc_crit) // col_s_cent))
       N_stirrups_col = 2 * n_crit + n_cent
       Total líneas de estribos en columnas = N_cols * N_stirrups_col
  7. Armado longitudinal de vigas:
     - 2 líneas horizontales por viga = 2 * N_beams líneas
  8. Estribos de vigas:
     - Por cada viga en cada vano i (de longitud libre L_clear = bay_i - col_w):
       n_crit_b = int(beam_lc_crit // beam_s_crit) (en extremo izquierdo y derecho)
       n_cent_b = max(0, int((L_clear - 2 * beam_lc_crit) // beam_s_cent))
       N_stirrups_beam_bay = 2 * n_crit_b + n_cent_b
       Total líneas de estribos en vigas = N_stories * sum(N_stirrups_beam_bay for bay in bays)
  9. Textos y títulos:
     - Título general del alzado: 1 texto
     - Etiquetas de vigas: N_beams textos
     - Etiquetas de columnas: N_cols textos

El recuento total de entidades (LINE, CIRCLE, TEXT) en el archivo DXF es una fórmula
algebraica determinista y cerrada.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple

from .core import DXFDocument, Layer


@dataclass
class FrameElevationDetail:
    """
    Especificación de alzado de pórtico de hormigón armado por eje.

    Parameters
    ----------
    axis_name : str  Nombre del eje (ej: "Eje 1", "Eje A")
    bays : list[float]  Longitudes de vanos entre ejes [mm] (ej: [5000.0, 6000.0])
    stories : list[float]  Alturas de entrepiso [mm] (ej: [3500.0, 3000.0])
    col_width : float  Ancho de columna en el plano del pórtico [mm]
    col_depth : float  Canto de columna perpendicular [mm]
    beam_width : float  Ancho de viga [mm]
    beam_height : float  Canto total de viga [mm]
    cover : float  Recubrimiento geométrico libre [mm]
    col_s_critical : float  Separación de estribos en zona confinada de columna [mm]
    col_s_central : float  Separación de estribos en zona central de columna [mm]
    col_lc_critical : float  Longitud de zona confinada en columna [mm]
    beam_s_critical : float  Separación de estribos en zona de confinamiento de viga [mm]
    beam_s_central : float  Separación de estribos en zona central de viga [mm]
    beam_lc_critical : float  Longitud de zona de confinamiento de viga [mm]
    label : str  Identificador del pórtico
    """
    axis_name: str = "Eje 1"
    bays: list[float] = field(default_factory=lambda: [5000.0, 6000.0])
    stories: list[float] = field(default_factory=lambda: [3500.0, 3000.0])
    col_width: float = 400.0
    col_depth: float = 400.0
    beam_width: float = 300.0
    beam_height: float = 500.0
    cover: float = 40.0
    col_s_critical: float = 100.0
    col_s_central: float = 200.0
    col_lc_critical: float = 500.0
    beam_s_critical: float = 100.0
    beam_s_central: float = 200.0
    beam_lc_critical: float = 800.0
    label: str = "PORTICO-01"

    @property
    def num_axes(self) -> int:
        return len(self.bays) + 1

    @property
    def num_levels(self) -> int:
        return len(self.stories) + 1

    @property
    def num_columns(self) -> int:
        return self.num_axes * len(self.stories)

    @property
    def num_beams(self) -> int:
        return len(self.bays) * len(self.stories)

    def col_stirrups_per_column(self, story_idx: int) -> int:
        """Número exacto de estribos en una columna de un piso dado."""
        h_story = self.stories[story_idx]
        h_clear = h_story - self.beam_height
        n_crit = int(self.col_lc_critical // self.col_s_critical)
        h_cent = max(0.0, h_clear - 2.0 * self.col_lc_critical)
        n_cent = int(h_cent // self.col_s_central)
        return 2 * n_crit + n_cent

    def beam_stirrups_per_bay(self, bay_idx: int) -> int:
        """Número exacto de estribos en una viga de un vano dado."""
        l_bay = self.bays[bay_idx]
        l_clear = l_bay - self.col_width
        n_crit = int(self.beam_lc_critical // self.beam_s_critical)
        l_cent = max(0.0, l_clear - 2.0 * self.beam_lc_critical)
        n_cent = int(l_cent // self.beam_s_central)
        return 2 * n_crit + n_cent

    def expected_entity_counts(self) -> dict[str, int]:
        """Deriva analíticamente el número EXACTO de entidades que debe contener el DXF."""
        n_axes = self.num_axes
        n_levels = self.num_levels
        n_stories = len(self.stories)
        n_bays = len(self.bays)
        n_cols = self.num_columns
        n_beams = self.num_beams

        # 1. Líneas de eje y niveles
        lines_axes = n_axes
        lines_levels = n_levels

        # 2. Contorno de columnas (2 líneas verticales por columna)
        lines_col_outline = 2 * n_cols

        # 3. Contorno de vigas (2 líneas horizontales por viga)
        lines_beam_outline = 2 * n_beams

        # 4. Armadura longitudinal de columnas (2 líneas verticales por columna)
        lines_col_longitudinal = 2 * n_cols

        # 5. Estribos de columnas
        col_stirrups_total = 0
        for s_idx in range(n_stories):
            col_stirrups_total += n_axes * self.col_stirrups_per_column(s_idx)
        lines_col_stirrups = col_stirrups_total

        # 6. Armadura longitudinal de vigas (2 líneas horizontales por viga)
        lines_beam_longitudinal = 2 * n_beams

        # 7. Estribos de vigas
        beam_stirrups_total = 0
        for b_idx in range(n_bays):
            beam_stirrups_total += n_stories * self.beam_stirrups_per_bay(b_idx)
        lines_beam_stirrups = beam_stirrups_total

        total_lines = (
            lines_axes
            + lines_levels
            + lines_col_outline
            + lines_beam_outline
            + lines_col_longitudinal
            + lines_col_stirrups
            + lines_beam_longitudinal
            + lines_beam_stirrups
        )

        # Círculos: exactamente 1 burbuja por eje
        total_circles = n_axes

        # Textos:
        #  - 1 título general
        #  - N_axes textos de burbuja de eje
        #  - N_levels textos de cota de nivel
        #  - N_cols textos de etiquetas de columna
        #  - N_beams textos de etiquetas de viga
        total_texts = 1 + n_axes + n_levels + n_cols + n_beams

        return {
            "LINE": total_lines,
            "CIRCLE": total_circles,
            "TEXT": total_texts,
            "total_entities": total_lines + total_circles + total_texts,
        }

    def draw_elevation(
        self,
        output_path: str | None = None,
        origin: tuple[float, float] = (0.0, 0.0),
    ) -> DXFDocument:
        """Genera el plano DXF de alzado del pórtico con armado y despiece completo."""
        if output_path is None:
            output_path = f"{self.label}_{self.axis_name.replace(' ', '_')}.dxf"

        doc = DXFDocument(output_path)
        x0, y0 = origin

        # Coordenadas acumuladas de ejes X
        x_coords: list[float] = [x0]
        for b in self.bays:
            x_coords.append(x_coords[-1] + b)

        # Coordenadas acumuladas de niveles Y
        y_coords: list[float] = [y0]
        for s in self.stories:
            y_coords.append(y_coords[-1] + s)

        total_width = x_coords[-1] - x0
        total_height = y_coords[-1] - y0

        # ------------------------------------------------------------------
        # 1. Ejes verticales y burbujas
        # ------------------------------------------------------------------
        grid_extension = 600.0
        bubble_radius = 200.0

        for i, x in enumerate(x_coords):
            # Línea de eje
            y_bottom = y0 - grid_extension
            y_top = y_coords[-1] + grid_extension
            doc.line((x, y_bottom), (x, y_top), layer=Layer.AXIS, lineweight=0.18)

            # Burbuja de eje
            cy_bubble = y_top + bubble_radius
            doc.circle((x, cy_bubble), radius=bubble_radius, layer=Layer.AXIS)

            # Etiqueta de eje (A, B, C... o 1, 2, 3...)
            label = chr(65 + i) if i < 26 else str(i + 1)
            doc.text((x - 60.0, cy_bubble - 60.0), label, height=120.0, layer=Layer.TEXT)

        # ------------------------------------------------------------------
        # 2. Niveles horizontales
        # ------------------------------------------------------------------
        level_extension = 600.0
        for j, y in enumerate(y_coords):
            # Línea de nivel
            doc.line((x0 - level_extension, y), (x_coords[-1] + level_extension, y), layer=Layer.AXIS, lineweight=0.18)
            # Cota de nivel
            level_m = (y - y0) / 1000.0
            sign = "+" if level_m >= 0 else ""
            doc.text((x0 - level_extension - 700.0, y - 40.0), f"N.{sign}{level_m:.2f} m", height=80.0, layer=Layer.TEXT)

        # ------------------------------------------------------------------
        # 3. Columnas: contorno de hormigón y armado
        # ------------------------------------------------------------------
        hw = self.col_width / 2.0
        for i, x in enumerate(x_coords):
            for j in range(len(self.stories)):
                y_bot = y_coords[j]
                y_top = y_coords[j + 1]

                # Contorno de hormigón (2 líneas verticales)
                doc.line((x - hw, y_bot), (x - hw, y_top), layer=Layer.CONCRETE, lineweight=0.50)
                doc.line((x + hw, y_bot), (x + hw, y_top), layer=Layer.CONCRETE, lineweight=0.50)

                # Armadura longitudinal de columna (2 líneas verticales en caras)
                x_rebar_l = x - hw + self.cover
                x_rebar_r = x + hw - self.cover
                doc.line((x_rebar_l, y_bot), (x_rebar_l, y_top), layer=Layer.REBAR, lineweight=0.35)
                doc.line((x_rebar_r, y_bot), (x_rebar_r, y_top), layer=Layer.REBAR, lineweight=0.35)

                # Estribos de columna en altura libre (entre cara superior de piso y fondo de viga superior)
                h_clear = (y_top - self.beam_height) - y_bot
                n_crit = int(self.col_lc_critical // self.col_s_critical)
                h_cent = max(0.0, h_clear - 2.0 * self.col_lc_critical)
                n_cent = int(h_cent // self.col_s_central)

                # Zona crítica inferior
                for k in range(n_crit):
                    y_st = y_bot + (k + 1) * self.col_s_critical
                    doc.line((x_rebar_l, y_st), (x_rebar_r, y_st), layer=Layer.STIRRUP, lineweight=0.18)

                # Zona central
                y_cent_start = y_bot + self.col_lc_critical
                for k in range(n_cent):
                    y_st = y_cent_start + (k + 1) * self.col_s_central
                    doc.line((x_rebar_l, y_st), (x_rebar_r, y_st), layer=Layer.STIRRUP, lineweight=0.18)

                # Zona crítica superior
                y_top_crit_start = y_top - self.beam_height - self.col_lc_critical
                for k in range(n_crit):
                    y_st = y_top_crit_start + (k + 1) * self.col_s_critical
                    doc.line((x_rebar_l, y_st), (x_rebar_r, y_st), layer=Layer.STIRRUP, lineweight=0.18)

                # Etiqueta de columna
                col_label = f"C{i+1}-P{j+1}"
                doc.text((x - 120.0, y_bot + h_clear / 2.0), col_label, height=70.0, layer=Layer.TEXT)

        # ------------------------------------------------------------------
        # 4. Vigas: contorno de hormigón y armado
        # ------------------------------------------------------------------
        for i in range(len(self.bays)):
            x_left_col = x_coords[i] + hw
            x_right_col = x_coords[i + 1] - hw
            l_clear = x_right_col - x_left_col

            for j in range(len(self.stories)):
                y_floor = y_coords[j + 1]
                y_beam_bot = y_floor - self.beam_height

                # Contorno de hormigón de viga (2 líneas horizontales)
                doc.line((x_left_col, y_floor), (x_right_col, y_floor), layer=Layer.CONCRETE, lineweight=0.50)
                doc.line((x_left_col, y_beam_bot), (x_right_col, y_beam_bot), layer=Layer.CONCRETE, lineweight=0.50)

                # Armadura longitudinal de viga (2 líneas horizontales superior e inferior)
                y_rebar_t = y_floor - self.cover
                y_rebar_b = y_beam_bot + self.cover
                doc.line((x_left_col, y_rebar_t), (x_right_col, y_rebar_t), layer=Layer.REBAR, lineweight=0.35)
                doc.line((x_left_col, y_rebar_b), (x_right_col, y_rebar_b), layer=Layer.REBAR, lineweight=0.35)

                # Estribos de viga en vano libre
                n_crit_b = int(self.beam_lc_critical // self.beam_s_critical)
                l_cent = max(0.0, l_clear - 2.0 * self.beam_lc_critical)
                n_cent_b = int(l_cent // self.beam_s_central)

                # Zona crítica izquierda
                for k in range(n_crit_b):
                    x_st = x_left_col + (k + 1) * self.beam_s_critical
                    doc.line((x_st, y_rebar_b), (x_st, y_rebar_t), layer=Layer.STIRRUP, lineweight=0.18)

                # Zona central
                x_cent_start = x_left_col + self.beam_lc_critical
                for k in range(n_cent_b):
                    x_st = x_cent_start + (k + 1) * self.beam_s_central
                    doc.line((x_st, y_rebar_b), (x_st, y_rebar_t), layer=Layer.STIRRUP, lineweight=0.18)

                # Zona crítica derecha
                x_right_crit_start = x_right_col - self.beam_lc_critical
                for k in range(n_crit_b):
                    x_st = x_right_crit_start + (k + 1) * self.beam_s_critical
                    doc.line((x_st, y_rebar_b), (x_st, y_rebar_t), layer=Layer.STIRRUP, lineweight=0.18)

                # Etiqueta de viga
                beam_label = f"V{j+1}0{i+1}"
                doc.text((x_left_col + l_clear / 2.0 - 100.0, y_floor - self.beam_height / 2.0), beam_label, height=70.0, layer=Layer.TEXT)

        # ------------------------------------------------------------------
        # 5. Título general del alzado
        # ------------------------------------------------------------------
        doc.text((x0, y0 - 1000.0), f"ALZADO ESTRUCTURAL — {self.axis_name.upper()} ({self.label})", height=150.0, layer=Layer.TEXT)

        doc.save()
        return doc


__all__ = ["FrameElevationDetail"]
