"""Alzado de un pórtico de 2 vanos y 2 pisos con armado y estribos: el número exacto de entidades del DXF se deriva a mano y se comprueba contra el fichero.

`FrameElevationDetail` dibuja ejes con burbujas, niveles con cota, contornos de pilares y vigas,
armadura longitudinal (dos líneas por pieza) y estribos en zonas críticas y centrales. Como todo
es determinista, `expected_entity_counts` da la fórmula cerrada: líneas = ejes + niveles + 2·pilares
+ 2·vigas + 2·pilares + estribos de pilar + 2·vigas + estribos de viga; círculos = ejes; textos =
1 + ejes + niveles + pilares + vigas. Se releen las entidades con ezdxf y coinciden una a una.

Ejecutar:  python examples/frame_elevation_two_bays_two_storeys_exact_entity_count_derivation_vs_dxf.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import FrameElevationDetail

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    fr = FrameElevationDetail(axis_name="Eje B", bays=[5000.0, 6000.0], stories=[3500.0, 3000.0], col_width=400.0, beam_height=500.0, cover=40.0,
                              col_s_critical=100.0, col_s_central=200.0, col_lc_critical=500.0, beam_s_critical=100.0, beam_s_central=200.0, beam_lc_critical=800.0, label="PORTICO-B")
    print(f"Pórtico {fr.label} ({fr.axis_name}): vanos {fr.bays} mm, pisos {fr.stories} mm → {fr.num_axes} ejes, {fr.num_levels} niveles, {fr.num_columns} pilares, {fr.num_beams} vigas\n")
    print("Estribos por pieza (zona crítica + central + crítica):")
    for j, h in enumerate(fr.stories):
        h_clear = h - fr.beam_height
        n_crit = int(fr.col_lc_critical // fr.col_s_critical)
        n_cent = int(max(0.0, h_clear - 2 * fr.col_lc_critical) // fr.col_s_central)
        print(f"  pilar piso {j + 1}: H libre {h_clear:.0f} mm → 2·{n_crit} + {n_cent} = {fr.col_stirrups_per_column(j)} estribos")
    for i, b in enumerate(fr.bays):
        l_clear = b - fr.col_width
        n_crit = int(fr.beam_lc_critical // fr.beam_s_critical)
        n_cent = int(max(0.0, l_clear - 2 * fr.beam_lc_critical) // fr.beam_s_central)
        print(f"  viga vano {i + 1}: L libre {l_clear:.0f} mm → 2·{n_crit} + {n_cent} = {fr.beam_stirrups_per_bay(i)} estribos")
    exp = fr.expected_entity_counts()
    col_st = sum(fr.num_axes * fr.col_stirrups_per_column(j) for j in range(len(fr.stories)))
    beam_st = sum(len(fr.stories) * fr.beam_stirrups_per_bay(i) for i in range(len(fr.bays)))
    print(f"\nDerivación: líneas = {fr.num_axes} ejes + {fr.num_levels} niveles + 2·{fr.num_columns} contorno pilares + 2·{fr.num_beams} contorno vigas + 2·{fr.num_columns} armado pilares + {col_st} estribos pilar + 2·{fr.num_beams} armado vigas + {beam_st} estribos viga = {exp['LINE']}")
    print(f"            círculos = {exp['CIRCLE']} (una burbuja por eje); textos = 1 + {fr.num_axes} + {fr.num_levels} + {fr.num_columns} + {fr.num_beams} = {exp['TEXT']}; total {exp['total_entities']}")
    p = OUT / "alzado_portico_B.dxf"
    fr.draw_elevation(str(p))
    dxf = ezdxf.readfile(str(p))
    cnt = Counter(e.dxftype() for e in dxf.modelspace())
    print(f"\nDXF {p.name} releído: {dict(cnt)} → {'COINCIDE' if cnt['LINE'] == exp['LINE'] and cnt['CIRCLE'] == exp['CIRCLE'] and cnt['TEXT'] == exp['TEXT'] else 'NO COINCIDE'} con la derivación")
    capas = Counter(e.dxf.layer for e in dxf.modelspace())
    print(f"  Por capa: {dict(capas)}")
    print(f"  Rótulos: {[t.dxf.text for t in dxf.modelspace().query('TEXT')][:12]} …")
    print("\nEl recuento cerrado es la prueba de regresión del generador: cualquier cambio en el reparto de estribos o en los rótulos rompe la igualdad. El alzado es esquemático (dos líneas por armado); el despiece barra a barra va en los detalles de pilar y viga.")


if __name__ == "__main__":
    main()
