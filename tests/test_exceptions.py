"""Tests para la jerarquia de excepciones tipadas."""
from __future__ import annotations
import pytest

from dxfstructuraljm.exceptions import (
    DXFError, ConfigurationError, GeometryError,
    TemplateError, DependencyError,
)
from dxfstructuraljm import templates


pytestmark = pytest.mark.unit


def test_dxf_error_is_exception():
    assert issubclass(DXFError, Exception)


def test_configuration_error_is_value_error():
    assert issubclass(ConfigurationError, ValueError)
    assert issubclass(ConfigurationError, DXFError)


def test_geometry_error_is_value_error():
    assert issubclass(GeometryError, ValueError)
    assert issubclass(GeometryError, DXFError)


def test_template_error_is_value_error():
    assert issubclass(TemplateError, ValueError)


def test_dependency_error_is_import_error():
    assert issubclass(DependencyError, ImportError)
    assert issubclass(DependencyError, DXFError)


def test_template_unknown_size_raises_template_error():
    with pytest.raises(TemplateError):
        templates.SheetTemplate(size="A9")


def test_template_unknown_size_still_raises_value_error_for_backcompat():
    with pytest.raises(ValueError):
        templates.SheetTemplate(size="A9")


def test_export_unsupported_version_raises_configuration_error():
    from dxfstructuraljm.export import save_dxf
    import ezdxf
    doc = ezdxf.new(dxfversion="R2018")
    with pytest.raises(ConfigurationError):
        save_dxf(doc, "x.dxf", dxfversion="R9999")
    # backward compat con ValueError
    with pytest.raises(ValueError):
        save_dxf(doc, "x.dxf", dxfversion="R9999")


def test_export_missing_doc_raises_dependency_error():
    from dxfstructuraljm.export import save_dxf
    with pytest.raises(DependencyError):
        save_dxf(None, "x.dxf")
    with pytest.raises(ImportError):
        save_dxf(None, "x.dxf")


def test_exceptions_reexported_from_package():
    import dxfstructuraljm as pkg
    assert pkg.DXFError is DXFError
    assert pkg.ConfigurationError is ConfigurationError
    assert pkg.GeometryError is GeometryError
    assert pkg.TemplateError is TemplateError
    assert pkg.DependencyError is DependencyError
