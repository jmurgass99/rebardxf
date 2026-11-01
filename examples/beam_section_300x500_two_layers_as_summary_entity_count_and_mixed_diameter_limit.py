"""Sección transversal de una viga 300 × 500 con dos capas de armado a DXF: posiciones de barra, A_s por capa, recuento de entidades y el límite con diámetros mezclados.

`BeamDetail` dibuja el contorno de hormigón con tramado, el estribo al recubrimiento, las barras
superiores e inferiores como círculos y el rótulo con A_s. Las posiciones en x se reparten en el
ancho útil b − 2·(c + Ø_e + Ø/2). Se comprueba el DXF releído con ezdxf (líneas, círculos, textos,
tramado) y con `verify`. Segundo caso: capa inferior 2Ø20 + 1Ø16 → el paquete dibuja los tres
círculos con el primer diámetro del grupo (Ø20) aunque A_s sí suma los dos: es un límite del
dibujo, no del cálculo.

Ejecutar:  python examples/beam_section_300x500_two_layers_as_summary_entity_count_and_mixed_diameter_limit.py
"""
import math
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import BeamDetail
from rebardxf.export import verify

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    beam = BeamDetail(b=300.0, h=500.0, cover=30.0, bars_top=[(16.0, 2)], bars_bot=[(20.0, 3)], db_stirrup=10.0,
                      s_critical=100.0, s_central=200.0, span=6000.0, lc_critical=1000.0, label="V-101", fc=28.0, Fy=420.0)
    path = OUT / "V-101_section.dxf"
    doc = beam.draw_section(str(path))
    s = beam.summary()
    print(f"Viga {s['label']}: {s['b_mm']:.0f} × {s['h_mm']:.0f} mm, recubrimiento {s['cover_mm']:.0f} mm, estribo Ø{beam.db_stirrup:.0f}")
    print(f"  Armado superior {s['bars_top']} → A_s = {s['As_top_mm2']:.1f} mm² (2·π·16²/4 = {2 * math.pi * 16 ** 2 / 4:.1f}); inferior {s['bars_bot']} → A_s = {s['As_bot_mm2']:.1f} mm² (3·π·20²/4 = {3 * math.pi * 20 ** 2 / 4:.1f})")
    d = beam.cover + beam.db_stirrup + 20.0 / 2
    print(f"  Posiciones x de las 3 barras inferiores (ancho útil b − 2·(c + Ø_e + Ø/2) = {beam.b - 2 * d:.0f} mm): {[round(x) for x in beam._bar_x_positions(3)]} mm; cota y = c + Ø_e + Ø/2 = {beam.cover + beam.db_stirrup + 10:.0f} mm")
    print(f"  Cuantía ρ = A_s,inf/(b·d) con d = h − c − Ø_e − Ø/2 = {beam.h - d:.0f} mm → {s['As_bot_mm2'] / (beam.b * (beam.h - d)) * 100:.2f} %")
    ent = doc.n_entities()
    dxf = ezdxf.readfile(str(path))
    cnt = Counter(e.dxftype() for e in dxf.modelspace())
    print(f"\nDXF {path.name}: contador interno {ent}; releído con ezdxf {dict(cnt)}; verify → {verify(path)}")
    print(f"  Capas presentes: {sorted({e.dxf.layer for e in dxf.modelspace()})}")
    print(f"  Textos: {[t.dxf.text for t in dxf.modelspace().query('TEXT')]}")

    mixed = BeamDetail(b=300.0, h=500.0, cover=30.0, bars_top=[(16.0, 2)], bars_bot=[(20.0, 2), (16.0, 1)], db_stirrup=10.0, label="V-102")
    p2 = OUT / "V-102_section.dxf"
    mixed.draw_section(str(p2))
    radios = sorted({round(c.dxf.radius, 1) for c in ezdxf.readfile(str(p2)).modelspace().query("CIRCLE")})
    print(f"\nViga V-102 con capa inferior 2Ø20 + 1Ø16: A_s,inf = {mixed.as_bot():.1f} mm² (correcto), pero los radios dibujados son {radios} mm: "
          f"las tres barras inferiores salen con Ø20 porque el dibujo usa el primer diámetro de cada capa. Para mezclar diámetros en el plano, usa `integration.fastsap_bridge.RCSectionDesign` (barra a barra).")


if __name__ == "__main__":
    main()
