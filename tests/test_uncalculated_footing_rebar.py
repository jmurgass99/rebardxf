"""Test TDD para comprobar que zapatas sin dimensionar no dibujan armadura fabricada en el plano DXF.

Copia el contrato canónico de SapToRevit (commit 7fd6d0b):
  - Ausencia de datos -> status CalculationStatus.NO_CALCULADO
  - No se dibujan barras ficticias
  - La nota del plano dice 'NO CALCULADO — ARMADO NO DEFINIDO'
  - El cuadro de zapatas reporta As_x=None, As_y=None, db=None y status='NO_CALCULADO'
"""
from __future__ import annotations

import pytest
from pathlib import Path
from jmstructural_common.audit_status import CalculationStatus
from dxfstructuraljm.core import Layer
from dxfstructuraljm.foundation_plan import FootingData, FoundationPlan
from dxfstructuraljm.services.footing_drawings import FootingPlanInput, draw_footing_plan


def test_footing_without_rebar_is_no_calculado_and_draws_no_rebar(tmp_path: Path):
    """Una zapata sin As_x / As_y debe marcarse NO_CALCULADO y no dibujar barras."""
    output_dxf = tmp_path / "plan_uncalc.dxf"
    inp = FootingPlanInput(
        footings=[
            {
                "label": "Z-UNREAD",
                "x": 0.0,
                "y": 0.0,
                "B": 2000.0,
                "L": 2000.0,
                "d": 500.0,
                # Sin As_x, As_y, db, fc, Fy
            }
        ]
    )
    res = draw_footing_plan(inp, output_dxf)

    # 1. Metadatos del cuadro
    sched = res["schedule"][0]
    assert sched["status"] == CalculationStatus.NO_CALCULADO.value
    assert sched["As_x_mm2_m"] is None
    assert sched["As_y_mm2_m"] is None
    assert sched["db_mm"] is None

    # 2. Entidades: no debe haber lineas de armadura fabricada
    import ezdxf
    doc = ezdxf.readfile(str(output_dxf))
    msp = doc.modelspace()

    rebar_lines = [e for e in msp if e.dxftype() == "LINE" and e.dxf.layer == Layer.REBAR.value]
    assert len(rebar_lines) == 0, f"Se fabricaron {len(rebar_lines)} barras en la capa REBAR sin armadura calculada"

    # 3. El plano debe incluir la nota de advertencia explicita
    texts = [e.dxf.text for e in msp if e.dxftype() == "TEXT"]
    assert any("NO CALCULADO" in t for t in texts), f"No se encontro nota NO CALCULADO en textos: {texts}"
    assert not any("Ø16" in t for t in texts), f"Se encontro texto de barra fabricada: {texts}"


def test_footing_with_rebar_retains_calculado_cumple(tmp_path: Path):
    """Una zapata con As_x y As_y validos se dibuja normalmente."""
    output_dxf = tmp_path / "plan_calc.dxf"
    inp = FootingPlanInput(
        footings=[
            {
                "label": "Z-OK",
                "x": 0.0,
                "y": 0.0,
                "B": 2000.0,
                "L": 2000.0,
                "d": 500.0,
                "As_x": 800.0,
                "As_y": 800.0,
                "db": 16.0,
            }
        ]
    )
    res = draw_footing_plan(inp, output_dxf)
    sched = res["schedule"][0]
    assert sched["status"] == CalculationStatus.CALCULADO_CUMPLE.value
    assert sched["As_x_mm2_m"] == 800.0
    assert sched["As_y_mm2_m"] == 800.0
    assert sched["db_mm"] == 16.0

    import ezdxf
    doc = ezdxf.readfile(str(output_dxf))
    msp = doc.modelspace()

    rebar_lines = [e for e in msp if e.dxftype() == "LINE" and e.dxf.layer == Layer.REBAR.value]
    assert len(rebar_lines) > 0
    texts = [e.dxf.text for e in msp if e.dxftype() == "TEXT"]
    assert any("Ø16" in t for t in texts)


# ---------------------------------------------------------------------------
# Hallazgo de auditoria: el diametro sobrevivio al arreglo
# ---------------------------------------------------------------------------
def test_diametro_ausente_no_se_estampa_como_16(tmp_path):
    """`As_x`/`As_y` calculados pero `db` AUSENTE: el plano fabricaba un Ø16.

    El `__post_init__` marca NO_CALCULADO cuando falta `As_x` o `As_y`, pero NO
    cuando falta `db`. Con la armadura calculada y el diametro sin elegir, la
    rama "si calculado" ejecutaba `db_val = f.db if f.db is not None else 16.0`
    -- el patron prohibido, con el MISMO literal Ø16 que se acababa de eliminar
    de `footing_drawings.py:48`, y en el mismo fichero del arreglo.

    Medido antes de este test:

        As_x = 1200.0   db = None
        cuadro de zapatas -> db_mm: None      ("no lo se")
        rotulo del plano  -> "Ø16 c/181"      ("es un Ø16")

    El mismo documento se contradice a si mismo. Y es el dibujo, no la tabla, lo
    que lee quien ferralla.
    """
    import ezdxf

    from dxfstructuraljm.core import Layer
    from dxfstructuraljm.services.footing_drawings import (
        FootingPlanInput, draw_footing_plan,
    )

    salida = str(tmp_path / "sin_diametro.dxf")
    res = draw_footing_plan(FootingPlanInput(footings=[{
        "label": "Z-SIN-DB", "x": 0, "y": 0, "B": 2000, "L": 2000, "d": 500,
        "As_x": 1200.0, "As_y": 1200.0,     # calculados
        # db ausente a proposito
    }]), salida)

    fila = res["schedule"][0]
    assert fila["As_x_mm2_m"] == 1200.0, "el area SI se calculo y debe conservarse"
    assert fila["db_mm"] is None

    textos = [e.dxf.text for e in ezdxf.readfile(salida).modelspace()
              if e.dxftype() == "TEXT"]
    rotulo = " ".join(textos)
    assert "\u00d816" not in rotulo.replace(" ", ""), (
        f"el plano estampa un diametro que nadie eligio: {textos!r}"
    )
    assert "1200" in rotulo, (
        "el area SI se conoce: declararla es mejor que callarla. "
        f"Rotulos: {textos!r}"
    )


def test_diametro_presente_se_rotula_normalmente(tmp_path):
    """Control: con `db` dado, el rotulo no cambia."""
    import ezdxf

    from dxfstructuraljm.services.footing_drawings import (
        FootingPlanInput, draw_footing_plan,
    )

    salida = str(tmp_path / "con_diametro.dxf")
    draw_footing_plan(FootingPlanInput(footings=[{
        "label": "Z-OK", "x": 0, "y": 0, "B": 2000, "L": 2000, "d": 500,
        "As_x": 1200.0, "As_y": 1200.0, "db": 20.0,
    }]), salida)
    rotulo = " ".join(e.dxf.text for e in ezdxf.readfile(salida).modelspace()
                      if e.dxftype() == "TEXT")
    assert "\u00d820" in rotulo.replace(" ", "")
