"""Tests para cuadro de cuantías."""
import pytest
from dxfstructuraljm.rebar_quantities import (
    RebarItem,
    ElementGeometry,
    diameter_mm,
    bar_weight_per_m,
    summarize_quantities,
    total_project_steel_kg,
)


def test_diameter_lookups():
    assert diameter_mm("#5", "USA") == pytest.approx(15.9)
    assert diameter_mm("16", "EU") == 16
    assert diameter_mm("N20", "AU") == 20


def test_weight_per_m_known_value():
    # #5 bar (15.9 mm) -> ~1.55 kg/m
    w = bar_weight_per_m("#5", "USA")
    assert w == pytest.approx(1.558, rel=1e-2)


def test_summary_basic():
    bars = [
        RebarItem("V-1", "#5", length_m=6.0, count=4),
        RebarItem("V-1", "#3", length_m=10.0, count=20),
        RebarItem("C-1", "#8", length_m=3.0, count=8),
    ]
    geos = [
        ElementGeometry("V-1", volume_m3=0.6),
        ElementGeometry("C-1", volume_m3=0.45),
    ]
    rows = summarize_quantities(bars, geos, code="USA")
    assert len(rows) == 2
    for r in rows:
        assert r.total_weight_kg > 0
        assert r.cuantia_kg_per_m3 > 0


def test_multi_code():
    bars = [RebarItem("V-1", "16", length_m=8.0, count=4)]
    geos = [ElementGeometry("V-1", volume_m3=0.5)]
    rows = summarize_quantities(bars, geos, code="EU")
    assert rows[0].total_weight_kg > 0
    with pytest.raises(ValueError):
        diameter_mm("#5", "ZZ")


def test_total_project():
    bars = [RebarItem("X", "#5", 10.0, 2)]
    t = total_project_steel_kg(bars, code="USA")
    assert t == pytest.approx(bar_weight_per_m("#5", "USA") * 20.0)
