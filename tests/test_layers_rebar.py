"""Tests AIA layers + rebar schedule."""
from rebardxf.aia_layers import (
    STRUCTURAL_LAYERS, get_layer,
)
from rebardxf.rebar_schedule_block import (
    RebarItem, RebarScheduleConfig, build_schedule_geometry,
)


def test_layers_count():
    assert len(STRUCTURAL_LAYERS) >= 15


def test_layer_lookup():
    L = get_layer("S-COLU-RBAR")
    assert L is not None
    assert L.color_aci == 1


def test_layer_inexistente():
    assert get_layer("XYZ") is None


def test_rebar_item_weight():
    it = RebarItem(mark="M1", diameter_mm=16, length_mm=6000, quantity=10)
    # peso φ16 ≈ 1.58 kg/m, total = 6m·10·1.58 ≈ 94.8
    assert 80 < it.total_weight_kg < 110


def test_schedule_geometry():
    cfg = RebarScheduleConfig(items=[
        RebarItem("M1", 12, 4000, 20),
        RebarItem("M2", 16, 5000, 15),
    ])
    geom = build_schedule_geometry(cfg)
    assert geom["total_weight_kg"] > 0
    assert len(geom["texts"]) > 0
