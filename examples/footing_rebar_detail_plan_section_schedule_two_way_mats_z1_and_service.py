"""Despiece de una zapata aislada 2,4 × 2,4 × 0,6 m con parrilla inferior en dos direcciones y refuerzo superior: planta, sección A-A y planilla en un DXF.

`FootingRebarDetail` recibe las cuatro posiciones (`bottom_x`, `bottom_y`, `top_x`, `top_y`) como
marcas `ColumnRebarBar`; `render_footing_rebar_detail` dibuja la planta con el pilar centrado, la
sección con las barras como círculos y la planilla con pesos. Se deriva el número de barras a partir
de un A_s requerido (A_b·1000/s) y la longitud de corte con patillas de 90° (2·12Ø), y se contrasta
el peso total con la planilla; después el servicio `draw_footing_rebar` para una zapata rectangular.

Ejecutar:  python examples/footing_rebar_detail_plan_section_schedule_two_way_mats_z1_and_service.py
"""
import math
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import ColumnRebarBar, FootingRebarDetail, render_footing_rebar_detail
from rebardxf.services import FootingRebarInput, draw_footing_rebar
from rebardxf.services.footing_drawings import _RebarSpec

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    Lx, Ly, h, cover, db = 2400.0, 2400.0, 600.0, 50.0, 16.0
    As_req = 1150.0  # mm²/m por dirección (del cálculo a flexión)
    Ab = math.pi * db ** 2 / 4
    s_req = Ab / As_req * 1000
    n_bars = math.ceil((Lx - 2 * cover) / s_req) + 1
    s_real = (Lx - 2 * cover) / (n_bars - 1)
    L_cut = (Lx - 2 * cover + 2 * 12 * db) / 1000  # con dos patillas de 90° de 12Ø
    print(f"Zapata Z-1 {Lx:.0f} × {Ly:.0f} × {h:.0f} mm, recubrimiento {cover:.0f} mm; A_s requerido {As_req:.0f} mm²/m por dirección")
    print(f"  Ø{db:.0f}: A_b = {Ab:.1f} mm² → s_req = {s_req:.0f} mm → {n_bars} barras a {s_real:.0f} mm (A_s real {Ab * 1000 / s_real:.0f} mm²/m); longitud de corte con patillas 12Ø: {L_cut:.2f} m")
    bx = ColumnRebarBar("Z1-X", db, L_cut, n_bars, "11")
    by = ColumnRebarBar("Z1-Y", db, L_cut, n_bars, "11")
    tx = ColumnRebarBar("Z1-TX", 12.0, 2.30, 8, "1")
    ty = ColumnRebarBar("Z1-TY", 12.0, 2.30, 8, "1")
    det = FootingRebarDetail(name="Z-1", Lx_mm=Lx, Ly_mm=Ly, h_mm=h, cover_mm=cover, bottom_x=bx, bottom_y=by, top_x=tx, top_y=ty, column_b_mm=500.0, column_h_mm=500.0, project="Nave industrial")
    p = render_footing_rebar_detail(det, OUT / "Z-1_despiece.dxf")
    total = sum(b.weight_kg for b in (bx, by, tx, ty))
    print(f"  Pesos: inferior X {bx.weight_kg:.1f} kg, inferior Y {by.weight_kg:.1f} kg, superior X {tx.weight_kg:.1f}, superior Y {ty.weight_kg:.1f} → total {total:.1f} kg; cuantía {total / (Lx * Ly * h / 1e9):.1f} kg/m³ de hormigón")
    dxf = ezdxf.readfile(str(p))
    cnt = Counter(e.dxftype() for e in dxf.modelspace())
    textos = [t.dxf.text for t in dxf.modelspace().query("TEXT")]
    print(f"\nDXF {p.name}: {dict(cnt)}; planta con {n_bars} + {n_bars} líneas de parrilla, sección con {n_bars} + {tx.quantity} círculos (inferior y superior)")
    print(f"  Títulos: {[t for t in textos if t.startswith(('VISTA', 'SECCION', 'PLANILLA', 'TOTAL'))]}; filas de planilla: {[t for t in textos if t.startswith(('BOT', 'TOP'))]}")
    meta = draw_footing_rebar(FootingRebarInput(name="Z-2", Lx_mm=3000.0, Ly_mm=2000.0, h_mm=700.0, cover_mm=50.0,
                                                bottom_x=_RebarSpec("Z2-X", 20.0, 3.38, 13, "11"), bottom_y=_RebarSpec("Z2-Y", 16.0, 2.38, 17, "11"),
                                                column_b_mm=600.0, column_h_mm=400.0, project="Nave industrial"), OUT / "Z-2_despiece.dxf")
    print(f"\nServicio draw_footing_rebar Z-2 (3,0 × 2,0 × 0,7, Ø20 c/≈240 en X y Ø16 c/≈120 en Y): {meta['total_kg']} kg → {Path(meta['path']).name}")
    try:
        draw_footing_rebar(FootingRebarInput(name="Z-3"), OUT / "Z-3.dxf")
    except Exception as exc:  # noqa: BLE001
        print(f"  Sin ninguna posición de armadura → {type(exc).__name__}: {exc}")
    print("\nEl detalle dibuja lo que se le da (número de barras, longitudes): el reparto a partir de A_s y las longitudes de anclaje son del calculista, aquí hechos a mano; `FoundationPlan` sí deriva el reparto desde A_s con los límites de separación de ACI/EC2.")


if __name__ == "__main__":
    main()
