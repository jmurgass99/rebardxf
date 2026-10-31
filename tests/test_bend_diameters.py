"""Tests for ACI 318-19 §25.3 minimum bend diameter table."""
import math
import pytest

from rebardxf.rebar_shapes import (
    min_bend_diameter_aci,
    BAR_DIAMETERS_MM,
    BAR_DIAMETERS_METRIC_MM,
    hook_90,
    closed_stirrup,
)


# ---------------------------------------------------------------------------
# ACI table — imperial bars
# ---------------------------------------------------------------------------
def test_standard_hook_5_is_6db():
    # #5: db = 15.875 mm; D = 6 db; R = 3 db = 47.625 mm
    D = min_bend_diameter_aci("#5", "standard_90")
    assert math.isclose(D, 6 * 15.875, rel_tol=1e-9)
    assert math.isclose(D / 2.0, 95.25 / 2.0, rel_tol=1e-9)  # R inside


def test_standard_hook_9_is_8db():
    # Spec: 8 * 28.7 = 229.6 mm (D, inside diameter)
    db = BAR_DIAMETERS_MM["#9"]   # 28.65 mm
    D = min_bend_diameter_aci("#9", "standard_90")
    assert math.isclose(D, 8 * db, rel_tol=1e-9)
    # spec value (using db≈28.7)
    assert abs(D - 229.6) < 0.5


def test_stirrup_4_is_4db():
    # #4 stirrup: D = 4 db = 50.8 mm
    D = min_bend_diameter_aci("#4", "stirrup_90")
    assert math.isclose(D, 50.8, rel_tol=1e-9)


def test_stirrup_135_same_as_90():
    assert (min_bend_diameter_aci("#5", "stirrup_135")
            == min_bend_diameter_aci("#5", "stirrup_90"))


def test_stirrup_large_bar_is_6db():
    # #6..#8 stirrups: 6 db
    assert math.isclose(min_bend_diameter_aci("#8", "stirrup_90"),
                        6 * 25.4, rel_tol=1e-9)


def test_seismic_hook_table():
    # §25.3.4: #9..#11 seismic stirrups = 8 db
    db = BAR_DIAMETERS_MM["#11"]
    assert math.isclose(min_bend_diameter_aci("#11", "seismic"),
                        8 * db, rel_tol=1e-9)


def test_large_bars_standard_hook_is_10db():
    db14 = BAR_DIAMETERS_MM["#14"]
    db18 = BAR_DIAMETERS_MM["#18"]
    assert math.isclose(min_bend_diameter_aci("#14", "standard_180"),
                        10 * db14, rel_tol=1e-9)
    assert math.isclose(min_bend_diameter_aci("#18", "standard_90"),
                        10 * db18, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Metric mapping
# ---------------------------------------------------------------------------
def test_metric_m16_stirrup_135():
    # M16 (db=16 mm) -> closest imperial = #5 -> stirrup factor 4
    # Expected D = 4 * 16 = 64 mm
    D = min_bend_diameter_aci("M16", "stirrup_135")
    assert math.isclose(D, 64.0, rel_tol=1e-9)


def test_metric_m32_standard_hook():
    # M32 -> #10 -> 8 db; db (metric) = 32 mm; D = 256
    assert math.isclose(min_bend_diameter_aci("M32", "standard_90"),
                        8 * 32.0, rel_tol=1e-9)


def test_numeric_db_input():
    # Numeric db: 16 mm -> nearest imperial = #5 -> standard hook 6*16 = 96
    assert math.isclose(min_bend_diameter_aci(16.0, "standard_90"),
                        6 * 16.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
def test_invalid_hook_type():
    with pytest.raises(ValueError):
        min_bend_diameter_aci("#5", "bogus")


def test_unknown_bar():
    with pytest.raises(KeyError):
        min_bend_diameter_aci("#99", "standard_90")


def test_no_stirrup_for_14_18():
    # ACI table does not standardise stirrups for #14 / #18
    with pytest.raises(NotImplementedError):
        min_bend_diameter_aci("#14", "stirrup_90")
    with pytest.raises(NotImplementedError):
        min_bend_diameter_aci("#18", "stirrup_135")


# ---------------------------------------------------------------------------
# Backward compatibility — shape constructors
# ---------------------------------------------------------------------------
def test_hook_90_without_bar_keeps_legacy_behavior():
    # No 'bar' kwarg -> uses legacy bend_radius; must not raise.
    pts_legacy = hook_90(leg=500, db=12.0)
    pts_aci = hook_90(leg=500, db=12.0, bar="#4")
    assert isinstance(pts_legacy, list) and isinstance(pts_aci, list)
    # ACI radius for #4 (4*12.7/2 = 25.4) differs from legacy (3*12=36) -> arc geometry differs
    assert pts_legacy != pts_aci


def test_closed_stirrup_accepts_bar_kwarg():
    pts = closed_stirrup(b=300, h=500, cover=25, db=12.7, bar="#4")
    assert len(pts) > 0
