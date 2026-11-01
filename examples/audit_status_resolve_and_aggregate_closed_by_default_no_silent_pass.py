"""El estado de un cálculo no es un booleano: `resolve_status` exige las seis evidencias declaradas, trata NaN e infinito como «no calculado» y `aggregate_calculation_statuses` no aprueba una lista vacía.

`CalculationStatus` tiene cinco valores (CALCULADO_CUMPLE, CALCULADO_FALLA, NO_CALCULADO,
REQUIERE_REVISION, NO_APLICA). `resolve_status(utilización, …)` es cerrado por defecto: omitir una
condición de evidencia equivale a declararla falsa; `missing_inputs` solo puede quitar; un ratio
infinito (capacidad cero) o NaN es REQUIERE_REVISION, no FALLA; la tolerancia 1e-9 absorbe el error
de ida y vuelta de un dimensionador pero no un 0,1 % de exceso. La agregación: vacío → NO_CALCULADO;
FALLA > NO_CALCULADO > REQUIERE_REVISION > CUMPLE; NO_APLICA nunca domina.

Ejecutar:  python examples/audit_status_resolve_and_aggregate_closed_by_default_no_silent_pass.py
"""
import math

from rebardxf._common.audit_status import EVIDENCE_CONDITIONS, CalculationStatus, aggregate_calculation_statuses, resolve_status

FULL = dict(demand_present=True, capacity_present=True, analysis_executed=True, geometry_present=True, material_present=True, reinforcement_present=True)


def main() -> None:
    print(f"Condiciones de evidencia ({len(EVIDENCE_CONDITIONS)}): {EVIDENCE_CONDITIONS}\n")
    casos = [("utilización 0,85 con las seis evidencias", dict(utilization=0.85, **FULL)),
             ("utilización 1,20 con las seis evidencias", dict(utilization=1.20, **FULL)),
             ("utilización 0,85 sin declarar nada", dict(utilization=0.85)),
             ("utilización 0,85, reinforcement_present=False", dict(utilization=0.85, **{**FULL, "reinforcement_present": False})),
             ("utilización 0,85, falta f_c en missing_inputs", dict(utilization=0.85, missing_inputs=("fc_MPa",), **FULL)),
             ("utilización 0,85, método no soportado", dict(utilization=0.85, unsupported_calc=True, **FULL)),
             ("sin número (None) con evidencias", dict(utilization=None, **FULL)),
             ("ratio +inf (capacidad cero)", dict(utilization=math.inf, **FULL)),
             ("ratio NaN", dict(utilization=math.nan, **FULL)),
             ("ratio −0,2 (signo invertido)", dict(utilization=-0.2, **FULL)),
             ("ratio 1 + 6,66e-16 (tres ULP)", dict(utilization=1.0 + 6.66e-16, **FULL)),
             ("ratio 1,001 (0,1 % de exceso)", dict(utilization=1.001, **FULL)),
             ("demanda cero con evidencias", dict(utilization=0.0, **FULL))]
    print(f"  {'caso':46} {'estado':>18}")
    for nombre, kw in casos:
        print(f"  {nombre:46} {resolve_status(**kw).value:>18}")
    print("\nAgregación de estados:")
    C, F, N, R, A = CalculationStatus.CALCULADO_CUMPLE, CalculationStatus.CALCULADO_FALLA, CalculationStatus.NO_CALCULADO, CalculationStatus.REQUIERE_REVISION, CalculationStatus.NO_APLICA
    agg = [("[] (ninguna comprobación)", []), ("[CUMPLE, CUMPLE, CUMPLE]", [C, C, C]), ("[CUMPLE, NO_APLICA]", [C, A]), ("[NO_APLICA, NO_APLICA]", [A, A]),
           ("[CUMPLE, REQUIERE_REVISION]", [C, R]), ("[CUMPLE, NO_CALCULADO]", [C, N]), ("[CUMPLE, NO_CALCULADO, FALLA]", [C, N, F]),
           ("[REQUIERE_REVISION, NO_CALCULADO]", [R, N]), ("['CALCULADO_CUMPLE', 'texto raro']", ["CALCULADO_CUMPLE", "texto raro"])]
    for nombre, lst in agg:
        print(f"  {nombre:40} → {aggregate_calculation_statuses(lst).value}")
    print(f"\n  all([]) en Python es {all([])}: por eso la lista vacía se trata aparte y da NO_CALCULADO; un plano con cero comprobaciones no está aprobado, está sin comprobar.")
    print("Este contrato es el que usan `FootingData`/`FoundationPlan` (estado inicial NO_CALCULADO, nunca un armado por defecto) y el que debería envolver cualquier verificación que termine en un plano: la ausencia se propaga como ausencia.")


if __name__ == "__main__":
    main()
