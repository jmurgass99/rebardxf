"""Tests para autocad_live (mock COM)."""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from rebardxf.integration import autocad_live


# ---- fake pyautocad inyectado en sys.modules ---------------------------

@pytest.fixture(autouse=True)
def _fake_pyautocad(monkeypatch):
    mod = types.ModuleType("pyautocad")

    def _APoint(*args):
        return tuple(args)

    def _aDouble(*args):
        return list(args)

    mod.APoint = _APoint
    mod.aDouble = _aDouble
    mod.Autocad = MagicMock(name="Autocad")
    monkeypatch.setitem(sys.modules, "pyautocad", mod)
    yield mod


# ---- helpers ----------------------------------------------------------

def _make_acad_mock() -> MagicMock:
    acad = MagicMock(name="acad")
    acad.ActiveDocument.ModelSpace = MagicMock(name="ModelSpace")
    acad.ActiveDocument.Layers = MagicMock(name="Layers")
    acad.ActiveDocument.Layers.Item.side_effect = Exception("missing")
    acad.ActiveDocument.Layers.Add.return_value = MagicMock(name="Layer")
    return acad


# ---- tests ------------------------------------------------------------

def test_context_manager_uses_injected_acad():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        assert cad.acad is acad


def test_set_layer_creates_and_activates():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        cad.set_layer("S-COLU-CONC", color=1)
    acad.ActiveDocument.Layers.Add.assert_called_once_with("S-COLU-CONC")
    assert acad.ActiveDocument.ActiveLayer is not None


def test_set_layer_reuses_existing():
    acad = _make_acad_mock()
    existing = MagicMock(name="ExistingLayer")
    acad.ActiveDocument.Layers.Item.side_effect = None
    acad.ActiveDocument.Layers.Item.return_value = existing
    with autocad_live.AutoCADClient(acad=acad) as cad:
        cad.set_layer("S-COLU-CONC", color=2)
    acad.ActiveDocument.Layers.Add.assert_not_called()
    assert existing.color == 2


def test_draw_polyline_passes_flat_coords():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        cad.draw_polyline([(0, 0), (1000, 0), (1000, 500)])
    acad.ActiveDocument.ModelSpace.AddPolyline.assert_called_once()
    args, _ = acad.ActiveDocument.ModelSpace.AddPolyline.call_args
    coords = args[0]
    # 3 puntos × 3 coords
    assert len(coords) == 9
    assert coords[0:3] == [0.0, 0.0, 0.0]


def test_draw_text_calls_addtext():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        cad.draw_text((100, 200), "VIGA-1", height=250)
    acad.ActiveDocument.ModelSpace.AddText.assert_called_once()
    args, _ = acad.ActiveDocument.ModelSpace.AddText.call_args
    assert args[0] == "VIGA-1"
    assert args[2] == 250.0


def test_insert_block_calls_insertblock():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        cad.insert_block("BLK_FOOTING", (10, 20), scale=2.0, rotation=1.57)
    acad.ActiveDocument.ModelSpace.InsertBlock.assert_called_once()


def test_apply_layer_standard_us():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        std = cad.apply_layer_standard("US")
    assert std is not None
    assert std.code_id == "AIA-NCS-US"
    acad.ActiveDocument.Layers.Add.assert_called_once_with("S-COLU-CONC")


def test_apply_layer_standard_unknown_country():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        result = cad.apply_layer_standard("XX")
    assert result is None


def test_client_without_connection_raises():
    cad = autocad_live.AutoCADClient()
    with pytest.raises(RuntimeError):
        _ = cad.acad


def test_invalid_point_raises():
    acad = _make_acad_mock()
    with autocad_live.AutoCADClient(acad=acad) as cad:
        with pytest.raises(ValueError):
            cad.draw_polyline([(1, 2, 3, 4)])
