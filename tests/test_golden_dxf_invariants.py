"""
test_golden_dxf_invariants.py — Golden Tests e Invariantes para DXFStructuralJm
================================================================================
Declaración: DXFStructuralJm es un motor de dibujo técnico CAD y detallado geométrico
(no ejecuta análisis físico por elementos finitos, sino generación determinista de DXF,
planillas de despiece y capas normalizadas).

1. Golden 1: Longitud de corte y descuentos de doblado de armaduras según BS 8666 / ACI 315.
   Fuente: BS 8666:2020 Table 1 Shape Code 21/33 / ACI 315R-18
2. Golden 2: Estándares internacionales de capas CAD estructurales (AIA NCS v6, ISO 13567).
   Fuente: ISO 13567-1 / AIA National CAD Standard v6
"""
from __future__ import annotations

import math
import pytest

from dxfstructuraljm.layer_standards import STANDARDS, lookup, naming_for
from dxfstructuraljm.rebar_cut_length import (
    bend_arc_length,
    bend_deduction,
    cut_length_centerline,
    cut_length_from_outside,
)


class TestGoldenDXFInvariants:
    """Golden tests con fuentes normativas para despiece geométrico y capas CAD."""

    def test_golden_1_rebar_bend_deduction_and_cut_length(self):
        """Golden Test 1: Descuento de doblado y longitud de corte por fibra neutra.

        Fuente: BS 8666:2020 Table 1 Shape Code 21/33 / ACI 315R-18

        Derivación analítica:
        - Barra ∅ db = 16 mm.
        - Radio interior de doblado r = 2*db = 32 mm (mandril standard de 4*db = 64 mm).
        - Doblez a 90° (theta = π/2 rad):
          Radio de fibra neutra: r_c = r + db/2 = 32 + 8 = 40 mm.
          Longitud de arco por fibra neutra:
            arco = (π / 2) * 40 mm = 20 * π = 62.83185 mm.
          Tangente exterior:
            tangente = 2 * (r + db) * tan(45°) = 2 * (32 + 16) * 1.0 = 96.0 mm.
          Descuento de doblado (bend deduction):
            deduccion = 96.0 - 62.83185 = 33.16815 mm.

        - Barra en 'L' (Shape Code 21) con cotas exteriores A = 500 mm, B = 300 mm:
          Suma de cotas exteriores = 800 mm.
          Longitud de corte nominal:
            L_corte = A + B - deduccion = 500 + 300 - 33.16815 = 766.83185 mm.
        """
        db = 16.0
        inside_dia = 64.0  # mandril de 4*db -> r = 32 mm
        angle = 90.0

        arc = bend_arc_length(angle_deg=angle, inside_diameter_mm=inside_dia, db_mm=db)
        expected_arc = (math.pi / 2.0) * (32.0 + 8.0)
        assert arc == pytest.approx(expected_arc, rel=1e-4)
        assert arc == pytest.approx(62.83185, rel=1e-4)

        ded = bend_deduction(angle_deg=angle, inside_diameter_mm=inside_dia, db_mm=db)
        expected_ded = 96.0 - expected_arc
        assert ded == pytest.approx(expected_ded, rel=1e-4)
        assert ded == pytest.approx(33.16815, rel=1e-4)

        # Longitud de corte para barra en L (500x300 mm exteriores)
        l_outside = cut_length_from_outside(
            outside_legs_mm=[500.0, 300.0],
            bend_angles_deg=[90.0],
            inside_diameter_mm=inside_dia,
            db_mm=db,
        )
        assert l_outside == pytest.approx(766.83185, rel=1e-4)

    def test_golden_2_international_cad_layer_standards(self):
        """Golden Test 2: Invariantes exactos de nomenclatura de capas CAD estructurales.

        Fuente: ISO 13567-1 / AIA National CAD Standard v6

        Verifica:
        - AIA-NCS-US: Patrón `<DISCIPLINE>-<MAJOR>-<MINOR>-<STATUS>` -> S-COLU-CONC
        - ISO-13567-EU: Patrón `A<SUBJECT><ELEMENT><PRESENTATION>` -> A21S101
        - BCA-CORENET-SG: Patrón `<DISCIPLINE>_<ELEMENT>_<PROPERTY>` -> S_COL_RBAR
        - NATSPEC-AU: Patrón `<MODEL>-<CATEGORY>-<TYPE>` -> ST-COL-CONC
        """
        assert len(STANDARDS) == 5

        aia = lookup("AIA-NCS-US")
        assert aia is not None
        assert aia.example == "S-COLU-CONC"
        assert aia.naming_pattern == "<DISCIPLINE>-<MAJOR>-<MINOR>-<STATUS>"

        iso = lookup("ISO-13567-EU")
        assert iso is not None
        assert iso.example == "A21S101"

        # Heurística por país
        assert naming_for("US").code_id == "AIA-NCS-US"
        assert naming_for("ES").code_id == "ISO-13567-EU"
        assert naming_for("SG").code_id == "BCA-CORENET-SG"
        assert naming_for("AU").code_id == "NATSPEC-AU"
        assert naming_for("CO").code_id == "NTC-1960-CO"
