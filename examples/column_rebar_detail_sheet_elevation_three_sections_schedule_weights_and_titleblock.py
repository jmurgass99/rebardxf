"""Plano de despiece de un pilar: alzado con las marcas, tres secciones (base, media, cabeza), planilla con pesos y cajetín, en un solo DXF.

`ColumnRebarDetail` recibe las marcas de barra (`ColumnRebarBar`: marca, Ø, longitud, cantidad,
forma) y `render_column_rebar_detail` compone la hoja. El peso de cada marca es ρ·A·L·n con
7850 kg/m³. Se comprueba el peso a mano, se cuentan las entidades del DXF y se pasa el mismo pilar
por el servicio `draw_column_rebar`. Las secciones dibujan todas las barras del perímetro (se
cuenta en el DXF); el alzado dibuja una línea por marca, no por barra.

Ejecutar:  python examples/column_rebar_detail_sheet_elevation_three_sections_schedule_weights_and_titleblock.py
"""
import math
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import ColumnRebarBar, ColumnRebarDetail, render_column_rebar_detail
from rebardxf.services import ColumnRebarInput, draw_column_rebar
from rebardxf.services.column_drawings import _BarSpec

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    H = 3600.0
    longit = [ColumnRebarBar("L1", 20.0, (H + 600.0) / 1000.0, 8, "L1"), ColumnRebarBar("L2", 16.0, 1.20, 4, "L1")]
    estribos = [ColumnRebarBar("E1", 10.0, 1.84, 26, "51"), ColumnRebarBar("E2", 10.0, 1.84, 6, "51")]
    det = ColumnRebarDetail(name="C-7", b_mm=500.0, h_mm=500.0, H_mm=H, cover_mm=40.0, longitudinal=longit, stirrups=estribos, project="Edificio de oficinas — Bloque B", drawn_by="JM")
    p = render_column_rebar_detail(det, OUT / "C-7_despiece.dxf")
    print(f"Pilar {det.name} {det.b_mm:.0f} × {det.h_mm:.0f} mm, H = {det.H_mm:.0f} mm, recubrimiento {det.cover_mm:.0f} mm")
    print(f"  {'marca':>5} {'Ø':>3} {'L [m]':>6} {'n':>3} {'forma':>5} {'kg/m':>7} {'peso [kg]':>9}")
    total = 0.0
    for bar in longit + estribos:
        wpm = 7850 * math.pi * (bar.diameter_mm / 1000) ** 2 / 4
        total += bar.weight_kg
        print(f"  {bar.mark:>5} {bar.diameter_mm:3.0f} {bar.length_m:6.2f} {bar.quantity:3d} {bar.shape:>5} {wpm:7.3f} {bar.weight_kg:9.1f}")
    print(f"  TOTAL = {total:.1f} kg; comprobación L1: 7850·π·0,02²/4·4,20·8 = {7850 * math.pi * 0.02 ** 2 / 4 * 4.2 * 8:.1f} kg; Ø10 pesa {7850 * math.pi * 0.01 ** 2 / 4:.3f} kg/m (tabla 0,617)")
    dxf = ezdxf.readfile(str(p))
    cnt = Counter(e.dxftype() for e in dxf.modelspace())
    capas = Counter(e.dxf.layer for e in dxf.modelspace())
    print(f"\nDXF {p.name}: {dict(cnt)}; por capa {dict(capas)}")
    textos = [t.dxf.text for t in dxf.modelspace().query("TEXT")]
    print(f"  Textos de cabecera y planilla: {[t for t in textos if t.startswith(('ALZADO', 'PLANILLA', 'TOTAL', 'Proyecto', 'Elemento'))]}")
    secciones = [t for t in textos if t in ('BASE', 'MEDIA', 'CABEZA')]
    n_barras = sum(b.quantity for b in longit)
    print(f"  Secciones: {secciones}; círculos dibujados = {cnt['CIRCLE']} = {len(secciones)} secciones × {cnt['CIRCLE'] // max(len(secciones), 1)} "
          f"por sección; barras reales = {n_barras} → {'todas dibujadas en cada corte' if cnt['CIRCLE'] == len(secciones) * n_barras else 'NO coinciden'}")
    meta = draw_column_rebar(ColumnRebarInput(name="C-8", b_mm=400.0, h_mm=600.0, H_mm=3200.0, cover_mm=40.0,
                                              longitudinal=[_BarSpec("L1", 25.0, 3.80, 10)], stirrups=[_BarSpec("E1", 10.0, 1.84, 24)], project="Bloque B", drawn_by="JM"), OUT / "C-8_despiece.dxf")
    print(f"\nServicio draw_column_rebar C-8: total {meta['total_kg']} kg, {meta['n_longitudinal']} marcas longitudinales, {meta['n_stirrups']} de estribo → {Path(meta['path']).name}")
    print("\nLa planilla y el cajetín salen en el mismo espacio modelo que el alzado (unidades mm); para una lámina con cajetín en espacio papel se usa `SheetTemplate.apply_to_layout` sobre este documento.")


if __name__ == "__main__":
    main()
