"""Tests para revit_dxf_link."""
from __future__ import annotations

from pathlib import Path

import ezdxf
import pytest

from dxfstructuraljm.integration import revit_dxf_link as rdl


def test_basic_entities(tmp_path):
    out = tmp_path / "revit.dxf"
    ents = [
        rdl.line((0, 0), (1000, 0), layer="S-COLU-CONC"),
        rdl.polyline([(0, 0), (1000, 0), (1000, 500)], layer="S-BEAM-CONC", close=True),
        rdl.circle((500, 500), 50, layer="S-COLU-RBAR"),
        rdl.text((100, 100), "C-1", height=200, layer="S-TEXT"),
    ]
    doc = rdl.make_revit_compatible_dxf(ents, out)
    assert out.exists()
    assert doc.header["$INSUNITS"] == 4   # MM

    # Re-leer el archivo
    doc2 = ezdxf.readfile(str(out))
    msp = doc2.modelspace()
    types = sorted(e.dxftype() for e in msp)
    assert "LINE" in types
    assert "LWPOLYLINE" in types
    assert "CIRCLE" in types
    assert "TEXT" in types


def test_layers_get_aia_colors(tmp_path):
    out = tmp_path / "layers.dxf"
    ents = [
        rdl.line((0, 0), (10, 10), layer="S-COLU-CONC"),
        rdl.line((0, 0), (10, 10), layer="S-BEAM-RBAR"),
    ]
    doc = rdl.make_revit_compatible_dxf(ents, out)
    assert doc.layers.get("S-COLU-CONC").color == rdl.AIA_COLORS["S-COLU"]
    assert doc.layers.get("S-BEAM-RBAR").color == rdl.AIA_COLORS["S-BEAM"]


def test_forbidden_entity_raises(tmp_path):
    ent = rdl.DXFEntity("3DSOLID", {}, layer="S-COLU-CONC")
    with pytest.raises(ValueError, match="3DSOLID"):
        rdl.make_revit_compatible_dxf([ent], tmp_path / "x.dxf")


def test_revit_style_exists(tmp_path):
    out = tmp_path / "style.dxf"
    rdl.make_revit_compatible_dxf([rdl.line((0, 0), (1, 1))], out)
    doc = ezdxf.readfile(str(out))
    assert "REVIT_STD" in doc.styles


def test_units_m(tmp_path):
    out = tmp_path / "m.dxf"
    opt = rdl.RevitDXFOptions(units="M")
    doc = rdl.make_revit_compatible_dxf([rdl.line((0, 0), (1, 1))], out, opt)
    assert doc.header["$INSUNITS"] == 6


def test_units_invalid_raises(tmp_path):
    opt = rdl.RevitDXFOptions(units="FT")
    with pytest.raises(ValueError):
        rdl.make_revit_compatible_dxf([rdl.line((0, 0), (1, 1))], tmp_path / "x.dxf", opt)
