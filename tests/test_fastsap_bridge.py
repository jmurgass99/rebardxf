"""Tests del bridge dxfstructuraljm <- fastsap."""
from __future__ import annotations
import os
import tempfile
import pytest

ezdxf = pytest.importorskip("ezdxf")

from dxfstructuraljm.integration import (
    RCSectionDesign, RebarBar,
    build_rectangular_section_design, draw_section_dxf,
)


def _typical_column():
    return build_rectangular_section_design(
        section_id="C1_600x600",
        b_mm=600, h_mm=600, cover_mm=40,
        n_bars_x=4, n_bars_y=4,
        bar_dia_mm=25, tie_dia_mm=12, tie_spacing_mm=100,
        fc_MPa=30, fy_MPa=500,
    )


def test_build_section_basic():
    d = _typical_column()
    assert d.b_mm == 600
    assert d.h_mm == 600
    # 4x4 esquinado: 4*2 (sup+inf) + 2*2 (laterales sin duplicar) = 12
    assert len(d.bars) == 12
    assert d.bars[0].diameter_mm == 25


def test_build_section_2x2_perimeter():
    """2x2 = solo las 4 esquinas."""
    d = build_rectangular_section_design(
        section_id="C_min", b_mm=300, h_mm=300, cover_mm=30,
        n_bars_x=2, n_bars_y=2, bar_dia_mm=16, tie_dia_mm=8, tie_spacing_mm=100,
    )
    assert len(d.bars) == 4


def test_build_section_invalid():
    with pytest.raises(ValueError):
        build_rectangular_section_design(
            section_id="bad", b_mm=-100, h_mm=300, cover_mm=30,
            n_bars_x=2, n_bars_y=2, bar_dia_mm=16, tie_dia_mm=8, tie_spacing_mm=100,
        )
    with pytest.raises(ValueError):
        build_rectangular_section_design(
            section_id="too_few", b_mm=300, h_mm=300, cover_mm=30,
            n_bars_x=1, n_bars_y=2, bar_dia_mm=16, tie_dia_mm=8, tie_spacing_mm=100,
        )
    with pytest.raises(ValueError, match="imposible armar"):
        build_rectangular_section_design(
            section_id="too_thick", b_mm=100, h_mm=100, cover_mm=40,
            n_bars_x=2, n_bars_y=2, bar_dia_mm=25, tie_dia_mm=12, tie_spacing_mm=100,
        )


def test_draw_section_dxf_creates_file(tmp_path):
    d = _typical_column()
    out = tmp_path / "section.dxf"
    res = draw_section_dxf(d, str(out))
    assert out.exists()
    assert out.stat().st_size > 1000   # archivo DXF real no es trivial
    assert res.n_bars == 12
    assert res.total_As_mm2 > 0
    assert res.dxf_path == str(out)


def test_draw_section_dxf_round_trip(tmp_path):
    """Verifica que el DXF generado es valido (re-leible por ezdxf)."""
    d = _typical_column()
    out = tmp_path / "rt.dxf"
    draw_section_dxf(d, str(out))
    doc = ezdxf.readfile(str(out))
    layers = {l.dxf.name for l in doc.layers}
    assert "REBAR" in layers
    assert "TIE" in layers
    assert "CONCRETE" in layers
    # Contar circulos (barras)
    msp = doc.modelspace()
    circles = list(msp.query("CIRCLE"))
    assert len(circles) == 12


def test_draw_section_dxf_no_bars_raises(tmp_path):
    empty = RCSectionDesign(
        section_id="empty", b_mm=300, h_mm=300, cover_mm=30,
        bars=tuple(), tie_diameter_mm=8, tie_spacing_mm=100,
    )
    with pytest.raises(ValueError, match="sin barras"):
        draw_section_dxf(empty, str(tmp_path / "x.dxf"))


def test_draw_section_dxf_total_As_correct(tmp_path):
    import math
    d = build_rectangular_section_design(
        section_id="A", b_mm=400, h_mm=400, cover_mm=30,
        n_bars_x=3, n_bars_y=3, bar_dia_mm=20, tie_dia_mm=10, tie_spacing_mm=100,
    )
    res = draw_section_dxf(d, str(tmp_path / "a.dxf"))
    # 3x3 perimeter = 8 barras
    assert res.n_bars == 8
    expected_As = 8 * math.pi * (20 / 2) ** 2
    assert abs(res.total_As_mm2 - expected_As) < 1.0
