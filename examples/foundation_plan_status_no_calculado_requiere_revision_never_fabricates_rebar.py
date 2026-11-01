"""Planta de cimentación con datos incompletos o imposibles: NO_CALCULADO, REQUIERE_REVISION y la regla de no fabricar armadura en el plano.

Cinco zapatas: completa (CALCULADO_CUMPLE), sin A_s (NO_CALCULADO: el plano estampa «ARMADO NO
DEFINIDO» y no dibuja barras), con A_s pero sin Ø (REQUIERE_REVISION), con A_s enorme para Ø12
(s_req < s_mín: congestión) y con A_s pequeño para Ø25 (s_req > s_máx). `FootingData` nace en
NO_CALCULADO (sin default favorable) y `FoundationPlan` decide mirando los datos. Se cuentan las
líneas de la capa ARMADURA del DXF: solo la zapata completa aporta barras.

Ejecutar:  python examples/foundation_plan_status_no_calculado_requiere_revision_never_fabricates_rebar.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf import FootingData, FoundationPlan
from rebardxf._common.audit_status import CalculationStatus, aggregate_calculation_statuses
from rebardxf.foundation_plan import layout_rebar_direction

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    zapatas = [FootingData("Z-OK", 0.0, 0.0, 2400.0, 2400.0, 600.0, As_x=1150.0, As_y=1150.0, db=16.0),
               FootingData("Z-SIN-AS", 6000.0, 0.0, 2400.0, 2400.0, 600.0),
               FootingData("Z-SIN-DB", 12000.0, 0.0, 2400.0, 2400.0, 600.0, As_x=1150.0, As_y=1150.0),
               FootingData("Z-CONGEST", 0.0, 6000.0, 2400.0, 2400.0, 600.0, As_x=4500.0, As_y=4500.0, db=12.0),
               FootingData("Z-S-MAX", 6000.0, 6000.0, 2400.0, 2400.0, 600.0, As_x=400.0, As_y=400.0, db=25.0)]
    print("Estado al construir FootingData (antes de dibujar):")
    for z in zapatas:
        print(f"  {z.label:10} status = {z.status.value:17} notas = «{z.notes}»")
    plan = FoundationPlan(footings=zapatas, column_size=400.0)
    p = OUT / "planta_estados.dxf"
    plan.draw(str(p))
    print("\nCuadro tras dibujar (schedule_table) y rótulo estampado en el plano:")
    dxf = ezdxf.readfile(str(p))
    textos = [t.dxf.text for t in dxf.modelspace().query("TEXT")]
    for row in plan.schedule_table():
        i = textos.index(row["label"])
        rotulo = textos[i + 2] if i + 2 < len(textos) else ""
        print(f"  {row['label']:10} {row['status']:17} A_s = {row['As_x_mm2_m']} / {row['As_y_mm2_m']}, Ø = {row['db_mm']}  → «{rotulo}»")
        if row["notes"]:
            print(f"  {'':10} motivo: {row['notes']}")
    rebar_lines = [e for e in dxf.modelspace().query("LINE") if e.dxf.layer == "ARMADURA"]
    st, n, s_dib, s_rot, _ = layout_rebar_direction(2400.0, 600.0, 1150.0, 16.0, 75.0)
    print(f"\nLíneas en la capa ARMADURA: {len(rebar_lines)} = {n} + {n} de la única zapata calculada (Ø16 c/{s_rot:.0f}); las otras cuatro no aportan ninguna.")
    print(f"Entidades del DXF: {dict(Counter(e.dxftype() for e in dxf.modelspace()))}")
    print(f"\nAgregado de los cinco estados: {plan.footings[0].status.value} + 4 no favorables → el plano no puede firmarse; "
          f"`aggregate_calculation_statuses` da {aggregate_calculation_statuses([z.status for z in zapatas]).value}.")
    print("La ausencia se propaga como ausencia: un dato que falta produce NO_CALCULADO con la lista de lo que falta, nunca un armado por defecto que se lea como aprobado.")


if __name__ == "__main__":
    main()
