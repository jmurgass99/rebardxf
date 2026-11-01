"""Escalas de dibujo: elegir la escala normalizada que mete un plano en una hoja, alturas de texto y desfases de cota en unidades de modelo, y conversiones papel ↔ modelo.

`auto_scale(ancho, alto, hoja, margen)` devuelve la menor escala de la serie 1:10…1:1000 que cabe
en el área útil; `Scale.text_height(2,5)` da la altura en mm de modelo para que imprima 2,5 mm,
`dim_offset` y `arrow_size` igual. Se tabula para una planta de cimentación de 24 × 15 m, un alzado
de 17 × 10 m, una sección de 0,5 × 0,6 m y un detalle de 0,12 m en hojas A1, A3 y A4, en mm y en m.

Ejecutar:  python examples/scales_auto_scale_for_sheets_text_heights_dimension_offsets_and_bbox_table.py
"""
from rebardxf import Scale, auto_scale
from rebardxf.scales import SHEET_SIZES_MM, STANDARD_SCALES, bbox_of


def main() -> None:
    print(f"Serie de escalas: {STANDARD_SCALES}; hojas ISO 216 [mm]: {SHEET_SIZES_MM}\n")
    casos = [("planta de cimentación 24 × 15 m", 24000.0, 15000.0), ("alzado de pórtico 17 × 10 m", 17000.0, 10000.0), ("sección de viga 0,5 × 0,6 m", 500.0, 600.0), ("detalle de gancho 0,12 × 0,08 m", 120.0, 80.0)]
    print(f"  {'dibujo':34} {'hoja':>4} {'área útil [mm]':>14} {'necesaria':>9} {'escala':>6} {'texto 2,5 mm → modelo':>21} {'cota 7 mm':>9} {'flecha 2,5':>10}")
    for nombre, w, h in casos:
        for hoja in ("A1", "A3", "A4"):
            sw, sh = SHEET_SIZES_MM[hoja]
            margen = 30.0
            need = max(w / (sw - 2 * margen), h / (sh - 2 * margen))
            sc = auto_scale(w, h, sheet=hoja, margin_mm=margen)
            print(f"  {nombre:34} {hoja:>4} {f'{sw - 2 * margen:.0f} × {sh - 2 * margen:.0f}':>14} {need:9.1f} {str(sc):>6} {sc.text_height(2.5):21.1f} {sc.dim_offset(7.0):9.1f} {sc.arrow_size(2.5):10.1f}")
    print("\nConversiones papel ↔ modelo:")
    for f in (20, 50, 100):
        sc = Scale(f)
        print(f"  1:{f}: 100 mm de papel = {sc.to_model(100.0):.0f} mm de modelo; una viga de 6000 mm mide {sc.to_paper(6000.0):.0f} mm en el papel; texto 3,5 mm → {sc.text_height(3.5):.0f} mm")
    scm = Scale(50, units="m")
    print(f"  Modelo en metros, 1:50: 6 m de viga = {scm.to_paper(6.0):.0f} mm de papel; 2,5 mm de texto = {scm.text_height(2.5):.4f} m de modelo")
    pts = [(0.0, 0.0), (24000.0, 0.0), (24000.0, 15000.0), (0.0, 15000.0), (12000.0, 16500.0)]
    bb = bbox_of(pts)
    print(f"\n  bbox_of de 5 puntos → {bb} → {bb[2] - bb[0]:.0f} × {bb[3] - bb[1]:.0f} mm → auto_scale A1 = {auto_scale(bb[2] - bb[0], bb[3] - bb[1], 'A1')}")
    try:
        auto_scale(1000.0, 1000.0, sheet="A5")
    except ValueError as exc:
        print(f"  Hoja desconocida → ValueError: {exc}")
    print("\nLa planta de 24 m pide 1:50 en A1, 1:75 en A3 (la serie incluye el 75; muchas oficinas lo evitan y saltan a 1:100) y 1:200 en A4; la sección entra a 1:10 en cualquier hoja porque 1:10 es la escala más grande de la serie. "
          "Las alturas de texto son las que hay que pasar a `DXFDocument.text` para que el plano impreso tenga 2,5 mm: dibujar en mm de modelo con texto de 2,5 mm sale ilegible a 1:50.")


if __name__ == "__main__":
    main()
