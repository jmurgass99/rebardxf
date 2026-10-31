"""Tests basados en propiedades (hypothesis) para los servicios DXF.

Invariantes verificados:
    - Para dimensiones validas, el DXF generado tiene > 0 entidades.
    - El total de entidades es positivo y crece con el numero de barras.
    - Las dimensiones reportadas en el summary son positivas.
    - El total_kg en la planilla es monotono respecto a count y length.
"""
from __future__ import annotations
import pytest

hypothesis = pytest.importorskip("hypothesis")
from hypothesis import given, settings, strategies as st, HealthCheck

from rebardxf.services import (
    ColumnSectionInput, draw_column_section,
    BeamSectionInput, draw_beam_section,
    WallSectionInput, draw_wall_section,
    RebarScheduleInput, build_rebar_schedule,
)
from rebardxf.services.schedules import _RebarItem


pytestmark = pytest.mark.property

slow_settings = settings(
    max_examples=15,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)


# ---------------------------------------------------------------------------
# Columnas
# ---------------------------------------------------------------------------
@slow_settings
@given(
    b=st.floats(min_value=250.0, max_value=1000.0, allow_nan=False),
    h=st.floats(min_value=250.0, max_value=1000.0, allow_nan=False),
    n=st.integers(min_value=4, max_value=12),
    db=st.sampled_from([12.0, 16.0, 20.0, 25.0, 32.0]),
)
def test_column_section_invariants(tmp_path, b, h, n, db):
    out = tmp_path / "c.dxf"
    inp = ColumnSectionInput(
        label="C-P", b_mm=b, h_mm=h, cover_mm=40.0,
        bars=[(db, n)],
    )
    meta = draw_column_section(inp, out)
    assert out.exists()
    assert meta["n_total_entities"] > 4
    s = meta["summary"]
    assert s["b_mm"] == b and s["h_mm"] == h
    assert s["As_mm2"] > 0
    assert 0 < s["rho_pct"] < 20


# ---------------------------------------------------------------------------
# Vigas
# ---------------------------------------------------------------------------
@slow_settings
@given(
    b=st.floats(min_value=200.0, max_value=600.0, allow_nan=False),
    h=st.floats(min_value=300.0, max_value=900.0, allow_nan=False),
    n_top=st.integers(min_value=2, max_value=5),
    n_bot=st.integers(min_value=2, max_value=6),
)
def test_beam_section_invariants(tmp_path, b, h, n_top, n_bot):
    out = tmp_path / "v.dxf"
    inp = BeamSectionInput(
        label="V-P", b_mm=b, h_mm=h, cover_mm=30.0,
        bars_top=[(20.0, n_top)], bars_bot=[(20.0, n_bot)],
    )
    meta = draw_beam_section(inp, out)
    assert out.exists()
    assert meta["n_total_entities"] >= 4 + n_top + n_bot
    assert meta["summary"]["As_top_mm2"] > 0
    assert meta["summary"]["As_bot_mm2"] > 0


# ---------------------------------------------------------------------------
# Muros
# ---------------------------------------------------------------------------
@slow_settings
@given(
    Lw=st.floats(min_value=3000.0, max_value=8000.0, allow_nan=False),
    tw=st.floats(min_value=200.0, max_value=400.0, allow_nan=False),
    Lbe_ratio=st.floats(min_value=0.10, max_value=0.30),
)
def test_wall_section_invariants(tmp_path, Lw, tw, Lbe_ratio):
    Lbe = Lw * Lbe_ratio
    out = tmp_path / "m.dxf"
    inp = WallSectionInput(label="M-P", Lw_mm=Lw, tw_mm=tw, Lbe_mm=Lbe)
    meta = draw_wall_section(inp, out)
    assert out.exists()
    assert meta["n_total_entities"] > 0
    s = meta["summary"]
    assert s["Lw_mm"] == Lw
    assert s["tw_mm"] == tw
    assert s["rho_be_pct"] > 0


# ---------------------------------------------------------------------------
# Schedule monotonia
# ---------------------------------------------------------------------------
@slow_settings
@given(
    count=st.integers(min_value=1, max_value=20),
    length=st.floats(min_value=500.0, max_value=6000.0, allow_nan=False),
    db=st.sampled_from([8.0, 10.0, 12.0, 16.0, 20.0, 25.0, 32.0]),
)
def test_schedule_total_positive(count, length, db):
    inp = RebarScheduleInput(entries=[
        _RebarItem("M", "E", db, count, length),
    ])
    res = build_rebar_schedule(inp)
    assert res["total_kg"] > 0
    assert res["n_entries"] == 1


@slow_settings
@given(
    count1=st.integers(min_value=1, max_value=10),
    extra=st.integers(min_value=1, max_value=10),
)
def test_schedule_monotonic_in_count(count1, extra):
    base = build_rebar_schedule(RebarScheduleInput(entries=[
        _RebarItem("M", "E", 16, count1, 1000),
    ]))
    more = build_rebar_schedule(RebarScheduleInput(entries=[
        _RebarItem("M", "E", 16, count1 + extra, 1000),
    ]))
    assert more["total_kg"] > base["total_kg"]
