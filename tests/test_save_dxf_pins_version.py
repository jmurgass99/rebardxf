# -*- coding: utf-8 -*-
"""save_dxf escribe la versión DXF pedida (hasta la 1.2.0 el parámetro se ignoraba)."""
from __future__ import annotations

import ezdxf
import pytest

from rebardxf.export import SUPPORTED_VERSIONS, save_dxf, verify
from rebardxf.exceptions import ConfigurationError

CODES = {"R2000": "AC1015", "R2004": "AC1018", "R2007": "AC1021", "R2010": "AC1024", "R2013": "AC1027", "R2018": "AC1032"}


@pytest.mark.parametrize("label", SUPPORTED_VERSIONS)
def test_saved_file_has_requested_version(tmp_path, label):
    doc = ezdxf.new("R2018")
    doc.modelspace().add_line((0, 0), (100, 50))
    path = save_dxf(doc, tmp_path / f"{label}.dxf", dxfversion=label)
    assert ezdxf.readfile(path).dxfversion == CODES[label]
    assert verify(path)["ok"]


def test_unknown_version_is_rejected(tmp_path):
    doc = ezdxf.new("R2018")
    with pytest.raises(ConfigurationError):
        save_dxf(doc, tmp_path / "x.dxf", dxfversion="R1999")
