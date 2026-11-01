"""Capas: el registro estándar en castellano (CONCRETO, ARMADURA, ESTRIBO, COTAS…) con color, tipo de línea y grosor, las capas AIA (S-COLU-RBAR…) y los cinco estándares de nomenclatura por país.

`apply_layers` registra `STANDARD_LAYERS` y los tipos de línea necesarios (CENTER, DASHED, HIDDEN)
en un documento ezdxf; `aia_layers.apply_to_dxf` añade las 21 capas AIA/NCS para estructuras; y
`layer_standards` describe los patrones de nombres de AIA-NCS (US), ISO 13567 (EU), CORENET (SG),
NATSPEC (AU) y NTC 1960 (CO) con `naming_for(país)`. Se lista todo y se comprueba en el DXF que
color, linetype y lineweight han quedado grabados.

Ejecutar:  python examples/layer_standards_aia_iso13567_corenet_natspec_ntc_and_apply_layers_colors_linetypes.py
"""
import os
from pathlib import Path

import ezdxf

from rebardxf import STANDARD_LAYERS, apply_layers
from rebardxf.aia_layers import STRUCTURAL_LAYERS, apply_to_dxf, get_layer
from rebardxf.layer_standards import STANDARDS, lookup, naming_for
from rebardxf.layers import color_of, list_layers

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)
ACI = {1: "rojo", 2: "amarillo", 3: "verde", 4: "cian", 5: "azul", 6: "magenta", 7: "blanco/negro", 8: "gris oscuro", 9: "gris claro"}


def main() -> None:
    print(f"Registro estándar ({len(list_layers())} capas):")
    print(f"  {'capa':10} {'color':>5} {'':12} {'linetype':>10} {'grosor [mm]':>11}  descripción")
    for spec in STANDARD_LAYERS.values():
        print(f"  {spec.name:10} {spec.color:5d} {ACI[spec.color]:12} {spec.linetype:>10} {spec.lineweight / 100:11.2f}  {spec.description}")
    doc = ezdxf.new("R2018")
    apply_layers(doc)
    n_aia = apply_to_dxf(doc)
    p = OUT / "capas_estandar.dxf"
    doc.modelspace().add_line((0, 0), (1000, 0), dxfattribs={"layer": "EJES"})
    doc.modelspace().add_line((0, 100), (1000, 100), dxfattribs={"layer": "S-GRID"})
    doc.saveas(str(p))
    d = ezdxf.readfile(str(p))
    print(f"\nDXF {p.name}: {len(d.layers)} capas ({len(STANDARD_LAYERS)} estándar + {n_aia} AIA + «0» y «Defpoints»); linetypes disponibles: {sorted(lt.dxf.name for lt in d.linetypes)}")
    for name in ("EJES", "OCULTAS", "AUXILIAR", "S-GRID", "S-COLU-RBAR"):
        L = d.layers.get(name)
        print(f"  {name:12} color {L.color} ({ACI.get(L.color, '?')}), linetype {L.dxf.linetype}, grosor {L.dxf.lineweight / 100:.2f} mm")
    print(f"  color_of('ARMADURA') = {color_of('ARMADURA')}; capa desconocida → {color_of('NADA')}")
    print(f"\nCapas AIA / US National CAD Standard ({len(STRUCTURAL_LAYERS)}): patrón <Disciplina>-<Mayor>-<Menor>")
    for L in STRUCTURAL_LAYERS[:8]:
        print(f"  {L.name:12} {L.description:28} color {L.color_aci} {ACI[L.color_aci]:12} {L.linetype:>10} {L.lineweight_mm:.2f} mm")
    print(f"  … y {len(STRUCTURAL_LAYERS) - 8} más (acero, conexiones, anotaciones, grilla); get_layer('S-FNDN-RBAR') → {get_layer('S-FNDN-RBAR')}")
    print("\nEstándares de nomenclatura por país:")
    for s in STANDARDS:
        print(f"  {s.code_id:15} {s.description:42} {s.naming_pattern:40} ej. {s.example}")
    for pais in ("ES", "US", "SG", "AU", "CO", "BR"):
        std = naming_for(pais)
        print(f"  {pais}: {std.code_id + ' → ' + std.example if std else 'sin estándar asignado (devuelve None)'}")
    print(f"  lookup('ISO-13567-EU').example = {lookup('ISO-13567-EU').example}")
    print("\nUn plano que mezcla las dos familias (CONCRETO y S-COLU-CONC) imprime bien pero confunde al que filtra por capas: elige una. Los códigos ISO 13567 (A21S101) solo se dan como patrón, el paquete no genera el catálogo completo de códigos de elemento.")


if __name__ == "__main__":
    main()
