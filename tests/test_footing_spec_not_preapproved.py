"""P0: una zapata recien construida no puede nacer aprobada.

`FootingData.status` tenia como valor por defecto:

    status: CalculationStatus = CalculationStatus.CALCULADO_CUMPLE

`FootingData` no se construye en ninguna parte de la produccion de este
monorepo: es API PUBLICA de una libreria de dibujo. Es decir, cualquier
consumidor que la instancie con su armado --que es el caso normal, porque As_x,
As_y y db son justo lo que se necesita para dibujar-- obtenia un
`CALCULADO_CUMPLE` sin que nadie hubiera auditado nada. El `__post_init__` solo
degradaba cuando FALTABA algo; con todo presente, el default se quedaba.

Es la misma "omision = cumplimiento" que se quito de
`foundationdesignjm.analysis.pile_group` (PileForce.status y
PileGroupResult.status tenian el mismo default), escrita como default de
dataclass en vez de como rama de codigo.

Un objeto de dibujo describe QUE se dibuja. No acredita que el calculo se haya
hecho. El estado lo declara quien calcula --`draw_foundation_plan` lo asigna
explicitamente tras comprobar-- y hasta entonces el valor honesto es
`NO_CALCULADO`.
"""
from __future__ import annotations

from dxfstructuraljm.foundation_plan import FootingData
from jmstructural_common.audit_status import CalculationStatus


def _zapata(**campos) -> FootingData:
    base = dict(label="Z1", x=0.0, y=0.0, B=2.0, L=2.0, d=0.45)
    base.update(campos)
    return FootingData(**base)


# --------------------------------------------------------------------------- #
# EL CASO
# --------------------------------------------------------------------------- #
def test_new_foundation_plan_entity_is_not_preapproved() -> None:
    """EL ATAQUE. Zapata con armado completo, sin auditar -> no nace aprobada."""
    z = _zapata(As_x=850.0, As_y=850.0, db=16.0)

    assert z.status is not CalculationStatus.CALCULADO_CUMPLE, (
        "una FootingData recien construida nacio aprobada sin que nadie "
        "hubiera comprobado nada"
    )
    assert z.status is CalculationStatus.NO_CALCULADO


def test_una_zapata_minima_tampoco_nace_aprobada() -> None:
    """Sin armado ya degradaba; se fija para que no se relaje."""
    z = _zapata()

    assert z.status is CalculationStatus.NO_CALCULADO
    assert "NO CALCULADO" in z.notes


def test_el_default_del_dataclass_ya_no_es_un_veredicto_favorable() -> None:
    """Guarda estructural: lee la firma real del campo.

    Si alguien vuelve a poner un default favorable, este test lo dice, aunque el
    `__post_init__` lo tape en los casos que hoy prueba la suite.
    """
    import dataclasses

    campo = next(f for f in dataclasses.fields(FootingData) if f.name == "status")
    assert campo.default is not CalculationStatus.CALCULADO_CUMPLE
    assert campo.default is CalculationStatus.NO_CALCULADO


# --------------------------------------------------------------------------- #
# El control no puede impedir el trabajo legitimo
# --------------------------------------------------------------------------- #
def test_quien_calcula_si_puede_declarar_el_veredicto() -> None:
    """El estado se DECLARA, y declararlo sigue funcionando."""
    z = _zapata(As_x=850.0, As_y=850.0, db=16.0,
                status=CalculationStatus.CALCULADO_CUMPLE)

    assert z.status is CalculationStatus.CALCULADO_CUMPLE


def test_armado_sin_diametro_sigue_pidiendo_revision() -> None:
    """Regresion de la rama que ya existia en `__post_init__`."""
    z = _zapata(As_x=850.0, As_y=850.0)

    assert z.status is CalculationStatus.REQUIERE_REVISION
