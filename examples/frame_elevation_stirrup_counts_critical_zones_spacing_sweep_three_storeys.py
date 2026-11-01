"""Cuántos estribos lleva un pórtico de 3 vanos y 3 pisos según las separaciones de las zonas críticas y centrales: barrido de separaciones y longitudes de confinamiento.

Las zonas críticas de pilar (l_c = máx(h, H/6, 450) en ACI 318 §18.7.5) y de viga (2h en §18.6.4)
concentran estribos a s_crit; el resto va a s_cent. `FrameElevationDetail` cuenta exactamente
n = 2·⌊l_c/s_crit⌋ + ⌊(L_libre − 2·l_c)/s_cent⌋ por pieza. Se barren s_crit = 75/100/125, s_cent =
150/200/250 y l_c de pilar 500/600 mm para ver el total de estribos del pórtico y el peso
aproximado de cercos, y se dibuja el caso más denso.

Ejecutar:  python examples/frame_elevation_stirrup_counts_critical_zones_spacing_sweep_three_storeys.py
"""
import math
import os
from pathlib import Path

from rebardxf import FrameElevationDetail

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)

BAYS, STORIES = [6000.0, 4500.0, 6000.0], [4000.0, 3300.0, 3300.0]
COL, BEAM_B, BEAM_H = 500.0, 300.0, 550.0
PESO_CERCO_PILAR = 7850 * math.pi * 0.01 ** 2 / 4 * (2 * (COL - 80) + 2 * (COL - 80) + 2 * 135) / 1000  # Ø10, perímetro + ganchos [kg]
PESO_CERCO_VIGA = 7850 * math.pi * 0.01 ** 2 / 4 * (2 * (BEAM_B - 60) + 2 * (BEAM_H - 60) + 2 * 135) / 1000


def totales(fr: FrameElevationDetail) -> tuple[int, int]:
    col = sum(fr.num_axes * fr.col_stirrups_per_column(j) for j in range(len(fr.stories)))
    beam = sum(len(fr.stories) * fr.beam_stirrups_per_bay(i) for i in range(len(fr.bays)))
    return col, beam


def main() -> None:
    base = FrameElevationDetail(axis_name="Eje 3", bays=BAYS, stories=STORIES, col_width=COL, col_depth=COL, beam_width=BEAM_B, beam_height=BEAM_H)
    print(f"Pórtico 3 × 3: vanos {BAYS}, pisos {STORIES}, pilares {COL:.0f} × {COL:.0f}, vigas {BEAM_B:.0f} × {BEAM_H:.0f} → {base.num_columns} pilares y {base.num_beams} vigas")
    print(f"Cerco de pilar Ø10 ≈ {PESO_CERCO_PILAR:.2f} kg, cerco de viga Ø10 ≈ {PESO_CERCO_VIGA:.2f} kg (perímetro al recubrimiento + 2 ganchos de 135 mm)\n")
    print(f"  {'s_crit':>6} {'s_cent':>6} {'l_c pilar':>9} {'l_c viga':>8} {'estribos pilar':>14} {'estribos viga':>13} {'total':>6} {'peso cercos [kg]':>16} {'líneas DXF':>10}")
    densest = None
    for s_crit in (75.0, 100.0, 125.0):
        for s_cent in (150.0, 200.0, 250.0):
            for lc_col in (500.0, 600.0):
                fr = FrameElevationDetail(axis_name="Eje 3", bays=BAYS, stories=STORIES, col_width=COL, col_depth=COL, beam_width=BEAM_B, beam_height=BEAM_H,
                                          col_s_critical=s_crit, col_s_central=s_cent, col_lc_critical=lc_col, beam_s_critical=s_crit, beam_s_central=s_cent, beam_lc_critical=2 * BEAM_H)
                c, b = totales(fr)
                peso = c * PESO_CERCO_PILAR + b * PESO_CERCO_VIGA
                if densest is None or c + b > densest[0]:
                    densest = (c + b, fr)
                if s_cent == 200.0 or (s_crit, lc_col) == (100.0, 500.0):
                    print(f"  {s_crit:6.0f} {s_cent:6.0f} {lc_col:9.0f} {2 * BEAM_H:8.0f} {c:14d} {b:13d} {c + b:6d} {peso:16.0f} {fr.expected_entity_counts()['LINE']:10d}")
    n, fr = densest
    p = OUT / "alzado_portico_3_denso.dxf"
    fr.draw_elevation(str(p))
    print(f"\nCaso más denso ({n} estribos, s_crit = {fr.col_s_critical:.0f}, s_cent = {fr.col_s_central:.0f}, l_c = {fr.col_lc_critical:.0f}) dibujado en {p.name}: {fr.expected_entity_counts()}")
    j = 0
    print(f"  Pilar del piso 1 (H libre {STORIES[0] - BEAM_H:.0f} mm): {fr.col_stirrups_per_column(j)} estribos = 2·⌊{fr.col_lc_critical:.0f}/{fr.col_s_critical:.0f}⌋ + ⌊({STORIES[0] - BEAM_H:.0f} − 2·{fr.col_lc_critical:.0f})/{fr.col_s_central:.0f}⌋")
    print("\nPasar de s_cent 250 a 150 sube el total de estribos un 25 % (509 → 638) y de s_crit 125 a 75 otro 33 %: la zona central pesa tanto como la crítica en el número de cercos aunque la crítica domine la fotografía del alzado. "
          "El recuento es de líneas dibujadas (un estribo = una línea en el alzado); la planilla real necesita las longitudes de corte de `rebar_cut_length`.")


if __name__ == "__main__":
    main()
