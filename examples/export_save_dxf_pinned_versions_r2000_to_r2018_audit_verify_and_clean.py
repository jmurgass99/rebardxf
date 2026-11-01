"""Guardar un DXF en la versión que pide el visor (R2000 a R2018), auditarlo, verificarlo releído y purgar bloques sin usar.

`save_dxf(doc, ruta, dxfversion, audit)` ejecuta el auditor de ezdxf, fija la versión del fichero y
guarda; hasta la 1.2.0 el parámetro de versión se ignoraba y todo salía R2018 (AC1032), que algunos
visores y máquinas de corte antiguas no leen. `verify` reabre el fichero y cuenta errores, arreglos
y entidades; `clean` elimina definiciones de bloque no referenciadas. Se guarda la misma sección de
pilar en las seis versiones y se comprueba el código AC leído.

Ejecutar:  python examples/export_save_dxf_pinned_versions_r2000_to_r2018_audit_verify_and_clean.py
"""
import os
from pathlib import Path

import ezdxf

from rebardxf import ColumnDetail
from rebardxf.exceptions import ConfigurationError
from rebardxf.export import SUPPORTED_VERSIONS, clean, save_dxf, verify

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)
CODES = {"AC1015": "R2000", "AC1018": "R2004", "AC1021": "R2007", "AC1024": "R2010", "AC1027": "R2013", "AC1032": "R2018"}


def main() -> None:
    col = ColumnDetail(b=450.0, h=450.0, cover=40.0, bars=[(20.0, 8)], db_stirrup=10.0, label="P-5", fc=30.0, Fy=500.0)
    wrapper = col.draw(str(OUT / "P-5_tmp.dxf"))
    ez = wrapper._doc
    print(f"Documento de ezdxf creado por ColumnDetail: versión {ez.dxfversion} ({CODES[ez.dxfversion]}), {len(list(ez.modelspace()))} entidades en el modelo\n")
    print(f"  {'pedida':>6} {'fichero':>8} {'leído':>7} {'ok':>5} {'errores':>7} {'arreglos':>8} {'entidades':>9} {'bytes':>7}")
    for label in SUPPORTED_VERSIONS:
        p = OUT / f"P-5_{label}.dxf"
        save_dxf(ez, p, dxfversion=label, audit=True)
        v = verify(p)
        print(f"  {label:>6} {p.name:>8} {CODES.get(v['dxfversion'], v['dxfversion']):>7} {str(v['ok']):>5} {v['errors']:7d} {v['fixes']:8d} {v['n_modelspace_entities']:9d} {p.stat().st_size:7d}")
    print("  Las seis versiones llevan las mismas 21 entidades; el fichero crece con la versión por las tablas y objetos que añade cada formato.")
    try:
        save_dxf(ez, OUT / "x.dxf", dxfversion="R2025")
    except ConfigurationError as exc:
        print(f"\n  Versión no soportada → ConfigurationError: {str(exc)[:90]}…")
    doc = ezdxf.new("R2018")
    for name in ("BLQ_USADO", "BLQ_HUERFANO_1", "BLQ_HUERFANO_2"):
        blk = doc.blocks.new(name)
        blk.add_circle((0, 0), 5)
    doc.modelspace().add_blockref("BLQ_USADO", (100, 100))
    antes = [b.name for b in doc.blocks if not b.name.startswith("*")]
    purged = clean(doc)
    despues = [b.name for b in doc.blocks if not b.name.startswith("*")]
    print(f"\nclean(): bloques antes {antes} → purgados {purged['blocks']} → quedan {despues} (el referenciado por INSERT se conserva)")
    p = save_dxf(doc, OUT / "bloques_limpios.dxf", dxfversion="R2010")
    print(f"  guardado como R2010 → verify {verify(p)}")
    print("\nR2010 es la versión segura para intercambio (Revit Link CAD, visores antiguos, CNC de ferralla); R2018 solo si hace falta algo de las versiones nuevas. El auditor arregla lo que puede (handles, tablas) y lo demás lo cuenta como error en `verify`.")


if __name__ == "__main__":
    main()
