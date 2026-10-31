"""Secciones de viga y pilar de hormigón armado a DXF, con cuadro de despiece.

Se dibuja la sección transversal de una viga 300x500 con su armado y la de un
pilar 400x400, se exportan a DXF (abribles en AutoCAD, BricsCAD, LibreCAD o
cualquier visor) y se genera el cuadro de despiece con pesos por diámetro.

Ejecutar:  python examples/01_beam_and_column_sections.py
Salida:    examples/out/V-1_section.dxf, examples/out/C-1_section.dxf
"""
from pathlib import Path

from rebardxf import BeamDetail, ColumnDetail, RebarSchedule

OUT = Path(__file__).resolve().parent / "out"


def main() -> None:
    OUT.mkdir(exist_ok=True)

    beam = BeamDetail(b=300.0, h=500.0, cover=30.0,
                      bars_top=[(16.0, 2)], bars_bot=[(20.0, 3)],
                      db_stirrup=10.0, s_critical=100.0, s_central=200.0,
                      span=6000.0, label="V-1", fc=28.0, Fy=420.0)
    beam_path = OUT / "V-1_section.dxf"
    beam.draw_section(str(beam_path))
    print(f"Viga {beam.label}: {beam.b:.0f}x{beam.h:.0f} mm → {beam_path.name} ({beam_path.stat().st_size} bytes)")

    col = ColumnDetail(b=400.0, h=400.0, cover=40.0, bars=[(20.0, 8)], db_stirrup=10.0, label="C-1")
    col_path = OUT / "C-1_section.dxf"
    col.draw(str(col_path))
    print(f"Pilar {col.label}: {col.b:.0f}x{col.h:.0f} mm, {sum(n for _, n in col.bars)} barras → {col_path.name}")

    # Cuadro de despiece de la viga (longitudes de corte aproximadas)
    sched = RebarSchedule()
    sched.add("1", "V-1", 20.0, 3, 6400.0, "straight")
    sched.add("2", "V-1", 16.0, 2, 6400.0, "straight")
    n_stirrups = int(2 * 1000.0 / 100.0) + int(4000.0 / 200.0)
    sched.add("3", "V-1", 10.0, n_stirrups, 2 * (300 - 60) + 2 * (500 - 60) + 2 * 100, "U")
    print("\nDespiece V-1:")
    sched.print_table()
    print(f"Peso total de acero: {sched.total_weight():.1f} kg")


if __name__ == "__main__":
    main()
