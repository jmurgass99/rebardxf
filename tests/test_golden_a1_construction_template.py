"""Golden test para lámina A1 con cajetín normalizado envolviendo planos (templates_construction).

Requisitos:
1. Dimensiones estándar A1 (841 x 594 mm) con margen interior (10 mm) y cajetín (180 x 80 mm).
2. Envolvente correcta de detalles estructurales (zapata + sección de viga) con offset de coordenadas.
3. Exportación a DXF y verificación de entidades y capas normalizadas.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
import ezdxf

from rebardxf.templates_construction import (
    SheetA1LayoutInput,
    build_a1_sheet_with_titleblock,
    build_footing_template,
    FootingTemplateInput,
    build_beam_section_template,
    BeamSectionTemplateInput,
    render_a1_sheet_to_dxf,
)


def test_golden_a1_construction_sheet_wrapping_structural_drawings():
    """GOLDEN. Verificación de lámina A1 normalizada con cajetín y dibujos constructivos incrustados."""
    # 1. Crear dibujos de detalle
    footing_geom = build_footing_template(FootingTemplateInput(B_mm=2000, L_mm=2000, H_mm=500))
    beam_geom = build_beam_section_template(BeamSectionTemplateInput(b_mm=300, h_mm=500))

    # 2. Configurar lámina A1 envolvente
    sheet_input = SheetA1LayoutInput(
        project_name="Residencial Los Álamos",
        drawing_title="Detalles de Cimentación y Vigas",
        drawing_number="EST-01",
        revision="A",
        author="JM",
        scale="1:50 / 1:25",
    )

    # Incrustar detalles en posiciones específicas del área útil
    drawings_positioned = [
        (footing_geom, (50.0, 100.0)),
        (beam_geom, (450.0, 200.0)),
    ]

    sheet_geom = build_a1_sheet_with_titleblock(sheet_input, drawings_positioned)

    # 3. Comprobaciones geométricas de la lámina
    # Borde papel: (0, 0, 841, 594)
    assert (0.0, 0.0, 841.0, 594.0) in sheet_geom.rectangles
    # Margen útil: (10, 10, 821, 574)
    assert (10.0, 10.0, 821.0, 574.0) in sheet_geom.rectangles
    # Cajetín en esquina inferior derecha: x = 841 - 10 - 180 = 651, y = 10, w = 180, h = 80
    assert (651.0, 10.0, 180.0, 80.0) in sheet_geom.rectangles

    # Comprobación de textos de rotulación en el cajetín
    all_texts = [t["text"] for t in sheet_geom.texts]
    assert any("Residencial Los Álamos" in txt for txt in all_texts)
    assert any("EST-01" in txt for txt in all_texts)
    assert any("REV: A" in txt for txt in all_texts)

    # 4. Render a DXF y verificación de archivo
    with tempfile.TemporaryDirectory() as tmpdir:
        dxf_path = Path(tmpdir) / "lamina_A1_EST01.dxf"
        render_a1_sheet_to_dxf(sheet_geom, str(dxf_path))

        assert dxf_path.exists()
        assert dxf_path.stat().st_size > 1000

        doc = ezdxf.readfile(str(dxf_path))
        msp = doc.modelspace()
        assert len(list(msp.query("LINE"))) > 10
        assert len(list(msp.query("TEXT"))) >= 6

        # Verificación explícita de capas usadas: BORDER, GEOMETRY, REBAR, TEXT
        border_lines = list(msp.query("LINE[layer=='BORDER']"))
        geom_lines = list(msp.query("LINE[layer=='GEOMETRY']"))
        rebar_circles = list(msp.query("CIRCLE[layer=='REBAR']"))
        texts = list(msp.query("TEXT[layer=='TEXT']"))

        assert len(border_lines) >= 16, "Deben existir líneas en capa BORDER (marco y cajetín)"
        assert len(geom_lines) >= 8, "Deben existir líneas en capa GEOMETRY (secciones y zapatas)"
        assert len(rebar_circles) > 0, "Deben existir círculos en capa REBAR"
        assert len(texts) >= 6, "Deben existir textos en capa TEXT"


def test_golden_templates_construction_missing_key_raises_keyerror():
    """GOLDEN. La ausencia de datos obligatorios ('pos' o 'text') debe lanzar KeyError y no fabricar defaults vacíos."""
    from rebardxf.templates_construction import TemplateGeometry

    # 1. Error en build_a1_sheet_with_titleblock con texto sin pos
    invalid_geom = TemplateGeometry(texts=[{"text": "Texto sin pos"}])
    sheet_input = SheetA1LayoutInput(
        project_name="Test", drawing_title="Test", drawing_number="01"
    )
    with pytest.raises(KeyError, match="Texto incompleto"):
        build_a1_sheet_with_titleblock(sheet_input, [(invalid_geom, (0.0, 0.0))])

    # 2. Error en render_a1_sheet_to_dxf con texto sin text
    invalid_sheet = TemplateGeometry(texts=[{"pos": (10.0, 10.0)}])
    with tempfile.TemporaryDirectory() as tmpdir:
        out = str(Path(tmpdir) / "err.dxf")
        with pytest.raises(KeyError, match="Texto incompleto"):
            render_a1_sheet_to_dxf(invalid_sheet, out)

