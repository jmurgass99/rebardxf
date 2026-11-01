"""Planta de cimentación con seis zapatas: del A_s requerido al reparto dibujado (n barras, separación) con los límites de separación de ACI 318-19 y EN 1992-1-1, y el cuadro de zapatas.

`layout_rebar_direction` convierte A_s [mm²/m] y Ø en una separación requerida s = A_b/A_s·1000, la
acota entre s_mín (paso libre ≥ máx(Ø, 25 mm, 4/3·d_agg) en ACI; ≥ máx(Ø, 20, d_agg + 5) en EC2) y
s_máx (3h ≤ 450 en ACI; 3h ≤ 400 en EC2) y devuelve n barras y la separación dibujada, de modo que
barras, rótulo «Ø16 c/200» y cuadro coincidan por construcción. `FoundationPlan` dibuja las
zapatas con ejes, pilar y parrilla, y `schedule_table` da el cuadro con el estado de cada una.

Ejecutar:  python examples/foundation_plan_six_footings_rebar_layout_from_as_required_aci_vs_ec2_spacing_limits.py
"""
import math
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import FootingData, FoundationPlan
from rebardxf.foundation_plan import layout_rebar_direction

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    print("layout_rebar_direction para una zapata de B = 2,4 m y h = 0,6 m (recubrimiento 75 mm, árido 20 mm):")
    print(f"  {'A_s [mm²/m]':>11} {'Ø':>3} {'norma':>9} {'s_req [mm]':>10} {'s_mín':>5} {'s_máx':>5} {'n':>3} {'s dibujada':>10} {'rótulo':>6}  estado")
    for As in (600.0, 1150.0, 2400.0):
        for db in (12.0, 16.0, 25.0):
            for code in ("ACI318-19", "EC2"):
                st, n, s_dib, s_rot, reason = layout_rebar_direction(2400.0, 600.0, As, db, 75.0, code, d_agg_mm=20.0)
                Ab = math.pi * db ** 2 / 4
                s_req = Ab / As * 1000
                s_max = min(3 * 600.0, 450.0 if code.startswith("ACI") else 400.0)
                s_min = db + (max(db, 25.0, 4 / 3 * 20.0) if code.startswith("ACI") else max(db, 20.0, 25.0))
                print(f"  {As:11.0f} {db:3.0f} {code:>9} {s_req:10.0f} {s_min:5.0f} {s_max:5.0f} {n:3d} {s_dib:10.1f} {s_rot:6.0f}  {st.value}{' — ' + reason if reason else ''}")
    footings = [FootingData("Z-1", 0.0, 0.0, 2400.0, 2400.0, 600.0, As_x=1150.0, As_y=1150.0, db=16.0, fc=28.0, Fy=420.0, d_agg_mm=20.0),
                FootingData("Z-2", 6000.0, 0.0, 2800.0, 2800.0, 700.0, As_x=1400.0, As_y=1400.0, db=16.0, fc=28.0, Fy=420.0, d_agg_mm=20.0),
                FootingData("Z-3", 12000.0, 0.0, 2000.0, 2000.0, 500.0, As_x=800.0, As_y=800.0, db=12.0, fc=28.0, Fy=420.0, d_agg_mm=20.0),
                FootingData("Z-4", 0.0, 5000.0, 2400.0, 3000.0, 600.0, As_x=1150.0, As_y=1500.0, db=16.0, fc=28.0, Fy=420.0, design_code="EC2", d_agg_mm=20.0),
                FootingData("Z-5", 6000.0, 5000.0, 3200.0, 3200.0, 800.0, As_x=1900.0, As_y=1900.0, db=20.0, fc=28.0, Fy=420.0, design_code="EC2", d_agg_mm=20.0),
                FootingData("Z-6", 12000.0, 5000.0, 2000.0, 2000.0, 500.0, As_x=800.0, As_y=800.0, db=12.0, fc=28.0, Fy=420.0, design_code="EC2", d_agg_mm=20.0)]
    plan = FoundationPlan(footings=footings, column_size=450.0, draw_rebar=True)
    p = OUT / "planta_cimentacion.dxf"
    doc = plan.draw(str(p))
    print("\nCuadro de zapatas (schedule_table):")
    print(f"  {'zapata':>6} {'B × L × h [m]':>18} {'A_s,x / A_s,y':>13} {'Ø':>3} {'norma':>9} {'estado':>17}  rótulo del plano")
    textos = [t.dxf.text for t in ezdxf.readfile(str(p)).modelspace().query("TEXT")]
    for row, f in zip(plan.schedule_table(), footings):
        i = textos.index(f.label)
        rot = next((t for t in textos[i + 1:] if t.startswith("Ø")), "")
        dims = "%.1f × %.1f × %.1f" % (row["B_m"], row["L_m"], row["d_m"])
        as_txt = "%.0f / %.0f" % (row["As_x_mm2_m"], row["As_y_mm2_m"])
        print(f"  {row['label']:>6} {dims:>18} {as_txt:>13} {row['db_mm']:3.0f} {f.design_code:>9} {row['status']:>17}  {rot}")
    cnt = Counter(e.dxftype() for e in ezdxf.readfile(str(p)).modelspace())
    print(f"\nDXF {p.name}: {dict(cnt)}; contador interno {doc.n_entities()}; capas: {sorted({e.dxf.layer for e in ezdxf.readfile(str(p)).modelspace()})}")
    print("\nEl mismo A_s con Ø mayor da menos barras pero puede chocar con s_máx (Ø25 con 600 mm²/m pide 818 mm > 450): el paquete lo marca REQUIERE_REVISION en vez de recortar la separación en silencio. "
          "El parámetro `s_commercial_step_mm` se acepta pero el rótulo redondea al milímetro: el redondeo a múltiplos de 25 mm queda para el delineante.")


if __name__ == "__main__":
    main()
