"""Tests del auto-generador de despiece de columnas y zapatas."""
from __future__ import annotations
import pytest
import ezdxf

from dxfstructuraljm.column_rebar_detail import (
    ColumnRebarBar, ColumnRebarDetail, render_column_rebar_detail,
)
from dxfstructuraljm.footing_rebar_detail import (
    FootingRebarDetail, render_footing_rebar_detail,
)


def test_bar_weight_calculation():
    b = ColumnRebarBar(mark="A", diameter_mm=20, length_m=6.0, quantity=4)
    assert 55 < b.weight_kg < 65


def test_render_column_creates_file(tmp_path):
    detail = ColumnRebarDetail(
        name="C-1", b_mm=500, h_mm=500, H_mm=3000,
        longitudinal=[ColumnRebarBar("A", 25, 3.0, 8)],
        stirrups=[ColumnRebarBar("E", 10, 0.6, 20)],
        project="Demo",
    )
    out = render_column_rebar_detail(detail, tmp_path / "col.dxf")
    assert out.exists() and out.stat().st_size > 2000


def test_column_dxf_has_entities(tmp_path):
    detail = ColumnRebarDetail(
        name="C-1", b_mm=500, h_mm=500, H_mm=3000,
        longitudinal=[ColumnRebarBar("A", 25, 3.0, 8)],
        stirrups=[ColumnRebarBar("E", 10, 0.6, 20)],
    )
    out = render_column_rebar_detail(detail, tmp_path / "col.dxf")
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    entities_by_type: dict[str, int] = {}
    for e in msp:
        entities_by_type[e.dxftype()] = entities_by_type.get(e.dxftype(), 0) + 1
    assert entities_by_type.get("LWPOLYLINE", 0) > 1
    assert entities_by_type.get("TEXT", 0) > 5


def test_footing_render_creates_file(tmp_path):
    detail = FootingRebarDetail(
        name="Z-1", Lx_mm=2500, Ly_mm=2500, h_mm=600, cover_mm=50,
        bottom_x=ColumnRebarBar("A", 16, 2.4, 12),
        bottom_y=ColumnRebarBar("B", 16, 2.4, 12),
        top_x=ColumnRebarBar("C", 12, 2.4, 8),
        top_y=ColumnRebarBar("D", 12, 2.4, 8),
        project="Demo",
    )
    out = render_footing_rebar_detail(detail, tmp_path / "foot.dxf")
    assert out.exists() and out.stat().st_size > 2000


def test_footing_dxf_has_rebar_circles(tmp_path):
    detail = FootingRebarDetail(
        name="Z-1", Lx_mm=2500, Ly_mm=2500, h_mm=600,
        bottom_x=ColumnRebarBar("A", 16, 2.4, 10),
    )
    out = render_footing_rebar_detail(detail, tmp_path / "f.dxf")
    doc = ezdxf.readfile(str(out))
    msp = doc.modelspace()
    circles = [e for e in msp if e.dxftype() == "CIRCLE"]
    assert len(circles) >= 10


def test_column_total_weight_in_schedule(tmp_path):
    detail = ColumnRebarDetail(
        name="C-1", b_mm=400, h_mm=400, H_mm=3000,
        longitudinal=[ColumnRebarBar("A", 20, 3.0, 6)],
    )
    out = render_column_rebar_detail(detail, tmp_path / "col2.dxf")
    doc = ezdxf.readfile(str(out))
    texts = [e.dxf.text for e in doc.modelspace() if e.dxftype() == "TEXT"]
    assert any("TOTAL" in t for t in texts)
