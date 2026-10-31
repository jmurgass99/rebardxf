"""Longitud de corte de barras dobladas (planilla de despiece)."""
import math

import pytest

from rebardxf.rebar_cut_length import (
    bend_arc_length,
    bend_deduction,
    cut_length_centerline,
    cut_length_from_outside,
)


class TestArc:
    def test_arco_90(self):
        # arco = (pi/2)·(r + db/2)
        assert bend_arc_length(90.0, inside_diameter_mm=64.0, db_mm=16.0) == pytest.approx(
            math.radians(90.0) * (32.0 + 8.0), rel=1e-9)

    def test_arco_crece_con_angulo(self):
        assert bend_arc_length(180.0, 64.0, 16.0) > bend_arc_length(90.0, 64.0, 16.0)


class TestCutLength:
    def test_barra_recta_es_su_longitud(self):
        # Sin dobleces: cut length = tramo recto.
        assert cut_length_centerline([3000.0], [], 64.0, 16.0) == pytest.approx(3000.0)

    def test_L_bar_suma_tramos_mas_arco(self):
        # L-bar: 2 tramos + 1 doblez de 90.
        L = cut_length_centerline([1000.0, 500.0], [90.0], 64.0, 16.0)
        assert L == pytest.approx(1500.0 + bend_arc_length(90.0, 64.0, 16.0), rel=1e-9)

    def test_out_to_out_menor_que_suma_cotas(self):
        # La longitud de corte (out-to-out) es MENOR que la suma de cotas exteriores.
        cotas = [1000.0, 500.0]
        L = cut_length_from_outside(cotas, [90.0], 64.0, 16.0)
        assert L < sum(cotas)
        assert L == pytest.approx(sum(cotas) - bend_deduction(90.0, 64.0, 16.0), rel=1e-9)


class TestDeduction:
    def test_deduccion_positiva_90(self):
        assert bend_deduction(90.0, 64.0, 16.0) > 0

    def test_ganchos_suman(self):
        sin = cut_length_centerline([2000.0], [], 64.0, 16.0)
        con = cut_length_centerline([2000.0], [], 64.0, 16.0, hook_tails_mm=[120.0, 120.0])
        assert con == pytest.approx(sin + 240.0)
