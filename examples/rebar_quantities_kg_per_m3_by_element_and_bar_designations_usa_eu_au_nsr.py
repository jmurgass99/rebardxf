"""Cuantías de acero por elemento (kg y kg/m³) con designaciones de barra de EE. UU. (#3–#11), Europa (Ø mm), Australia (N12–N40) y Colombia, y el total del proyecto.

`summarize_quantities` agrupa `RebarItem` por elemento, pesa con π·Ø²/4·7850 y divide por el
volumen de hormigón de `ElementGeometry`; `diameter_mm` traduce la designación según el código.
Dos pilares, una viga y una zapata con barras en designación americana, el mismo conjunto en
métrico, y la tabla de equivalencias #/N/mm con el kg/m de cada una.

Ejecutar:  python examples/rebar_quantities_kg_per_m3_by_element_and_bar_designations_usa_eu_au_nsr.py
"""
from rebardxf.rebar_quantities import ElementGeometry, RebarItem, bar_weight_per_m, diameter_mm, summarize_quantities, total_project_steel_kg


def main() -> None:
    barras_usa = [RebarItem("C-1", "#8", 4.2, 8), RebarItem("C-1", "#3", 1.9, 26), RebarItem("C-2", "#6", 4.2, 8), RebarItem("C-2", "#3", 1.7, 26),
                  RebarItem("V-1", "#6", 6.35, 5), RebarItem("V-1", "#5", 2.4, 2), RebarItem("V-1", "#3", 1.54, 42),
                  RebarItem("Z-1", "#5", 2.68, 26)]
    geom = [ElementGeometry("C-1", 0.5 * 0.5 * 3.6), ElementGeometry("C-2", 0.4 * 0.4 * 3.6), ElementGeometry("V-1", 0.3 * 0.5 * 6.0), ElementGeometry("Z-1", 2.4 * 2.4 * 0.6)]
    print("Designación americana (ASTM A615):")
    print(f"  {'elemento':>8} {'acero [kg]':>10} {'hormigón [m³]':>13} {'cuantía [kg/m³]':>15}")
    for r in summarize_quantities(barras_usa, geom, code="USA"):
        print(f"  {r.element_id:>8} {r.total_weight_kg:10.1f} {r.volume_m3:13.3f} {r.cuantia_kg_per_m3:15.0f}")
    print(f"  Total del proyecto: {total_project_steel_kg(barras_usa, 'USA'):.1f} kg")
    barras_eu = [RebarItem("C-1", "25", 4.2, 8), RebarItem("C-1", "10", 1.9, 26), RebarItem("C-2", "20", 4.2, 8), RebarItem("C-2", "10", 1.7, 26),
                 RebarItem("V-1", "20", 6.35, 5), RebarItem("V-1", "16", 2.4, 2), RebarItem("V-1", "10", 1.54, 42), RebarItem("Z-1", "16", 2.68, 26)]
    print("\nMismo armado en métrico (EU, Ø25/20/16/10):")
    for r in summarize_quantities(barras_eu, geom, code="EU"):
        print(f"  {r.element_id:>8} {r.total_weight_kg:10.1f} kg → {r.cuantia_kg_per_m3:5.0f} kg/m³")
    print(f"  Total: {total_project_steel_kg(barras_eu, 'EU'):.1f} kg ({(total_project_steel_kg(barras_eu, 'EU') / total_project_steel_kg(barras_usa, 'USA') - 1) * 100:+.1f} % frente al americano: #8 = 25,4 mm y #3 = 9,5 mm no son Ø25 y Ø10 exactos)")
    print("\nEquivalencias y kg/m por código:")
    print(f"  {'USA':>5} {'Ø [mm]':>6} {'kg/m':>6} | {'EU':>4} {'kg/m':>6} | {'AU':>4} {'Ø [mm]':>6} {'kg/m':>6} | {'NSR':>4} {'Ø [mm]':>6}")
    filas = [("#3", "10", "N12", "#3"), ("#4", "12", "N12", "#4"), ("#5", "16", "N16", "#5"), ("#6", "20", "N20", "#6"), ("#8", "25", "N24", "#8"), ("#10", "32", "N32", "25")]
    for usa, eu, au, nsr in filas:
        print(f"  {usa:>5} {diameter_mm(usa, 'USA'):6.1f} {bar_weight_per_m(usa, 'USA'):6.3f} | {eu:>4} {bar_weight_per_m(eu, 'EU'):6.3f} | {au:>4} {diameter_mm(au, 'AU'):6.0f} {bar_weight_per_m(au, 'AU'):6.3f} | {nsr:>4} {diameter_mm(nsr, 'NSR'):6.1f}")
    try:
        diameter_mm("N12", "EU")
    except ValueError as exc:
        print(f"\n  Designación de otro código → ValueError: {exc}")
    print("\nLas cuantías orientativas de pilar (120–200 kg/m³), viga (90–150) y zapata (30–70) sirven para contrastar un despiece: un elemento fuera de rango suele tener una longitud o un conteo mal copiado. El módulo no deduce longitudes ni solapes; pesa lo que se le da.")


if __name__ == "__main__":
    main()
