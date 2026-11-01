"""Cuadro de pilares clásico (plantas × pilares) con la sección a escala en cada celda: estadísticas exactas de entidades, comprobación contra el DXF y validación de armados imposibles.

`ColumnScheduleDrawer` dibuja la cuadrícula, los rótulos de planta y pilar y, en cada celda, el
contorno, el estribo, las barras (esquinas + intermedias repartidas en caras) y dos líneas de texto
(«40x40 cm - 8Ø20», «e: Ø10 c/15cm»). Devuelve `ColumnScheduleStats` con el recuento por tipo, que
se compara con el DXF releído; los círculos son exactamente la suma de n_bars. Un número de barras
impar o menor que 4 lanza ValueError.

Ejecutar:  python examples/schedule_grid_column_schedule_three_columns_two_storeys_exact_entities_and_validation.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import ColumnScheduleDrawer, ColumnStorySpec

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    columns, stories = ["P-1", "P-2", "P-3", "P-4"], ["Cimentación", "Planta 1", "Planta 2", "Cubierta"]
    specs = {}
    plan = {"P-1": [(500, 500, 12, 25, 10, 100), (450, 450, 8, 25, 10, 150), (400, 400, 8, 20, 8, 150), (350, 350, 4, 16, 8, 200)],
            "P-2": [(600, 400, 10, 25, 10, 100), (500, 400, 8, 20, 10, 150), (450, 400, 8, 20, 8, 150), (400, 400, 6, 16, 8, 200)],
            "P-3": [(500, 500, 8, 25, 10, 100), (450, 450, 8, 20, 10, 150), (400, 400, 6, 16, 8, 150), None],
            "P-4": [(400, 400, 8, 20, 10, 100), (400, 400, 8, 16, 8, 150), (350, 350, 4, 16, 8, 200), (350, 350, 4, 12, 8, 200)]}
    for tag, filas in plan.items():
        for story, spec in zip(stories, filas):
            if spec:
                b, h, n, db, dbe, s = spec
                specs[(story, tag)] = ColumnStorySpec(tag, story, b, h, n, db, dbe, s)
    drawer = ColumnScheduleDrawer(columns, stories, specs)
    p = OUT / "cuadro_pilares.dxf"
    st = drawer.render_to_file(p)
    print(f"Cuadro {len(columns)} pilares × {len(stories)} plantas = {st.total_cells} celdas ({len(specs)} con pilar, {st.total_cells - len(specs)} con «-»)")
    print(f"  Estadísticas: {st.line_entities} líneas, {st.text_entities} textos, {st.circle_entities} círculos → {st.total_entities} entidades")
    n_bars = sum(s.n_bars for s in specs.values())
    print(f"  Círculos = Σ n_bars = {n_bars} → {'coincide' if n_bars == st.circle_entities else 'NO coincide'}")
    n_lines = 2 + len(stories) + 2 + len(columns) + 8 * len(specs)
    print(f"  Líneas = cuadrícula ({2 + len(stories)} horizontales + {2 + len(columns)} verticales) + 8 por celda con pilar ({len(specs)}) = {n_lines} → {'coincide' if n_lines == st.line_entities else 'NO coincide'}")
    n_text = 1 + len(columns) + len(stories) + 2 * len(specs) + (st.total_cells - len(specs))
    print(f"  Textos = 1 + {len(columns)} + {len(stories)} + 2·{len(specs)} + {st.total_cells - len(specs)} = {n_text} → {'coincide' if n_text == st.text_entities else 'NO coincide'}")
    dxf = ezdxf.readfile(str(p))
    cnt = Counter(e.dxftype() for e in dxf.modelspace())
    print(f"  DXF releído: {dict(cnt)}; capas {sorted({e.dxf.layer for e in dxf.modelspace()})}")
    textos = [t.dxf.text for t in dxf.modelspace().query("TEXT")]
    print(f"  Celda P-1 / Cimentación: {[t for t in textos if t.startswith('50x50')]}, {[t for t in textos if t == 'e: Ø10 c/10cm'][:1]}")
    for bad, msg in ((5, "impar"), (2, "menos de 4")):
        try:
            ColumnScheduleDrawer(["X"], ["S"], {("S", "X"): ColumnStorySpec("X", "S", 400, 400, bad, 16)}).render_to_file(OUT / "x.dxf")
        except ValueError as exc:
            print(f"  n_bars = {bad} ({msg}) → ValueError: {str(exc)[:70]}…")
    print("\nLa miniatura reparte las barras intermedias solo en las caras superior e inferior: para 12Ø25 dibuja 4 esquinas + 4 + 4; el pilar rectangular 600 × 400 con 10 barras sale con 3 intermedias por cara larga. "
          "Es un cuadro de obra (dimensiones en cm, estribo en cm), no un despiece: el despiece va en `column_rebar_detail`.")


if __name__ == "__main__":
    main()
