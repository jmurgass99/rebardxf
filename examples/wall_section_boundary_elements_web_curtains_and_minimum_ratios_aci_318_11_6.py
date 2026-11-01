"""Sección horizontal de un muro de cortante de 4 m con elementos de borde: dos cortinas de alma, cuantías ρ_v, ρ_h y ρ_be frente a los mínimos (ACI 318 §11.6) y el DXF resultante.

`WallDetail` dibuja el muro, los dos elementos de borde con su estribo cerrado y barras longitudinales,
las barras verticales del alma como puntos en dos cortinas y las horizontales como líneas. Calcula
ρ_v = 2·A_b·(1000/s)/(t_w·1000), ρ_h igual y ρ_be = n·A_b/(t_w·L_be) y los compara con 0,25 % (alma) y
1 % (borde). Se barre la separación del alma de 150 a 350 mm para ver dónde se incumple el mínimo
y se pasa el mismo muro por el servicio `draw_wall_section`.

Ejecutar:  python examples/wall_section_boundary_elements_web_curtains_and_minimum_ratios_aci_318_11_6.py
"""
import math
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import WallDetail
from rebardxf.services import WallSectionInput, draw_wall_section
from rebardxf.wall_detail import RHO_BE_MIN, RHO_MIN_HORIZONTAL, RHO_MIN_VERTICAL

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    wall = WallDetail(Lw=4000.0, tw=250.0, Lbe=600.0, n_bars_be=8, db_be=20.0, db_web_v=12.0, db_web_h=12.0, s_web_v=200.0, s_web_h=200.0, db_stirrup=10.0, cover=30.0, label="M-1", fc=28.0, Fy=420.0)
    s = wall.summary()
    print(f"Muro {s['label']}: L_w = {s['Lw_mm']:.0f}, t_w = {s['tw_mm']:.0f}, L_be = {s['Lbe_mm']:.0f} mm; borde {s['n_bars_be']}Ø{s['db_be_mm']:.0f}; alma Ø12 c/200 en dos cortinas")
    print(f"  ρ_be = 8·π·20²/4/(250·600) = {8 * math.pi * 400 / 4 / (250 * 600) * 100:.2f} % (paquete {s['rho_be_pct']:.3f}, mínimo {RHO_BE_MIN * 100:.0f} %) → {'cumple' if s['check_be'] else 'NO cumple'}")
    print(f"  ρ_v = 2·(π·12²/4)·(1000/200)/(250·1000) = {2 * math.pi * 144 / 4 * 5 / 250e3 * 100:.3f} % (paquete {s['rho_v_pct']:.3f}, mínimo {RHO_MIN_VERTICAL * 100:.2f} %) → {'cumple' if s['check_v'] else 'NO cumple'}; ρ_h = {s['rho_h_pct']:.3f} % → {'cumple' if s['check_h'] else 'NO cumple'}")
    p = OUT / "M-1_section.dxf"
    doc = wall.draw(str(p))
    cnt = Counter(e.dxftype() for e in ezdxf.readfile(str(p)).modelspace())
    n_web = int((wall.Lw - 2 * wall.Lbe) // wall.s_web_v)
    print(f"\nDXF {p.name}: {dict(cnt)}; círculos = 2 bordes × 8 + 2 cortinas × {n_web} puntos de alma = {16 + 2 * n_web}; contador interno {doc.n_entities()}")
    print("\nBarrido de la separación del alma (Ø12, dos cortinas, t_w = 250):")
    print(f"  {'s [mm]':>6} {'ρ_v [%]':>7} {'mínimo':>7}  veredicto")
    for sv in (150.0, 200.0, 250.0, 300.0, 350.0):
        w = WallDetail(Lw=4000.0, tw=250.0, Lbe=600.0, s_web_v=sv, s_web_h=sv)
        print(f"  {sv:6.0f} {w.rho_web_v() * 100:7.3f} {RHO_MIN_VERTICAL * 100:7.2f}  {'cumple' if w.rho_web_v() >= RHO_MIN_VERTICAL else 'NO cumple (ρ_v < 0,25 %)'}")
    meta = draw_wall_section(WallSectionInput(label="M-2", Lw_mm=6000.0, tw_mm=300.0, Lbe_mm=800.0, n_bars_be=10, db_be_mm=25.0, s_web_v_mm=150.0, s_web_h_mm=150.0), OUT / "M-2_section.dxf")
    print(f"\nServicio draw_wall_section M-2 (6 m × 0,3 m, borde 10Ø25, alma Ø12 c/150): {meta['n_total_entities']} entidades; ρ_be = {meta['summary']['rho_be_pct']:.2f} %, ρ_v = {meta['summary']['rho_v_pct']:.3f} %")
    try:
        draw_wall_section(WallSectionInput(Lw_mm=1000.0, Lbe_mm=600.0), OUT / "M-x.dxf")
    except Exception as exc:  # noqa: BLE001
        print(f"  Bordes que no caben (2·600 ≥ 1000) → {type(exc).__name__}: {exc}")
    print("\nCon Ø12 en dos cortinas y t_w = 250 el 0,25 % de ACI 318 §11.6.2 se cumple hasta s ≈ 360 mm; la norma limita además s ≤ mín(l_w/5, 3·t_w, 450 mm) y EC8 §5.4.3.5 pide 0,2–0,3 % según la zona: el paquete solo comprueba la cuantía y rotula los valores para que el revisor los vea en el plano. El elemento de borde no se dimensiona aquí (longitud y confinamiento son datos).")


if __name__ == "__main__":
    main()
