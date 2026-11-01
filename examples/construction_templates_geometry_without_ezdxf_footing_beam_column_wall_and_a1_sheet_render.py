"""Plantillas constructivas como geometría pura (sin ezdxf): zapata, sección de viga, de pilar y de muro, compuestas en una lámina A1 con cajetín y renderizadas a DXF R2010.

`templates_construction` devuelve `TemplateGeometry` (rectángulos, círculos, líneas, textos) que se
puede testar y transformar sin ezdxf; `build_a1_sheet_with_titleblock` coloca varios detalles en la
lámina con sus desplazamientos y `render_a1_sheet_to_dxf` los escribe en capas BORDER/GEOMETRY/
REBAR/TEXT. Se cuentan las primitivas de cada plantilla y las entidades del DXF final.

Ejecutar:  python examples/construction_templates_geometry_without_ezdxf_footing_beam_column_wall_and_a1_sheet_render.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf.templates_construction import (BeamSectionTemplateInput, ColumnSectionTemplateInput, FootingTemplateInput, SheetA1LayoutInput, TitleBlockA1Input,
                                             WallSectionTemplateInput, build_a1_sheet_with_titleblock, build_beam_section_template, build_column_section_template,
                                             build_footing_template, build_title_block_a1, build_wall_section_template, render_a1_sheet_to_dxf)

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def resumen(nombre, g):
    print(f"  {nombre:34} rect {len(g.rectangles):3d}  círc {len(g.circles):3d}  líneas {len(g.lines):3d}  textos {len(g.texts):3d}  → {[t['text'] for t in g.texts][:4]}")
    return g


def main() -> None:
    print("Plantillas (unidades mm del modelo):")
    zap = resumen("zapata 2500 × 2500 × 600, pilar 400", build_footing_template(FootingTemplateInput(B_mm=2500, L_mm=2500, H_mm=600, col_b_mm=400, col_h_mm=400, cover_mm=50)))
    viga = resumen("viga 300 × 500, 3+3Ø16, est Ø10@200", build_beam_section_template(BeamSectionTemplateInput(b_mm=300, h_mm=500, cover_mm=40, n_top=3, n_bot=3, bar_dia_mm=16, stirrup_dia_mm=10, stirrup_spacing_mm=200)))
    pilar = resumen("pilar 400 × 400, 3 × 3 → 8Ø20", build_column_section_template(ColumnSectionTemplateInput(b_mm=400, h_mm=400, cover_mm=40, n_bars_x=3, n_bars_y=3, bar_dia_mm=20, tie_dia_mm=10, tie_spacing_mm=150)))
    muro = resumen("muro 3000 × 200, borde 4Ø16, alma 6", build_wall_section_template(WallSectionTemplateInput(length_mm=3000, thickness_mm=200, cover_mm=40, boundary_bars=4, web_bars=6, bar_dia_mm=16)))
    caj = resumen("cajetín A1 (bloque 180 × 80 mm)", build_title_block_a1(TitleBlockA1Input(project_name="Nave logística", drawing_number="E-02", revision="1", author="JM", scale="1:50")))
    print(f"  La zapata lleva una parrilla fija de 8 × 8 = {len(zap.circles)} puntos (representación, no cálculo); el pilar 3 × 3 da {2 * 3 + 2 * (3 - 2)} barras perimetrales")
    inp = SheetA1LayoutInput(project_name="Nave logística", drawing_title="Detalles de cimentación y pilares", drawing_number="E-02", revision="1", author="JM", scale="1:20")
    # Los detalles van en mm de modelo; para 1:20 se escalan ×1/20 al colocarlos en la lámina (841 × 594 mm de papel)
    def escala(g, f):
        from rebardxf.templates_construction import TemplateGeometry
        return TemplateGeometry(rectangles=[(x * f, y * f, w * f, h * f) for x, y, w, h in g.rectangles], circles=[(x * f, y * f, max(r * f, 0.6)) for x, y, r in g.circles],
                                texts=[{"pos": (t["pos"][0] * f, t["pos"][1] * f), "text": t["text"], "height": max(t.get("height", 2.5) * f, 2.0)} for t in g.texts],
                                lines=[(a * f, b * f, c * f, d * f) for a, b, c, d in g.lines])
    f = 1 / 20
    sheet = build_a1_sheet_with_titleblock(inp, drawings=[(escala(zap, f), (40.0, 300.0)), (escala(viga, f), (260.0, 320.0)), (escala(pilar, f), (330.0, 320.0)), (escala(muro, f), (40.0, 120.0))])
    print(f"\nLámina A1 1:20 con cuatro detalles: {len(sheet.rectangles)} rectángulos, {len(sheet.circles)} círculos, {len(sheet.lines)} líneas, {len(sheet.texts)} textos; cajetín: {[t['text'] for t in sheet.texts[:6]]}")
    p = OUT / "lamina_A1_detalles.dxf"
    render_a1_sheet_to_dxf(sheet, str(p))
    dxf = ezdxf.readfile(str(p))
    cnt = Counter(e.dxftype() for e in dxf.modelspace())
    capas = Counter(e.dxf.layer for e in dxf.modelspace())
    print(f"DXF {p.name} ({dxf.dxfversion}): {dict(cnt)}; por capa {dict(capas)} (los 3 primeros rectángulos y 4 primeras líneas van a BORDER)")
    print("\nEstas plantillas son geometría de referencia (parrilla fija, barras repartidas por reglas simples) pensada para tests y para componer láminas; el detalle normativo con A_s, separaciones y estados de cálculo está en `FoundationPlan`, `BeamDetail` y `ColumnDetail`.")


if __name__ == "__main__":
    main()
