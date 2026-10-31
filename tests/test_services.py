"""Tests para la capa de servicios."""
from __future__ import annotations
import pytest

from rebardxf.exceptions import ConfigurationError, GeometryError
from rebardxf.services import (
    ColumnSectionInput, draw_column_section,
    BeamSectionInput, draw_beam_section,
    FootingPlanInput, draw_footing_plan,
    FootingRebarInput, draw_footing_rebar,
    WallSectionInput, draw_wall_section,
    ColumnRebarInput, draw_column_rebar,
    RebarScheduleInput, build_rebar_schedule,
)
from rebardxf.services.column_drawings import _BarSpec as ColBar
from rebardxf.services.footing_drawings import _RebarSpec as FBar
from rebardxf.services.schedules import _RebarItem


pytestmark = pytest.mark.integration


def test_draw_column_section(tmp_dxf):
    meta = draw_column_section(ColumnSectionInput(label="C-T"), tmp_dxf)
    assert tmp_dxf.exists()
    assert meta["label"] == "C-T"
    assert meta["n_total_entities"] > 0
    assert "summary" in meta


def test_column_section_invalid_dim():
    with pytest.raises(GeometryError):
        draw_column_section(ColumnSectionInput(b_mm=-1), "/tmp/x.dxf")


def test_column_section_invalid_bars(tmp_dxf):
    with pytest.raises(ConfigurationError):
        draw_column_section(ColumnSectionInput(bars=[]), tmp_dxf)


def test_draw_beam_section(tmp_dxf):
    meta = draw_beam_section(BeamSectionInput(label="V-T"), tmp_dxf)
    assert tmp_dxf.exists()
    assert meta["n_total_entities"] > 0


def test_beam_invalid_cover(tmp_dxf):
    with pytest.raises(GeometryError):
        draw_beam_section(BeamSectionInput(cover_mm=500), tmp_dxf)


def test_draw_footing_plan(tmp_dxf):
    inp = FootingPlanInput(footings=[
        {"label": "Z-1", "x": 0, "y": 0, "B": 2000, "L": 2000,
         "d": 500, "As_x": 800, "As_y": 800, "db": 16},
        {"label": "Z-2", "x": 5000, "y": 0, "B": 2500, "L": 2500,
         "d": 600},
    ])
    meta = draw_footing_plan(inp, tmp_dxf)
    assert meta["n_footings"] == 2
    assert tmp_dxf.exists()


def test_footing_empty_raises():
    with pytest.raises(ConfigurationError):
        draw_footing_plan(FootingPlanInput(footings=[]), "/tmp/x.dxf")


def test_footing_missing_field_raises():
    with pytest.raises(ConfigurationError):
        draw_footing_plan(FootingPlanInput(
            footings=[{"label": "Z", "x": 0, "y": 0, "B": 1000}]
        ), "/tmp/x.dxf")


def test_draw_wall_section(tmp_dxf):
    meta = draw_wall_section(WallSectionInput(label="M-T"), tmp_dxf)
    assert tmp_dxf.exists()
    assert meta["n_total_entities"] > 0


def test_wall_be_too_long(tmp_dxf):
    with pytest.raises(GeometryError):
        draw_wall_section(WallSectionInput(Lw_mm=1000, Lbe_mm=600), tmp_dxf)


def test_draw_column_rebar(tmp_dxf):
    inp = ColumnRebarInput(
        name="C-T", longitudinal=[
            ColBar(mark="1", diameter_mm=25, length_m=3.2, quantity=8),
        ],
        stirrups=[ColBar(mark="E1", diameter_mm=10, length_m=1.8, quantity=20)],
    )
    meta = draw_column_rebar(inp, tmp_dxf)
    assert meta["total_kg"] > 0
    assert tmp_dxf.exists()


def test_column_rebar_no_longitudinal():
    with pytest.raises(ConfigurationError):
        draw_column_rebar(ColumnRebarInput(longitudinal=[]), "/tmp/x.dxf")


def test_draw_footing_rebar(tmp_dxf):
    inp = FootingRebarInput(
        name="Z-T",
        bottom_x=FBar("M1", 16, 2.0, 10),
        bottom_y=FBar("M2", 16, 2.0, 10),
    )
    meta = draw_footing_rebar(inp, tmp_dxf)
    assert meta["total_kg"] > 0
    assert tmp_dxf.exists()


def test_footing_rebar_no_bars():
    with pytest.raises(ConfigurationError):
        draw_footing_rebar(FootingRebarInput(), "/tmp/x.dxf")


def test_build_rebar_schedule():
    inp = RebarScheduleInput(entries=[
        _RebarItem("1", "C-1", 25, 8, 3200),
        _RebarItem("2", "V-1", 16, 3, 5200),
    ])
    res = build_rebar_schedule(inp)
    assert res["n_entries"] == 2
    assert res["total_kg"] > 0
    assert len(res["table"]) == 2


def test_schedule_empty_raises():
    with pytest.raises(ConfigurationError):
        build_rebar_schedule(RebarScheduleInput(entries=[]))


def test_schedule_invalid_count_raises():
    with pytest.raises(ConfigurationError):
        build_rebar_schedule(RebarScheduleInput(entries=[
            _RebarItem("1", "C", 16, 0, 1000),
        ]))
