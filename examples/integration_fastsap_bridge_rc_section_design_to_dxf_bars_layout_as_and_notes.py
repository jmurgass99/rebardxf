"""Puente desde un diseño de sección (como lo devuelve un dimensionador: barras con posición y diámetro) al DXF de la sección con cotas y anotaciones, sin importar el dimensionador.

`RCSectionDesign` es un dataclass neutro (b, h, recubrimiento, barras con x, y, Ø, estribo); el
ayudante `build_rectangular_section_design` lo construye desde n barras por fila y columna (sin
duplicar esquinas: 2·n_x + 2·(n_y − 2)), y `draw_section_dxf` dibuja contorno, estribo, barras
rellenas, cotas y el bloque de texto con A_s y ρ. Se generan un pilar 500 × 600 con 3 × 4 barras,
una viga con barras de dos diámetros colocadas a mano y los errores de entrada.

Ejecutar:  python examples/integration_fastsap_bridge_rc_section_design_to_dxf_bars_layout_as_and_notes.py
"""
import math
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf.integration import RCSectionDesign, RebarBar, build_rectangular_section_design, draw_section_dxf

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    d = build_rectangular_section_design("P-12", b_mm=500.0, h_mm=600.0, cover_mm=40.0, n_bars_x=3, n_bars_y=4, bar_dia_mm=25.0, tie_dia_mm=10.0, tie_spacing_mm=150.0, fc_MPa=30.0, fy_MPa=500.0)
    print(f"Sección {d.section_id} {d.b_mm:.0f} × {d.h_mm:.0f}, recubrimiento {d.cover_mm:.0f}, estribo Ø{d.tie_diameter_mm:.0f}@{d.tie_spacing_mm:.0f}: {len(d.bars)} barras Ø{d.bars[0].diameter_mm:.0f} = 2·3 + 2·(4 − 2)")
    off = d.cover_mm + d.tie_diameter_mm + d.bars[0].diameter_mm / 2
    print(f"  Centro de la primera barra a c + Ø_e + Ø/2 = {off:.1f} mm del borde; posiciones (x, y): {sorted((round(b.x_mm), round(b.y_mm)) for b in d.bars)}")
    p = OUT / "P-12_bridge.dxf"
    res = draw_section_dxf(d, str(p), scale=1.0, add_dimensions=True, add_annotations=True)
    As = sum(math.pi * b.diameter_mm ** 2 / 4 for b in d.bars)
    print(f"  Resultado: {res.n_bars} barras, A_s = {res.total_As_mm2:.0f} mm² (a mano {As:.0f}), ρ = {As / (d.b_mm * d.h_mm) * 100:.2f} %; notas {res.notes}")
    dxf = ezdxf.readfile(str(p))
    cnt = Counter(e.dxftype() for e in dxf.modelspace())
    print(f"  DXF {p.name}: {dict(cnt)}; capas {sorted({e.dxf.layer for e in dxf.modelspace()})}; textos {[t.dxf.text for t in dxf.modelspace().query('TEXT')]}")
    bars = (RebarBar(55.0, 55.0, 20.0), RebarBar(150.0, 55.0, 16.0), RebarBar(245.0, 55.0, 20.0), RebarBar(55.0, 445.0, 16.0), RebarBar(245.0, 445.0, 16.0))
    viga = RCSectionDesign("V-7", b_mm=300.0, h_mm=500.0, cover_mm=30.0, bars=bars, tie_diameter_mm=10.0, tie_spacing_mm=100.0, concrete_fc_MPa=28.0, steel_fy_MPa=420.0)
    r2 = draw_section_dxf(viga, str(OUT / "V-7_bridge.dxf"))
    radios = sorted({round(c.dxf.radius, 1) for c in ezdxf.readfile(str(OUT / "V-7_bridge.dxf")).modelspace().query("CIRCLE")})
    print(f"\nViga V-7 con barras colocadas a mano (2Ø20 + 1Ø16 abajo, 2Ø16 arriba): A_s = {r2.total_As_mm2:.0f} mm²; radios dibujados {radios} mm → aquí sí se respeta cada diámetro (lo que `BeamDetail` no hace)")
    print("  Aviso: la anotación del bloque de texto dice «5 bars phi20» tomando el Ø de la primera barra; con diámetros mezclados hay que leer A_s, no esa línea.")
    for kwargs, desc in ((dict(n_bars_x=1, n_bars_y=2), "n_bars_x = 1"), (dict(cover_mm=200.0), "recubrimiento + estribo + barra ≥ b/2"), (dict(b_mm=-1.0), "b negativo")):
        base = dict(section_id="X", b_mm=300.0, h_mm=400.0, cover_mm=40.0, n_bars_x=2, n_bars_y=2, bar_dia_mm=16.0, tie_dia_mm=8.0, tie_spacing_mm=150.0)
        base.update(kwargs)
        try:
            build_rectangular_section_design(**base)
        except ValueError as exc:
            print(f"  {desc} → ValueError: {exc}")
    try:
        draw_section_dxf(RCSectionDesign("vacia", 300, 400, 40, (), 8, 150), str(OUT / "x.dxf"))
    except ValueError as exc:
        print(f"  Sección sin barras → ValueError: {exc}")
    print("\nEl puente no importa el dimensionador: cualquier programa que entregue barras con (x, y, Ø) puede pintar su sección. Las capas aquí son CONCRETE/REBAR/TIE/DIM/TEXT (inglés), distintas del registro CONCRETO/ARMADURA del resto del paquete.")


if __name__ == "__main__":
    main()
