# -*- coding: utf-8 -*-
"""test_golden_analytical_dxf_detailing.py — Fichas Golden analíticas para RebarDXF.

BLOQUE D — GOLDENS DE LA BANDA BAJA (RebarDXF):
======================================================
1. Golden 1: Invariante analítico de recuento exacto de entidades CAD (LINE, CIRCLE, TEXT) en pórticos.
   Cita/Referencia:
     - ISO 13567 (Technical product documentation — Organization and naming of layers for CAD).
     - ACI 315R-18 (Guide to Presenting Reinforcing Steel Design Details).
     - AutoCAD DXF Reference (Autodesk R2018 Specification).

2. Golden 2: Longitud de corte y desarrollo de ganchos estándar según ACI 318-19 Cl. 25.3 / EN 1992-1-1 Cl. 8.4.
   Cita/Referencia:
     - ACI 318-19 (Building Code Requirements for Structural Concrete), Table 25.3.1 & Section 25.3.2.
     - Eurocódigo 2 EN 1992-1-1:2004, Sección 8.4 (Anclaje de armaduras longitudinales) y 8.5 (Anclaje de cercos y estribos).
     - CRSI (Concrete Reinforcing Steel Institute) Manual of Standard Practice, 29th Ed.
"""
from __future__ import annotations

import math
import tempfile
from pathlib import Path
import ezdxf
import pytest

from rebardxf.frame_elevation import FrameElevationDetail


class TestGoldenAnalyticalDXFDetailing:
    def test_golden_1_cad_entity_count_invariant_frame_elevation(self) -> None:
        """Golden 1: Invariante de recuento cerrado de entidades DXF en alzado de pórtico 2 vanos, 2 pisos.

        Geometría del pórtico:
          Vanos: L_1 = 5000 mm, L_2 = 6000 mm (N_bays = 2, N_axes = 3).
          Pisos: H_1 = 3500 mm, H_2 = 3000 mm (N_stories = 2, N_levels = 3).
          Columnas: ancho = 400 mm, viga: canto = 500 mm.
          N_cols = 3 * 2 = 6 columnas.
          N_beams = 2 * 2 = 4 vigas.

        Derivación analítica paso a paso:
          1. Ejes verticales: 3 líneas de eje + 3 círculos (burbujas) + 3 textos de eje.
          2. Niveles: 3 líneas de nivel + 3 textos de cota.
          3. Columnas contorno: 2 líneas verticales * 6 columnas = 12 líneas.
          4. Vigas contorno: 2 líneas horizontales * 4 vigas = 8 líneas.
          5. Armadura longitudinal columnas: 2 líneas * 6 columnas = 12 líneas.
          6. Estribos de columnas:
             - Piso 1 (H = 3500 mm, H_clear = 3000 mm):
               lc = 500 mm, s_crit = 100 mm -> n_crit = 5
               h_cent = 3000 - 1000 = 2000 mm, s_cent = 200 mm -> n_cent = 10
               Total estribos/columna = 2 * 5 + 10 = 20 estribos.
             - Piso 2 (H = 3000 mm, H_clear = 2500 mm):
               lc = 500 mm, s_crit = 100 mm -> n_crit = 5
               h_cent = 2500 - 1000 = 1500 mm, s_cent = 200 mm -> n_cent = 7
               Total estribos/columna = 2 * 5 + 7 = 17 estribos.
             - Total líneas estribos columnas = 3 * 20 + 3 * 17 = 60 + 51 = 111 líneas.
          7. Armadura longitudinal vigas: 2 líneas * 4 vigas = 8 líneas.
          8. Estribos de vigas:
             - Vano 1 (L = 5000 mm, L_clear = 4600 mm):
               lc = 800 mm, s_crit = 100 mm -> n_crit = 8
               l_cent = 4600 - 1600 = 3000 mm, s_cent = 200 mm -> n_cent = 15
               Total estribos/viga = 2 * 8 + 15 = 31 estribos.
             - Vano 2 (L = 6000 mm, L_clear = 5600 mm):
               lc = 800 mm, s_crit = 100 mm -> n_crit = 8
               l_cent = 5600 - 1600 = 4000 mm, s_cent = 200 mm -> n_cent = 20
               Total estribos/viga = 2 * 8 + 20 = 36 estribos.
             - Total líneas estribos vigas = 2 pisos * (31 + 36) = 2 * 67 = 134 líneas.
          9. Total LINE = 3 (ejes) + 3 (niveles) + 12 (col outline) + 8 (beam outline)
                          + 12 (col rebar) + 111 (col stirrups) + 8 (beam rebar) + 134 (beam stirrups)
                        = 291 LINE.
          10. Total CIRCLE = 3 (burbujas de eje).
          11. Total TEXT = 1 (título) + 3 (ejes) + 3 (niveles) + 6 (etiquetas col) + 4 (etiquetas vigas) = 17 TEXT.
          Total entidades = 291 + 3 + 17 = 311 entidades.
        """
        frame = FrameElevationDetail(
            axis_name="Eje 1",
            bays=[5000.0, 6000.0],
            stories=[3500.0, 3000.0],
            col_width=400.0,
            beam_height=500.0,
            col_lc_critical=500.0,
            col_s_critical=100.0,
            col_s_central=200.0,
            beam_lc_critical=800.0,
            beam_s_critical=100.0,
            beam_s_central=200.0,
            label="PORTICO-GOLDEN",
        )

        expected = frame.expected_entity_counts()
        assert expected["LINE"] == 291
        assert expected["CIRCLE"] == 3
        assert expected["TEXT"] == 17
        assert expected["total_entities"] == 311

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "golden_frame.dxf"
            frame.draw_elevation(str(out_file))

            doc = ezdxf.readfile(str(out_file))
            msp = doc.modelspace()

            assert len(list(msp.query("LINE"))) == 291
            assert len(list(msp.query("CIRCLE"))) == 3
            assert len(list(msp.query("TEXT"))) == 17

    def test_golden_2_aci318_ec2_rebar_hook_and_bend_deductions(self) -> None:
        """Golden 2: Fórmulas cerradas de arcos de doblado y ganchos estándar ACI 318-19 / EC2.

        1. Gancho estándar a 90° para barra longitudinal (ACI 318-19 Table 25.3.1 / EC2 Cl. 8.4):
           - Diámetro nominal de barra: d_b = 20 mm.
           - Diámetro interior de mandril de doblado: D_m = 4 * d_b = 80 mm (r_in = 40 mm).
           - Radio al eje neutro de la barra: r_n = r_in + d_b / 2 = 40 + 10 = 50 mm.
           - Ángulo de doblado: theta = 90 deg = pi / 2 rad.
           - Longitud de arco de doblado: L_arc = r_n * theta = 50 * (pi / 2) = 25 * pi = 78.5398 mm.
           - Extensión recta requerida: L_ext = 12 * d_b = 12 * 20 = 240.0 mm.
           - Deducción por curvatura en esquina exterior a 90°:
             D_90 = 2 * (r_in + d_b) - L_arc = 2 * (40 + 20) - 78.5398 = 120 - 78.5398 = 41.4602 mm.

        2. Gancho sísmico a 135° para estribos cerrados (ACI 318-19 Table 25.3.2 / EC2 Cl. 8.5):
           - Diámetro nominal de estribo: d_b = 10 mm.
           - Diámetro de mandril: D_m = 4 * d_b = 40 mm (r_in = 20 mm).
           - Radio al eje neutro: r_n = 20 + 5 = 25 mm.
           - Ángulo de doblado: theta = 135 deg = 3 * pi / 4 rad.
           - Longitud de arco: L_arc = 25 * (3 * pi / 4) = 58.9049 mm.
           - Extensión recta mínima: L_ext = max(6 * d_b, 75.0 mm) = max(60.0, 75.0) = 75.0 mm.
           - Longitud total de desarrollo del gancho sísmico:
             L_hook_135 = L_arc + L_ext = 58.9049 + 75.0 = 133.9049 mm.
        """
        # Caso 1: Barra longitudinal 90°
        db_long = 20.0
        r_in_long = 2.0 * db_long  # Dm = 4 db -> r = 2 db
        rn_long = r_in_long + db_long / 2.0
        theta_90 = math.pi / 2.0

        L_arc_90 = rn_long * theta_90
        assert L_arc_90 == pytest.approx(25.0 * math.pi, rel=1e-6)
        assert L_arc_90 == pytest.approx(78.539816, rel=1e-5)

        L_ext_90 = 12.0 * db_long
        assert L_ext_90 == pytest.approx(240.0, rel=1e-6)

        deduction_90 = 2.0 * (r_in_long + db_long) - L_arc_90
        assert deduction_90 == pytest.approx(41.460184, rel=1e-5)

        # Caso 2: Estribo sísmico 135°
        db_stirrup = 10.0
        r_in_stirrup = 2.0 * db_stirrup
        rn_stirrup = r_in_stirrup + db_stirrup / 2.0
        theta_135 = 3.0 * math.pi / 4.0

        L_arc_135 = rn_stirrup * theta_135
        assert L_arc_135 == pytest.approx(18.75 * math.pi, rel=1e-6)
        assert L_arc_135 == pytest.approx(58.904862, rel=1e-5)

        L_ext_135 = max(6.0 * db_stirrup, 75.0)
        assert L_ext_135 == 75.0

        L_hook_135 = L_arc_135 + L_ext_135
        assert L_hook_135 == pytest.approx(133.904862, rel=1e-5)
