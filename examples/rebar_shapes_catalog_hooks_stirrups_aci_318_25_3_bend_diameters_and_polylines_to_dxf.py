"""Catálogo de formas de barra: diámetros mínimos de doblado de ACI 318-19 §25.3 por designación y tipo de gancho, vértices de ganchos, cercos y barras en L/U, y su inserción como polilíneas en un DXF.

`min_bend_diameter_aci` devuelve D = 6Ø (#3–#8), 8Ø (#9–#11) y 10Ø (#14, #18) para ganchos
estándar, 4Ø (#3–#5) y 6Ø (#6–#8) para cercos, 6Ø/8Ø para ganchos sísmicos; acepta #, M y mm.
Las formas (`hook_90`, `hook_135`, `closed_stirrup`, `open_stirrup`, `L_shape`, `U_shape`) devuelven
vértices por el eje de la barra con los arcos discretizados; con `bar=` usan la tabla ACI y sin él
la aproximación heredada (3Ø, 4Ø, 5Ø). Se insertan en un `DXFDocument` con `insert_polyline`.

Ejecutar:  python examples/rebar_shapes_catalog_hooks_stirrups_aci_318_25_3_bend_diameters_and_polylines_to_dxf.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import rebar_shapes as rs
from rebardxf.core import DXFDocument

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def main() -> None:
    print("Diámetro interior mínimo de doblado D [mm] (ACI 318-19 §25.3) y D/Ø:")
    print(f"  {'barra':>6} {'Ø [mm]':>7} {'gancho 90/180':>13} {'cerco 90/135':>12} {'sísmico':>8}")
    for bar in ("#3", "#4", "#5", "#6", "#8", "#9", "#11", "#14", "M10", "M16", "M25", 12, 32):
        imp, db = rs._resolve_bar(bar)
        std = rs.min_bend_diameter_aci(bar, "standard_90")
        try:
            stir = f"{rs.min_bend_diameter_aci(bar, 'stirrup_135'):6.1f} ({rs.min_bend_diameter_aci(bar, 'stirrup_135') / db:.0f}Ø)"
        except NotImplementedError:
            stir = "no tabulado"
        try:
            seis = f"{rs.min_bend_diameter_aci(bar, 'seismic'):5.1f}"
        except NotImplementedError:
            seis = "—"
        print(f"  {str(bar):>6} {db:7.2f} {std:7.1f} ({std / db:.0f}Ø) {stir:>12} {seis:>8}   (tabla como {imp})")
    print(f"  Extensión de la cola: 90° máx(12Ø, 150) = {rs.hook_extension(16, 90):.0f} mm para Ø16; 135° máx(6Ø, 75) = {rs.hook_extension(10, 135):.0f} para Ø10; 180° máx(4Ø, 65) = {rs.hook_extension(20, 180):.0f} para Ø20\n")

    formas = [("hook_90 Ø16 pierna 600 (ACI)", rs.hook_90(600.0, 16.0, bar="M16")), ("hook_90 Ø16 pierna 600 (legacy 3Ø)", rs.hook_90(600.0, 16.0)),
              ("hook_135 Ø10 pierna 300", rs.hook_135(300.0, 10.0, bar="M10")), ("closed_stirrup 300×500 c30 Ø10", rs.closed_stirrup(300.0, 500.0, 30.0, 10.0, bar="M10")),
              ("open_stirrup 300×500 c30 Ø10", rs.open_stirrup(300.0, 500.0, 30.0, 10.0, bar="M10")), ("L_shape 1000+500 Ø16", rs.L_shape(1000.0, 500.0, 16.0)),
              ("U_shape ancho 240 patas 400 Ø12", rs.U_shape(240.0, 400.0, 12.0)), ("S_shape 300/60/300 Ø12", rs.S_shape(300.0, 60.0, 300.0, 12.0))]
    print(f"  {'forma':38} {'vértices':>8} {'ancho × alto caja [mm]':>22} {'radio interior usado':>20}")
    for nombre, pts in formas:
        w, h = bbox(pts)
        r = rs.min_bend_diameter_aci("M16", "standard_90") / 2 if "(ACI)" in nombre else (rs.bend_radius(16.0) if "legacy" in nombre or "L_shape" in nombre else "")
        print(f"  {nombre:38} {len(pts):8d} {f'{w:.0f} × {h:.0f}':>22} {str(r if r == '' else f'{r:.1f} mm'):>20}")
    doc = DXFDocument(str(OUT / "formas_barra.dxf"))
    y = 0.0
    for nombre, pts in formas:
        rs.insert_polyline(doc, [(x, py + y) for x, py in pts], layer="ARMADURA", lineweight=35)
        doc.text((0.0, y - 60.0), nombre, height=30.0)
        y += bbox(pts)[1] + 250.0
    doc.save()
    cnt = Counter(e.dxftype() for e in ezdxf.readfile(str(OUT / "formas_barra.dxf")).modelspace())
    print(f"\nDXF formas_barra.dxf: {dict(cnt)} ({len(formas)} polilíneas, una por forma, en la capa ARMADURA)")
    print(f"Catálogo por nombre: {sorted(rs.ShapeCatalog.get(n) is not None for n in ('straight', 'L', 'U', 'S', 'hook90', 'hook135', 'stirrup', 'open_stirrup'))}; p. ej. ShapeCatalog.get('hook90')(leg=500, db=16) → {len(rs.ShapeCatalog.get('hook90')(leg=500, db=16))} vértices")
    print("\nCon `bar=` el radio sale de la tabla ACI (Ø16 cerco: 4Ø → r = 32 mm; gancho estándar 6Ø → 48 mm); sin él la aproximación heredada da 3Ø. Las formas L, U y S aún no aceptan `bar=` y usan siempre la heredada: para una planilla normativa pásalas por `rebar_cut_length` con el D de la tabla.")


if __name__ == "__main__":
    main()
