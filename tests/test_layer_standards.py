"""Tests layer standards multi-país."""
from dxfstructuraljm.layer_standards import STANDARDS, lookup, naming_for


def test_5_estandares():
    assert len(STANDARDS) == 5


def test_naming_us():
    s = naming_for("US")
    assert s is not None
    assert s.code_id == "AIA-NCS-US"


def test_naming_co():
    s = naming_for("CO")
    assert s is not None and "NTC" in s.code_id


def test_naming_sg():
    s = naming_for("SG")
    assert s.code_id == "BCA-CORENET-SG"


def test_naming_au():
    s = naming_for("AU")
    assert s.code_id == "NATSPEC-AU"


def test_naming_unknown():
    assert naming_for("ZZ") is None
