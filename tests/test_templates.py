"""Tests plantillas constructivas."""
from rebardxf.templates_construction import (
    FootingTemplateInput, TitleBlockA1Input,
    build_footing_template, build_title_block_a1,
    BeamSectionTemplateInput, build_beam_section_template,
    ColumnSectionTemplateInput, build_column_section_template,
    WallSectionTemplateInput, build_wall_section_template,
)


def test_footing_geometry_no_vacia():
    g = build_footing_template(FootingTemplateInput())
    assert len(g.rectangles) >= 2  # zapata + columna
    assert len(g.circles) >= 16  # malla de barras


def test_title_block_a1():
    g = build_title_block_a1(TitleBlockA1Input(
        project_name="Edificio Test", drawing_number="E-01", revision="A",
    ))
    text_values = [t["text"] for t in g.texts]
    assert "Edificio Test" in text_values
    assert any("E-01" in v for v in text_values)


# ---------------------------------------------------------------------------
# Beam section template
# ---------------------------------------------------------------------------

def test_beam_section_default():
    """Default beam section has correct element counts."""
    g = build_beam_section_template(BeamSectionTemplateInput())
    # 2 rectangles: outline + stirrup
    assert len(g.rectangles) == 2
    # circles = n_top(3) + n_bot(3) = 6
    assert len(g.circles) == 6
    # At least dimension + annotation texts
    assert len(g.texts) >= 4


def test_beam_section_custom():
    """Custom beam with different bar counts."""
    inp = BeamSectionTemplateInput(b_mm=400, h_mm=700, cover_mm=50,
                                   n_top=4, n_bot=5, bar_dia_mm=20,
                                   stirrup_dia_mm=12, stirrup_spacing_mm=150)
    g = build_beam_section_template(inp)
    assert len(g.rectangles) == 2
    assert len(g.circles) == 4 + 5  # n_top + n_bot
    # Verify bar radius matches input
    assert g.circles[0][2] == 20 / 2.0


def test_beam_section_annotations():
    """Beam annotations include bar description."""
    inp = BeamSectionTemplateInput(bar_dia_mm=16, stirrup_dia_mm=10,
                                   stirrup_spacing_mm=200)
    g = build_beam_section_template(inp)
    text_values = [t["text"] for t in g.texts]
    assert any("⌀16" in v for v in text_values)
    assert any("Est" in v for v in text_values)


# ---------------------------------------------------------------------------
# Column section template
# ---------------------------------------------------------------------------

def test_column_section_default():
    """Default column section: 3x3 grid = 2*3 + 2*(3-2) = 8 bars."""
    g = build_column_section_template(ColumnSectionTemplateInput())
    assert len(g.rectangles) == 2  # outline + tie
    # Total bars = 2*n_bars_x + 2*(n_bars_y - 2) = 6 + 2 = 8
    assert len(g.circles) == 8
    assert len(g.texts) >= 3


def test_column_section_custom():
    """Custom column with 4x4 bars."""
    inp = ColumnSectionTemplateInput(b_mm=600, h_mm=600, cover_mm=50,
                                     n_bars_x=4, n_bars_y=4,
                                     bar_dia_mm=25, tie_dia_mm=12,
                                     tie_spacing_mm=150)
    g = build_column_section_template(inp)
    assert len(g.rectangles) == 2
    # 2*4 + 2*(4-2) = 8 + 4 = 12
    assert len(g.circles) == 12
    assert g.circles[0][2] == 25 / 2.0


def test_column_section_annotations():
    """Column annotations include bar count and tie description."""
    inp = ColumnSectionTemplateInput(n_bars_x=3, n_bars_y=3,
                                     bar_dia_mm=20, tie_dia_mm=10,
                                     tie_spacing_mm=200)
    g = build_column_section_template(inp)
    text_values = [t["text"] for t in g.texts]
    # Total bars = 8
    assert any("8⌀20" in v for v in text_values)
    assert any("Est" in v for v in text_values)


# ---------------------------------------------------------------------------
# Wall section template
# ---------------------------------------------------------------------------

def test_wall_section_default():
    """Default wall: 3 rectangles, 2*4 boundary + 6 web = 14 bars."""
    g = build_wall_section_template(WallSectionTemplateInput())
    # 3 rectangles: outline + 2 boundary zones
    assert len(g.rectangles) == 3
    # circles: 2 * boundary_bars + web_bars = 8 + 6 = 14
    assert len(g.circles) == 2 * 4 + 6
    assert len(g.texts) >= 3


def test_wall_section_custom():
    """Custom wall with different reinforcement."""
    inp = WallSectionTemplateInput(length_mm=5000, thickness_mm=300,
                                   cover_mm=50, boundary_bars=6,
                                   web_bars=10, bar_dia_mm=20)
    g = build_wall_section_template(inp)
    assert len(g.rectangles) == 3
    # 2 * 6 + 10 = 22
    assert len(g.circles) == 22
    assert g.circles[0][2] == 20 / 2.0


def test_wall_section_annotations():
    """Wall annotations include boundary and web descriptions."""
    g = build_wall_section_template(WallSectionTemplateInput())
    text_values = [t["text"] for t in g.texts]
    assert any("Borde" in v for v in text_values)
    assert any("Alma" in v for v in text_values)
