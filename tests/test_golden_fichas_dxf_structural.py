"""Golden tests y caracterización analítica de despiece de armaduras y DXF geométrico.

Fichas ancla y referencias
--------------------------
* **W01686 — Detailing, layout and anchorage (UPC / Eurocódigo 2)**:
  - Longitud de anclaje básica por adherencia:
      l_b,rqd = (phi / 4) * (sigma_sd / f_bd)
      con f_bd = 2.25 * eta1 * eta2 * (f_ctk,0.05 / gamma_c).
  - Longitud mínima de anclaje:
      l_b,min = max(0.3 * l_b,rqd, 10 * phi, 100 mm).
  - Reglas de despiece y doblado de armaduras pasivas.

* **W00492 / Planos ARAGO — Despieces de vigas, pilares y cuadros de ferralla**:
  - Longitud de corte por fibra neutra (Centerline):
      Arco = theta_rad * (r + phi / 2)
      Bend deduction = 2 * (r + phi) * tan(theta / 2) - Arco (para 90 deg: 2*(r+phi) - Arco).
  - Longitud out-to-out corregida para barras en L (Shape 11), U (Shape 21) y cercos (Shape 51).

* **BS 8666 / UNE-EN ISO 3766 / ACI 318 — Planilla de ferralla y cubicación**:
  - Masa nominal lineal: w = (pi * phi^2 / 4) * rho_steel (con rho = 7850 kg/m3).
  - Invariante de conservación de masa y cuantía de acero por m3 de hormigón (kg/m3).
  - Estándar de capas CAD (AIA Layer Guidelines).
"""
from __future__ import annotations

import math
import pytest

from dxfstructuraljm.rebar_cut_length import (
    bend_arc_length,
    bend_deduction,
    cut_length_centerline,
    cut_length_from_outside,
)
from dxfstructuraljm.rebar_quantities import (
    RebarItem,
    ElementGeometry,
    diameter_mm,
    bar_weight_per_m,
    summarize_quantities,
    total_project_steel_kg,
)
from dxfstructuraljm.layer_standards import (
    LayerStandard,
    lookup,
    naming_for,
    STANDARDS,
)
from dxfstructuraljm.aia_layers import get_layer


class TestW01686RebarAnchorageAndDetailingGolden:
    """Validación del modelo canónico de longitud de anclaje según Eurocódigo 2 / W01686."""

    def test_ec2_basic_anchorage_length_analytical(self):
        """Cálculo de l_b,rqd para phi=16 mm, C25/30 (fctk=1.80 MPa -> fbd=2.70 MPa), B500 (sigma=435 MPa).

        f_ctd = 1.80 / 1.5 = 1.20 MPa.
        f_bd = 2.25 * 1.0 * 1.0 * 1.20 = 2.70 MPa.
        l_b,rqd = (16 / 4) * (435 / 2.70) = 4 * 161.111 = 644.44 mm.
        """
        phi_mm = 16.0
        f_ctk_005 = 1.80  # MPa (C25/30)
        gamma_c = 1.5
        f_ctd = f_ctk_005 / gamma_c  # 1.20 MPa
        eta1 = 1.0  # buena adherencia
        eta2 = 1.0  # phi <= 32 mm
        f_bd = 2.25 * eta1 * eta2 * f_ctd  # 2.70 MPa

        sigma_sd = 435.0  # MPa (fyk / 1.15)
        l_b_rqd_mm = (phi_mm / 4.0) * (sigma_sd / f_bd)

        assert f_bd == pytest.approx(2.70, rel=1e-6)
        assert l_b_rqd_mm == pytest.approx(644.444, rel=1e-4)

        # Longitud mínima de anclaje a tracción
        l_b_min = max(0.3 * l_b_rqd_mm, 10.0 * phi_mm, 100.0)
        assert l_b_min == pytest.approx(193.333, rel=1e-4)

    def test_anchorage_proportional_to_bar_diameter(self):
        """La longitud de anclaje es estrictamente lineal con el diámetro de la barra."""
        l_12 = (12.0 / 4.0) * (435.0 / 2.70)
        l_20 = (20.0 / 4.0) * (435.0 / 2.70)
        assert (l_20 / l_12) == pytest.approx(20.0 / 12.0, rel=1e-6)


class TestBS8666RebarCutLengthGeometricInvariants:
    """Validación geométrica del cálculo de longitudes de corte y deducciones por doblez."""

    def test_90_degree_bend_arc_and_deduction_formula(self):
        """Para doblez a 90 deg con radio interior r=32mm (inside_diameter=64mm), phi=16mm:

        Arco = (pi/2) * (r + phi/2) = (pi/2) * 40 = 62.83185 mm.
        Cota exterior añadida por esquina = 2 * (r + phi) = 2 * 48 = 96 mm.
        Deducción de corte = 96 - 62.83185 = 33.16815 mm.
        """
        phi = 16.0
        inside_dia = 64.0  # 2 * r = 2 * 32
        theta_deg = 90.0

        arc = bend_arc_length(angle_deg=theta_deg, inside_diameter_mm=inside_dia, db_mm=phi)
        expected_arc = (math.pi / 2.0) * ((inside_dia / 2.0) + phi / 2.0)
        assert arc == pytest.approx(expected_arc, rel=1e-6)

        deduct = bend_deduction(angle_deg=theta_deg, inside_diameter_mm=inside_dia, db_mm=phi)
        expected_deduct = 2.0 * ((inside_dia / 2.0) + phi) - expected_arc
        assert deduct == pytest.approx(expected_deduct, rel=1e-6)

    def test_l_bar_shape11_cut_length(self):
        """Barra en L (Shape 11): A=500mm, B=300mm, phi=16mm, inside_dia=64mm -> L_cut = 766.83 mm."""
        legs_out = [500.0, 300.0]
        bends = [90.0]
        phi = 16.0
        inside_dia = 64.0

        cut_len = cut_length_from_outside(outside_legs_mm=legs_out, bend_angles_deg=bends, inside_diameter_mm=inside_dia, db_mm=phi)
        assert cut_len == pytest.approx(766.83185, rel=1e-4)

    def test_u_bar_shape21_two_bends(self):
        """Barra en U (Shape 21): A=400mm, B=600mm, C=400mm con dos dobleces de 90 deg."""
        legs_out = [400.0, 600.0, 400.0]
        bends = [90.0, 90.0]
        phi = 16.0
        inside_dia = 64.0

        cut_len = cut_length_from_outside(outside_legs_mm=legs_out, bend_angles_deg=bends, inside_diameter_mm=inside_dia, db_mm=phi)
        # Suma exterior = 1400 mm, menos 2 * 33.168 mm = 1333.66 mm
        assert cut_len == pytest.approx(1400.0 - 2.0 * 33.16815, rel=1e-4)


class TestRebarQuantitiesAndMassConservationGolden:
    """Validación de cubicación de acero, masa nominal e invariantes de planilla."""

    @pytest.mark.parametrize("desig, expected_kg_m", [
        ("6", 0.222),
        ("8", 0.395),
        ("10", 0.617),
        ("12", 0.888),
        ("16", 1.578),
        ("20", 2.466),
        ("25", 3.853),
        ("32", 6.313),
    ])
    def test_metric_nominal_weights_eu_standard(self, desig, expected_kg_m):
        """Verifica los pesos nominales teóricos de ferralla según catálogo europeo."""
        w = bar_weight_per_m(desig, code="EU")
        assert w == pytest.approx(expected_kg_m, abs=0.005)

    def test_mass_conservation_and_element_quantities_summary(self):
        """Planilla de viga de hormigón: 4 barras phi 16 (L=6m) + 25 estribos phi 8 (L=1.2m).

        Masa longitudinal = 4 * 6.0 * 1.5783 kg/m = 37.88 kg.
        Masa estribos = 25 * 1.2 * 0.3946 kg/m = 11.84 kg.
        Masa total = 49.72 kg.
        """
        items = [
            RebarItem(element_id="VIGA-101", designation="16", length_m=6.0, count=4),
            RebarItem(element_id="VIGA-101", designation="8", length_m=1.2, count=25),
        ]
        geos = [
            ElementGeometry(element_id="VIGA-101", volume_m3=0.30 * 0.50 * 6.0),
        ]

        total_kg = total_project_steel_kg(items, code="EU")
        expected_long_kg = 4 * 6.0 * bar_weight_per_m("16", code="EU")
        expected_trans_kg = 25 * 1.2 * bar_weight_per_m("8", code="EU")
        expected_total = expected_long_kg + expected_trans_kg

        assert total_kg == pytest.approx(expected_total, rel=1e-6)
        assert total_kg == pytest.approx(49.72, abs=0.1)

        # Resumen por elemento y cuantía de acero kg/m3
        rows = summarize_quantities(items, geometries=geos, code="EU")
        assert len(rows) == 1
        row = rows[0]
        assert row.element_id == "VIGA-101"
        assert row.total_weight_kg == pytest.approx(expected_total, rel=1e-5)
        # Volumen = 0.3 * 0.5 * 6.0 = 0.9 m3 -> Cuantía ≈ 49.72 / 0.9 = 55.24 kg/m3
        expected_cuantia = expected_total / 0.90
        assert row.cuantia_kg_per_m3 == pytest.approx(expected_cuantia, rel=1e-4)


class TestCADLayerStandardsAndDraftingInvariants:
    """Validación de estándares de capas CAD estructurales (AIA Layer Guidelines)."""

    def test_layer_standards_lookup(self):
        """Verifica que el estándar de capas AIA resuelve correctamente los elementos estructurales."""
        std_us = lookup("AIA-NCS-US")
        assert std_us is not None
        assert std_us.code_id == "AIA-NCS-US"
        assert "AIA" in std_us.description

        std_eu = lookup("ISO-13567-EU")
        assert std_eu is not None
        assert std_eu.code_id == "ISO-13567-EU"

    def test_aia_structural_layers_definitions(self):
        """Verifica la asignación de colores ACI y nombres normalizados de capas estructurales."""
        col_layer = get_layer("S-COLU-RBAR")
        assert col_layer is not None
        assert col_layer.color_aci == 1  # rojo para armadura

        beam_layer = get_layer("S-BEAM-CONC")
        assert beam_layer is not None
        assert beam_layer.color_aci == 5  # azul para hormigón
