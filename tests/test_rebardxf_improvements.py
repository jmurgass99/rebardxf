"""Tests para mejoras de rebardxf: todas las barras en cortes de columna, db_ref en viga, paso comercial en zapata."""
from __future__ import annotations

from pathlib import Path
import ezdxf
import pytest

from rebardxf.beam_section import BeamDetail
from rebardxf.column_rebar_detail import (
    ColumnRebarBar,
    ColumnRebarDetail,
    render_column_rebar_detail,
)
from rebardxf.foundation_plan import layout_rebar_direction


def test_column_rebar_detail_draws_all_perimeter_bars(tmp_path: Path):
    """Con 12 barras longitudinales, las 3 secciones (BASE, MEDIA, CABEZA) dibujan 3*12 = 36 círculos."""
    detail = ColumnRebarDetail(
        name="C-12",
        b_mm=500.0,
        h_mm=500.0,
        H_mm=3000.0,
        cover_mm=40.0,
        longitudinal=[ColumnRebarBar("A", 25.0, 3.2, 12)],
        stirrups=[ColumnRebarBar("E", 10.0, 1.8, 20)],
    )
    out = render_column_rebar_detail(detail, tmp_path / "col12.dxf")
    doc = ezdxf.readfile(str(out))
    circles = [e for e in doc.modelspace() if e.dxftype() == "CIRCLE"]
    assert len(circles) == 36


def test_beam_section_top_vs_bot_bar_diameter_offset(tmp_path: Path):
    """El recubrimiento al centroide de las barras superiores usa el diámetro superior, no el inferior."""
    beam = BeamDetail(
        b=300.0,
        h=600.0,
        cover=30.0,
        db_stirrup=10.0,
        bars_top=[(12.0, 2)],
        bars_bot=[(32.0, 2)],
    )
    pos_top = beam._bar_x_positions(2, db_ref=12.0)
    pos_bot = beam._bar_x_positions(2, db_ref=32.0)
    assert pos_top[0] == pytest.approx(30.0 + 10.0 + 6.0)
    assert pos_bot[0] == pytest.approx(30.0 + 10.0 + 16.0)


def test_layout_rebar_direction_commercial_step():
    status, n_bars, s_dib, s_rot, _ = layout_rebar_direction(
        dim_mm=2000.0,
        depth_mm=500.0,
        As_mm2_m=1000.0,
        db_mm=16.0,
        cover_mm=75.0,
        s_commercial_step_mm=25.0,
        snap_to_commercial_step=True,
    )
    assert s_rot % 25.0 == pytest.approx(0.0)
    assert n_bars >= 10
