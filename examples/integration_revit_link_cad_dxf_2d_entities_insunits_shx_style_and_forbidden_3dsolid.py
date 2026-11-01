"""DXF apto para «Insert → Link CAD» de Revit: solo entidades 2D, unidades en milímetros ($INSUNITS = 4), estilo de texto con fuente SHX, capas AIA con color por prefijo, y rechazo de sólidos 3D.

`make_revit_compatible_dxf` toma entidades neutras (`DXFEntity` o los atajos `line`, `polyline`,
`circle`, `text`) y escribe un R2010 con cabecera y estilo que Revit lee sin fuentes TrueType ni
XREF. Se dibuja una planta esquemática (ejes, pilares, zapatas, textos), se comprueban la cabecera,
el estilo REVIT_STD, los colores de capa deducidos del prefijo AIA y el error con un 3DSOLID; después
el mismo fichero en metros.

Ejecutar:  python examples/integration_revit_link_cad_dxf_2d_entities_insunits_shx_style_and_forbidden_3dsolid.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf.integration.revit_dxf_link import AIA_COLORS, DXFEntity, RevitDXFOptions, circle, line, make_revit_compatible_dxf, polyline, text

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def planta() -> list[DXFEntity]:
    ents = []
    for i, x in enumerate((0.0, 6000.0, 12000.0)):
        ents.append(line((x, -1000.0), (x, 9000.0), layer="S-GRID"))
        ents.append(circle((x, 9600.0), 400.0, layer="S-GRID-IDEN"))
        ents.append(text((x - 150.0, 9450.0), chr(65 + i), height=350.0, layer="S-GRID-IDEN"))
        for y in (0.0, 8000.0):
            ents.append(polyline([(x - 250, y - 250), (x + 250, y - 250), (x + 250, y + 250), (x - 250, y + 250)], layer="S-COLU-CONC", close=True))
            ents.append(polyline([(x - 1200, y - 1200), (x + 1200, y - 1200), (x + 1200, y + 1200), (x - 1200, y + 1200)], layer="S-FNDN-CONC", close=True))
            ents.append(text((x - 1100.0, y - 1600.0), f"Z-{chr(65 + i)}{1 if y == 0 else 2}", height=250.0, layer="S-TEXT"))
    ents.append(line((-1000.0, 0.0), (13000.0, 0.0), layer="S-GRID"))
    ents.append(line((-1000.0, 8000.0), (13000.0, 8000.0), layer="S-GRID"))
    ents.append(text((4000.0, -3000.0), "PLANTA DE CIMENTACION 1:100", height=500.0, layer="S-ANNO-TEXT"))
    return ents


def main() -> None:
    ents = planta()
    p = OUT / "planta_revit_link.dxf"
    doc = make_revit_compatible_dxf(ents, p)
    print(f"{len(ents)} entidades neutras → {p.name}: versión {doc.dxfversion} (R2010), $INSUNITS = {doc.header['$INSUNITS']} (4 = milímetros)")
    d = ezdxf.readfile(str(p))
    cnt = Counter(e.dxftype() for e in d.modelspace())
    print(f"  Entidades: {dict(cnt)} (solo LINE, LWPOLYLINE, CIRCLE, TEXT)")
    st = d.styles.get("REVIT_STD")
    print(f"  Estilo de texto REVIT_STD → fuente «{st.dxf.font}» (SHX, no TrueType); textos con ese estilo: {sum(1 for t in d.modelspace().query('TEXT') if t.dxf.style == 'REVIT_STD')} de {cnt['TEXT']}")
    print(f"  Capas y color (prefijo AIA): " + ", ".join(f"{L.dxf.name}={L.color}" for L in d.layers if L.dxf.name not in ("0", "Defpoints")))
    print(f"  Mapa AIA_COLORS: {AIA_COLORS}")
    try:
        make_revit_compatible_dxf([DXFEntity("3DSOLID", {}, "S-COLU")], OUT / "x.dxf")
    except ValueError as exc:
        print(f"\n  Entidad 3DSOLID → ValueError: {exc}")
    try:
        make_revit_compatible_dxf([DXFEntity("SPLINE", {}, "S-ANNO")], OUT / "x.dxf")
    except ValueError as exc:
        print(f"  Entidad SPLINE (no soportada) → ValueError: {exc}")
    ents_m = [DXFEntity(e.type, {k: (tuple(v_ / 1000 for v_ in v) if isinstance(v, tuple) else [tuple(c / 1000 for c in pt) for pt in v] if k == "points" else (v / 1000 if k in ("radius", "height") else v)) for k, v in e.data.items()}, e.layer) for e in ents]
    doc_m = make_revit_compatible_dxf(ents_m, OUT / "planta_revit_link_m.dxf", RevitDXFOptions(units="M", shx_font="simplex.shx", aci_overrides={"S-FNDN": 30}))
    print(f"\nMisma planta en metros: $INSUNITS = {doc_m.header['$INSUNITS']} (6 = metros), fuente {doc_m.styles.get('REVIT_STD').dxf.font}, color de S-FNDN-CONC sobrescrito a {doc_m.layers.get('S-FNDN-CONC').color}")
    try:
        make_revit_compatible_dxf(ents, OUT / "x.dxf", RevitDXFOptions(units="FT"))
    except ValueError as exc:
        print(f"  Unidades no soportadas → ValueError: {exc}")
    print("\nRevit vincula bien si las unidades del DXF coinciden con las del import (mm o m), no hay 3D ni XREF y las fuentes son SHX; los colores por capa se mantienen al vincular y se pierden al explotar. El puente no convierte un plano existente: recibe entidades neutras.")


if __name__ == "__main__":
    main()
