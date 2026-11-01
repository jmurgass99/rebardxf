"""Servicio `draw_footing_plan`: diccionarios de entrada (como llegan por JSON), DXF, cuadro de zapatas serializable y validación de campos obligatorios.

La capa de servicios recibe dataclasses `Input` con listas de dicts, valida (campos obligatorios,
dimensiones positivas), dibuja y devuelve metadatos sin exponer los wrappers internos: ruta, número
de entidades, cuadro con estado por zapata. Se mezclan zapatas con ACI y EC2, recubrimientos
distintos y una sin armado, se serializa el resultado a JSON y se provocan los dos errores de
validación (campo que falta, dimensión negativa).

Ejecutar:  python examples/foundation_plan_service_metadata_schedule_and_json_ready_output_for_rest_clients.py
"""
import json
import os
from pathlib import Path

from rebardxf.exceptions import ConfigurationError, GeometryError
from rebardxf.services import FootingPlanInput, draw_footing_plan

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)

FOOTINGS = [
    {"label": "Z-A1", "x": 0.0, "y": 0.0, "B": 2200.0, "L": 2200.0, "d": 550.0, "As_x": 1000.0, "As_y": 1000.0, "db": 16.0, "fc": 25.0, "Fy": 500.0, "design_code": "EC2", "cover_mm": 50.0, "d_agg_mm": 20.0},
    {"label": "Z-A2", "x": 5500.0, "y": 0.0, "B": 2600.0, "L": 2600.0, "d": 650.0, "As_x": 1300.0, "As_y": 1300.0, "db": 16.0, "fc": 25.0, "Fy": 500.0, "design_code": "EC2", "cover_mm": 50.0, "d_agg_mm": 20.0},
    {"label": "Z-B1", "x": 0.0, "y": 5000.0, "B": 2000.0, "L": 2600.0, "d": 550.0, "As_x": 900.0, "As_y": 1200.0, "db": 12.0, "fc": 28.0, "Fy": 420.0, "design_code": "ACI318-19", "cover_mm": 75.0},
    {"label": "Z-B2", "x": 5500.0, "y": 5000.0, "B": 2600.0, "L": 2600.0, "d": 650.0},
]


def main() -> None:
    inp = FootingPlanInput(footings=FOOTINGS, column_size_mm=400.0, draw_rebar=True)
    meta = draw_footing_plan(inp, OUT / "planta_servicio.dxf")
    print(f"draw_footing_plan → {Path(meta['path']).name}: {meta['n_footings']} zapatas, {meta['n_total_entities']} entidades internas {meta['n_entities']}\n")
    print("Cuadro devuelto (listo para JSON):")
    print(f"  {'zapata':>6} {'B × L × d [m]':>18} {'A_s,x':>6} {'A_s,y':>6} {'Ø':>4} {'estado':>17}  notas")
    for r in meta["schedule"]:
        dims = "%.2f × %.2f × %.2f" % (r["B_m"], r["L_m"], r["d_m"])
        print(f"  {r['label']:>6} {dims:>18} {str(r['As_x_mm2_m']):>6} {str(r['As_y_mm2_m']):>6} {str(r['db_mm']):>4} {r['status']:>17}  {r['notes']}")
    js = json.dumps(meta["schedule"], ensure_ascii=False)
    print(f"\n  JSON del cuadro: {len(js)} caracteres; primera fila: {js[:120]}…")
    for bad, desc in (([{"label": "Z-X", "x": 0, "y": 0, "B": 2000.0, "L": 2000.0}], "sin canto d"),
                      ([{"label": "Z-Y", "x": 0, "y": 0, "B": -2000.0, "L": 2000.0, "d": 500.0}], "B negativo"),
                      ([], "lista vacía")):
        try:
            draw_footing_plan(FootingPlanInput(footings=bad), OUT / "x.dxf")
        except (ConfigurationError, GeometryError) as exc:
            print(f"  Validación ({desc}) → {type(exc).__name__}: {exc}")
    print("\nEl servicio es la frontera que usa la API REST (`/api/drawings/footing`): los errores tipados se traducen a 422 y el cuadro viaja tal cual. Z-B2 sin A_s sale NO_CALCULADO en el cuadro y «ARMADO NO DEFINIDO» en el plano.")


if __name__ == "__main__":
    main()
