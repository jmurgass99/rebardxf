"""Lámina A3 y A1 con marco, cajetín y ventana en espacio papel sobre un modelo dibujado en mm, frente al método heredado que pintaba el cajetín en el modelo.

`SheetTemplate.apply_to_layout(doc)` crea un layout con el tamaño ISO, dibuja borde exterior,
marco interior (margen de encuadernación 25 mm), cajetín de 3 × 4 celdas con los datos de
`TitleBlockInfo`, hueco para el logo y una ventana (VIEWPORT) centrada en el modelo con la altura
de vista pedida (escala = altura modelo / altura papel). Se cuentan las entidades del layout y del
modelo, se crean A3 y A1 sobre el mismo documento y se muestra el aviso de deprecación del método
que dibujaba todo en el modelspace.

Ejecutar:  python examples/sheet_template_a3_a1_paperspace_layout_title_block_viewport_vs_legacy_modelspace.py
"""
import os
import warnings
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import A1, ColumnDetail, SheetTemplate, TitleBlockInfo
from rebardxf.exceptions import TemplateError
from rebardxf.scales import SHEET_SIZES_MM

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    col = ColumnDetail(b=500.0, h=500.0, cover=40.0, bars=[(20.0, 12)], db_stirrup=10.0, label="P-1", fc=30.0, Fy=500.0)
    p = OUT / "lamina_P-1.dxf"
    doc = col.draw(str(p))
    info = TitleBlockInfo(project="Edificio de oficinas — Bloque B", drawing="S-301 Detalle pilar P-1", scale="1:10", revision="B", designer="JM", checker="AR", client="Promotora XYZ", notes="Hormigón C30/37, acero B500S")
    sheet = SheetTemplate(size="A3", info=info)
    vp_h_paper = SHEET_SIZES_MM["A3"][1] - 2 * 10.0
    layout = sheet.apply_to_layout(doc, view_center=(250.0, 250.0), view_height=vp_h_paper * 10.0)
    doc.save()
    dxf = ezdxf.readfile(str(p))
    lay = dxf.layouts.get("A3_Sheet")
    cnt_ps = Counter(e.dxftype() for e in lay)
    cnt_ms = Counter(e.dxftype() for e in dxf.modelspace())
    print(f"Hoja {sheet.size} {sheet.width:.0f} × {sheet.height:.0f} mm; layouts del documento: {[l.name for l in dxf.layouts]}")
    print(f"  Espacio papel «A3_Sheet»: {dict(cnt_ps)} (borde, marco, cajetín 3 × 4, logo, ventana); modelo: {dict(cnt_ms)} (la sección del pilar en mm, intacta)")
    vp = [e for e in lay if e.dxftype() == "VIEWPORT"]
    if vp:
        v = vp[-1]
        print(f"  Ventana: centro papel ({v.dxf.center.x:.1f}, {v.dxf.center.y:.1f}) mm, tamaño {v.dxf.width:.0f} × {v.dxf.height:.0f} mm, vista del modelo centrada en {tuple(round(c) for c in v.dxf.view_center_point)} con altura {v.dxf.view_height:.0f} mm → escala 1:{v.dxf.view_height / v.dxf.height:.0f}")
    textos = [t.dxf.text for t in lay.query("TEXT")]
    print(f"  Cajetín: {[t for t in textos if t in (info.project, info.drawing, info.scale, info.revision, info.designer, info.client)]}")
    a1 = A1(TitleBlockInfo(project="Bloque B", drawing="S-001 Planta de cimentación", scale="1:50"))
    a1.apply_to_layout(doc, view_center=(250.0, 250.0), view_height=(SHEET_SIZES_MM["A1"][1] - 20.0) * 50.0)
    doc.save()
    dxf = ezdxf.readfile(str(p))
    print(f"\nAñadida una A1 al mismo documento: layouts {[l.name for l in dxf.layouts]}; A1_Sheet tiene {len(list(dxf.layouts.get('A1_Sheet')))} entidades (cajetín de 180 × 50 mm en A1/A2/A0, 150 × 40 en A3/A4)")
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        SheetTemplate("A4", TitleBlockInfo()).draw_in_modelspace(doc)
    print(f"  Método heredado draw_in_modelspace: {w[0].category.__name__} — «{str(w[0].message)[:80]}…»; añade {doc.n_entities()['lines']} líneas al contador del modelo")
    try:
        SheetTemplate("B2")
    except TemplateError as exc:
        print(f"  Tamaño desconocido → TemplateError: {exc}")
    print("\nEl cajetín en espacio papel se imprime a 1:1 y la escala la fija la ventana (view_height = alto de la ventana × denominador): para 1:10 en A3 la vista tiene 2770 mm de alto. "
          "El texto «v1.0» de la celda de marca es fijo y el logo es un hueco: dos detalles cosméticos que el usuario sustituye en su plantilla.")


if __name__ == "__main__":
    main()
