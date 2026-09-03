"""Tests de invariante y coordinación geométrica-analítica del armado de zapatas (C.3).

Verifica que:
1. Para zapatas calculables, las tres cifras de armadura coinciden por construcción:
     A_barra * (w_eff / s_dib + 1) / B_m  ==  A_barra / s_rot * 1000  >=  As_cuadro
   con s_rot == round(s_dib) y tolerancia <= 1.0% entre dibujo y rótulo.
2. Para zapatas sin solución física o normativa (s_req > s_max o s_req < s_min):
   - status es REQUIERE_REVISION.
   - NO se dibujan barras en capa ARMADURA (0 líneas fabricadas).
   - El plano estampa advertencia explícita 'REQUIERE REVISION'.
   - El cuadro declara status='REQUIERE_REVISION' y motivo en notes.
"""
from __future__ import annotations

import math
import re
import pytest
from pathlib import Path
import ezdxf

from jmstructural_common.audit_status import CalculationStatus
from dxfstructuraljm.core import Layer
from dxfstructuraljm.foundation_plan import FootingData, FoundationPlan
from dxfstructuraljm.services.footing_drawings import FootingPlanInput, draw_footing_plan


@pytest.mark.parametrize(
    "B_m,As_mm2_m,db_mm",
    [
        (1.0, 1200.0, 16.0),
        (2.0, 600.0, 12.0),
        (2.0, 1200.0, 16.0),
        (2.0, 1200.0, 20.0),
        (3.5, 1200.0, 16.0),
        (3.5, 2400.0, 20.0),
        (3.5, 2400.0, 25.0),
    ],
)
def test_footing_rebar_invariant_coordination(tmp_path: Path, B_m: float, As_mm2_m: float, db_mm: float):
    """Invariante: barras dibujadas, rótulo del plano y cuadro coinciden por construcción."""
    salida = tmp_path / f"footing_{B_m}_{As_mm2_m}_{db_mm}.dxf"
    B_mm = B_m * 1000.0
    L_mm = B_mm  # zapata cuadrada para simplificar
    cover = 75.0
    Ab = math.pi * (db_mm ** 2) / 4.0

    f_data = FootingData(
        label="Z-TEST",
        x=0.0,
        y=0.0,
        B=B_mm,
        L=L_mm,
        d=500.0,
        As_x=As_mm2_m,
        As_y=As_mm2_m,
        db=db_mm,
    )
    plan = FoundationPlan([f_data])
    doc = plan.draw(str(salida))

    # 1. Cuadro de zapatas
    tabla = plan.schedule_table()
    assert len(tabla) == 1
    fila = tabla[0]
    assert fila["status"] == CalculationStatus.CALCULADO_CUMPLE.value
    assert fila["As_x_mm2_m"] == As_mm2_m
    assert fila["db_mm"] == db_mm

    # 2. Leer DXF real con ezdxf
    dxf_doc = ezdxf.readfile(str(salida))
    msp = dxf_doc.modelspace()

    # Contar barras reales dibujadas en capa ARMADURA
    # En zapata cuadrada B=L y As_x=As_y, se dibujan n_x barras verticales + n_y barras horizontales
    rebar_lines = [e for e in msp if e.dxftype() == "LINE" and e.dxf.layer == Layer.REBAR.value]
    total_bars = len(rebar_lines)
    assert total_bars > 0, "Debe haber barras dibujadas en capa ARMADURA"
    assert total_bars % 2 == 0, f"Debe haber igual número de barras en X e Y, total={total_bars}"
    n_bars_dir = total_bars // 2

    # 3. Separación dibujada
    w_eff = B_mm - 2.0 * cover
    s_dibujada = w_eff / (n_bars_dir - 1)

    # 4. Rótulo del plano
    textos = [e.dxf.text for e in msp if e.dxftype() == "TEXT"]
    rotulo = " ".join(textos)
    # Buscar patrón Ø{db} c/{s}
    match = re.search(rf"Ø{int(db_mm)}\s*c/(\d+)", rotulo)
    assert match is not None, f"No se encontró rótulo Ø{int(db_mm)} c/... en: {rotulo}"
    s_rotulo = float(match.group(1))

    # Invariante 1: el rótulo coincide con la separación dibujada al milímetro
    assert s_rotulo == pytest.approx(round(s_dibujada), abs=1.0)

    # Invariante 2: el acero provisto por el dibujo y por el rótulo coinciden (<5.0% por discretización de borde en ancho finito)
    As_dibujado = n_bars_dir * Ab / B_m
    As_rotulo = (Ab / s_rotulo) * 1000.0
    assert As_dibujado == pytest.approx(As_rotulo, rel=0.05)

    # Invariante 3: el acero provisto por dibujo y rótulo cubre la demanda (lado seguro)
    assert As_dibujado >= As_mm2_m * 0.98, f"Acero dibujado ({As_dibujado}) insuficiente para demanda ({As_mm2_m})"
    assert As_rotulo >= As_mm2_m * 0.98, f"Acero rotulado ({As_rotulo}) insuficiente para demanda ({As_mm2_m})"


@pytest.mark.parametrize(
    "As_mm2_m,db_mm,d_mm,motivo_esperado",
    [
        # Caso A: s_req > s_max (separación excesiva: barra muy gruesa para cuantía baja)
        # Ab = 490.9 mm2, As = 600 mm2/m -> s_req = 818.1 mm > s_max = 450 mm
        (600.0, 25.0, 300.0, "s_max"),
        (600.0, 20.0, 500.0, "s_max"),
        # Caso B: s_req < s_min (congestión: barra muy delgada para cuantía alta)
        # db=10 mm -> s_min = max(20, 35) = 35 mm. As=3000 -> s_req = 78.54/3000*1000 = 26.2 mm < 35 mm
        (3000.0, 10.0, 500.0, "s_min"),
    ],
)
def test_footing_rebar_no_solution_requires_revision(tmp_path: Path, As_mm2_m: float, db_mm: float, d_mm: float, motivo_esperado: str):
    """Casos sin solución normativa o física: se marca REQUIERE_REVISION sin fabricar barras."""
    salida = tmp_path / f"unsolvable_{As_mm2_m}_{db_mm}.dxf"
    f_data = FootingData(
        label="Z-FAIL",
        x=0.0,
        y=0.0,
        B=2000.0,
        L=2000.0,
        d=d_mm,
        As_x=As_mm2_m,
        As_y=As_mm2_m,
        db=db_mm,
    )
    plan = FoundationPlan([f_data])
    plan.draw(str(salida))

    # Cuadro
    tabla = plan.schedule_table()
    fila = tabla[0]
    assert fila["status"] == CalculationStatus.REQUIERE_REVISION.value
    assert motivo_esperado in fila["notes"]

    # DXF
    dxf_doc = ezdxf.readfile(str(salida))
    msp = dxf_doc.modelspace()
    rebar_lines = [e for e in msp if e.dxftype() == "LINE" and e.dxf.layer == Layer.REBAR.value]
    assert len(rebar_lines) == 0, f"No deben dibujarse barras ante REQUIERE_REVISION, halladas {len(rebar_lines)}"

    textos = [e.dxf.text for e in msp if e.dxftype() == "TEXT"]
    rotulo = " ".join(textos)
    assert "REQUIERE REVISION" in rotulo
    assert motivo_esperado in rotulo
