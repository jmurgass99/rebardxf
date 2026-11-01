"""Planilla de despiece de una viga de 6 m: marcas, longitudes de corte, peso por marca y por diámetro, conservación de masa y el servicio `build_rebar_schedule`.

`RebarSchedule.add(marca, elemento, Ø, n, L_corte, forma)`; `to_table` da las filas con kg/m
(7850·π·Ø²/4) y total, `summary_by_diameter` agrupa por Ø y `total_weight` suma. Se comprueba que
la suma por diámetro iguala el total (conservación de masa), que el kg/m coincide con la regla
0,006165·Ø² y se pasa la misma lista por el servicio, que valida entradas (Ø, n, L > 0).

Ejecutar:  python examples/rebar_schedule_beam_marks_weights_by_diameter_mass_conservation_and_service.py
"""
import math

from rebardxf import RebarSchedule
from rebardxf.exceptions import ConfigurationError
from rebardxf.services import RebarScheduleInput, build_rebar_schedule
from rebardxf.services.schedules import _RebarItem


def main() -> None:
    sched = RebarSchedule()
    sched.add("1", "V-101", 20.0, 3, 6350.0, "straight")      # inferiores con patillas
    sched.add("2", "V-101", 16.0, 2, 6350.0, "straight")      # superiores
    sched.add("3", "V-101", 16.0, 2, 2400.0, "straight")      # refuerzo negativo en apoyos
    sched.add("4", "V-101", 10.0, 42, 1544.0, "stirrup")      # cercos 300 × 500 c30 (longitud de corte del caso de longitudes)
    sched.add("5", "V-101", 8.0, 12, 540.0, "U")              # horquillas
    print("Planilla V-101 (longitudes de corte en mm):")
    sched.print_table()
    print("\nFilas de to_table():")
    for r in sched.to_table():
        print(f"  marca {r['mark']} {r['shape']:>8} Ø{r['db_mm']:<2} n = {r['count']:3d} L = {r['L_mm']:6.0f} mm ΣL = {r['L_total_m']:6.2f} m × {r['unit_wt_kg_m']:.4f} kg/m = {r['total_kg']:7.3f} kg")
    por_d = sched.summary_by_diameter()
    print(f"\nPor diámetro: {por_d}; suma = {sum(v['total_kg'] for v in por_d.values()):.2f} kg frente a total_weight = {sched.total_weight()} kg → {'conservación OK' if abs(sum(v['total_kg'] for v in por_d.values()) - sched.total_weight()) < 0.05 else 'DISCREPANCIA'}")
    print("kg/m exacto frente a la regla 0,006165·Ø²:")
    for db in (8.0, 10.0, 12.0, 16.0, 20.0, 25.0, 32.0):
        print(f"  Ø{db:2.0f}: {sched.unit_weight(db):.4f} kg/m, regla {0.006165 * db ** 2:.4f}, tabla comercial {dict(((8, 0.395), (10, 0.617), (12, 0.888), (16, 1.578), (20, 2.466), (25, 3.853), (32, 6.313)))[int(db)]}")
    meta = build_rebar_schedule(RebarScheduleInput(entries=[_RebarItem(e.mark, e.element, e.diameter, e.count, e.length, e.shape) for e in sched.entries]))
    print(f"\nServicio build_rebar_schedule: {meta['n_entries']} entradas, total {meta['total_kg']} kg, por Ø {meta['by_diameter']}")
    try:
        build_rebar_schedule(RebarScheduleInput(entries=[_RebarItem("9", "V-1", 16.0, 0, 6000.0)]))
    except ConfigurationError as exc:
        print(f"  Entrada con n = 0 → ConfigurationError: {exc}")
    vol = 0.30 * 0.50 * 6.0
    print(f"\nCuantía de la viga: {sched.total_weight() / vol:.0f} kg/m³ de hormigón ({vol:.2f} m³); los cercos son el {por_d[10]['total_kg'] / sched.total_weight() * 100:.0f} % del acero. "
          "Las longitudes de corte son dato: salen de `rebar_cut_length`, no de la planilla.")


if __name__ == "__main__":
    main()
