"""Sección de pilar con 4 a 16 barras: cómo se reparten por el perímetro, cuantía ρ, y el defecto corregido que superponía barras en 12Ø20.

`ColumnDetail` coloca n_b barras en cada cara horizontal y n_h en cada vertical (esquinas incluidas)
con 2·n_b + 2·(n_h − 2) = total. Hasta la 1.2.0 la fórmula de n_h solo cuadraba con n_b = 2: con 12,
14 o 16 barras faltaban posiciones y se repetía la última, de modo que el DXF mostraba 10 círculos
donde el rótulo decía 12Ø20. Se tabulan las posiciones (todas distintas, esquinas siempre
armadas), se dibuja el pilar 500 × 500 con 12Ø20 y se cuentan los círculos del fichero; después un
pilar rectangular 300 × 600 con 10Ø25 y el caso impar (9 barras repite una posición, declarado).

Ejecutar:  python examples/column_section_bar_layouts_4_to_16_bars_perimeter_distribution_rho_and_fixed_overlap.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import ColumnDetail

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def caras(col: ColumnDetail) -> tuple[int, int]:
    d = col.cover + col.db_stirrup + col.bar_diameter() / 2
    pts = col._bar_positions
    n_b = sum(1 for x, y in pts if abs(y - d) < 1e-9)
    n_h = sum(1 for x, y in pts if abs(x - d) < 1e-9)
    return n_b, n_h


def main() -> None:
    print("Pilar 500 × 500 mm, recubrimiento 40 mm, estribo Ø10, barras Ø20:")
    print(f"  {'barras':>6} {'posiciones':>10} {'distintas':>9} {'por cara horiz.':>15} {'por cara vert.':>14} {'A_s [mm²]':>9} {'ρ [%]':>6}")
    for total in (4, 6, 8, 10, 12, 14, 16):
        col = ColumnDetail(b=500.0, h=500.0, cover=40.0, bars=[(20.0, total)], db_stirrup=10.0, label=f"C-{total}")
        pts = col._bar_positions
        uniq = len({(round(x, 6), round(y, 6)) for x, y in pts})
        nb, nh = caras(col)
        print(f"  {total:6d} {len(pts):10d} {uniq:9d} {nb:15d} {nh:14d} {col.as_total():9.0f} {col.rho() * 100:6.2f}")
    col12 = ColumnDetail(b=500.0, h=500.0, cover=40.0, bars=[(20.0, 12)], db_stirrup=10.0, label="C-12", fc=30.0, Fy=500.0)
    p = OUT / "C-12_section.dxf"
    col12.draw(str(p))
    cnt = Counter(e.dxftype() for e in ezdxf.readfile(str(p)).modelspace())
    print(f"\nDXF {p.name}: {dict(cnt)} → {cnt['CIRCLE']} círculos para 12 barras (hasta la 1.2.0 salían 10, con dos pares superpuestos en una esquina)")
    print(f"  Rótulos: {[t.dxf.text for t in ezdxf.readfile(str(p)).modelspace().query('TEXT')]}")
    rect = ColumnDetail(b=300.0, h=600.0, cover=40.0, bars=[(25.0, 10)], db_stirrup=10.0, label="C-R")
    nb, nh = caras(rect)
    print(f"\nPilar 300 × 600 con 10Ø25: {nb} barras en cada cara corta y {nh} en cada cara larga ({len({(round(x, 6), round(y, 6)) for x, y in rect._bar_positions})} posiciones distintas); ρ = {rect.rho() * 100:.2f} %; "
          f"resumen: {rect.summary()['n_bars']} barras, Ø máx {rect.summary()['db_main_mm']:.0f}, A_g = {rect.summary()['Ag_mm2'] / 1e4:.0f} cm²")
    odd = ColumnDetail(b=500.0, h=500.0, cover=40.0, bars=[(20.0, 9)], db_stirrup=10.0)
    print(f"Caso impar 9Ø20: {len(odd._bar_positions)} posiciones, {len({(round(x, 6), round(y, 6)) for x, y in odd._bar_positions})} distintas: no hay reparto perimetral simétrico y la última se repite (documentado en el docstring).")
    print("\nLas esquinas van siempre armadas y el resto se reparte por caras; con diámetros mezclados en `bars` se dibuja el mayor. Para pilares circulares o con dos estribos hace falta otro generador.")


if __name__ == "__main__":
    main()
