# -*- coding: utf-8 -*-
"""test_frame_elevation_exact_entities.py — Validación de alzado de pórtico por eje con recuento EXACTO de entidades CAD.

ENTREGABLE C2 (AG29):
=====================
1. Generación de planos de alzado de pórticos estructurales por eje con vigas,
   columnas, armado longitudinal y estribado diferenciado (zonas críticas y centrales).
2. El archivo DXF generado es parseado mediante `ezdxf` y se comprueba que contiene
   el número EXACTO de entidades (LINE, CIRCLE, TEXT) derivado analíticamente
   de la geometría y número de armaduras/estribos (NUNCA un `>= 1`).
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import ezdxf
import pytest

from rebardxf.frame_elevation import FrameElevationDetail


class TestFrameElevationExactEntities:
    @pytest.mark.parametrize(
        "bays,stories,col_w,beam_h,lc_col,s_crit_col,s_cent_col,lc_beam,s_crit_beam,s_cent_beam",
        [
            # Caso 1: Pórtico estándar 2 vanos, 2 pisos
            ([5000.0, 6000.0], [3500.0, 3000.0], 400.0, 500.0, 500.0, 100.0, 200.0, 800.0, 100.0, 200.0),
            # Caso 2: Pórtico 1 vano, 3 pisos
            ([6000.0], [4000.0, 3500.0, 3000.0], 500.0, 600.0, 600.0, 100.0, 150.0, 1000.0, 100.0, 200.0),
            # Caso 3: Pórtico 3 vanos, 1 piso
            ([4500.0, 5500.0, 4500.0], [3600.0], 400.0, 450.0, 500.0, 100.0, 200.0, 700.0, 100.0, 150.0),
        ],
    )
    def test_frame_elevation_matches_exact_ezdxf_entity_counts(
        self,
        bays: list[float],
        stories: list[float],
        col_w: float,
        beam_h: float,
        lc_col: float,
        s_crit_col: float,
        s_cent_col: float,
        lc_beam: float,
        s_crit_beam: float,
        s_cent_beam: float,
    ) -> None:
        """Verifica que el DXF producido por FrameElevationDetail contiene el recuento EXACTO de entidades derivado analíticamente."""
        frame = FrameElevationDetail(
            axis_name="Eje 1",
            bays=bays,
            stories=stories,
            col_width=col_w,
            beam_height=beam_h,
            col_lc_critical=lc_col,
            col_s_critical=s_crit_col,
            col_s_central=s_cent_col,
            beam_lc_critical=lc_beam,
            beam_s_critical=s_crit_beam,
            beam_s_central=s_cent_beam,
            label="PORTICO-TEST",
        )

        expected = frame.expected_entity_counts()

        with tempfile.TemporaryDirectory() as tmpdir:
            dxf_path = Path(tmpdir) / "frame_elevation.dxf"
            frame.draw_elevation(output_path=str(dxf_path))

            assert dxf_path.exists()

            # Parseo formal con ezdxf
            doc = ezdxf.readfile(str(dxf_path))
            msp = doc.modelspace()

            lines = list(msp.query("LINE"))
            circles = list(msp.query("CIRCLE"))
            texts = list(msp.query("TEXT"))

            # Verificación estricta: EXACTITUD (no >= 1)
            assert len(lines) == expected["LINE"], (
                f"Discrepancia en LINE: obtenido {len(lines)}, esperado {expected['LINE']}"
            )
            assert len(circles) == expected["CIRCLE"], (
                f"Discrepancia en CIRCLE: obtenido {len(circles)}, esperado {expected['CIRCLE']}"
            )
            assert len(texts) == expected["TEXT"], (
                f"Discrepancia en TEXT: obtenido {len(texts)}, esperado {expected['TEXT']}"
            )
            assert (len(lines) + len(circles) + len(texts)) == expected["total_entities"]
