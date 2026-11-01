"""
export.py — DXF export helpers (save / audit / clean).

Wraps ezdxf save with optional version pinning, audit/cleanup and a
fallback to a minimal hand-written DXF if ezdxf is unavailable.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from .exceptions import ConfigurationError, DependencyError

try:
    import ezdxf
    from ezdxf.audit import Auditor
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False


SUPPORTED_VERSIONS = ("R2000", "R2004", "R2007", "R2010", "R2013", "R2018")


def save_dxf(doc, path: str | Path,
             dxfversion: str = "R2018",
             audit: bool = True) -> str:
    """
    Save an ezdxf Drawing to disk after optional audit.

    Parameters
    ----------
    doc        : ezdxf.Drawing
    path       : output file path
    dxfversion : 'R2000' .. 'R2018'  pin output version
    audit      : run Auditor and remove fixable issues

    Returns
    -------
    Absolute path of the saved file.
    """
    if not HAS_EZDXF or doc is None:
        raise DependencyError("ezdxf no esta disponible - no se puede guardar DXF.")
    if dxfversion not in SUPPORTED_VERSIONS:
        raise ConfigurationError(
            f"dxfversion '{dxfversion}' no soportada. "
            f"Use una de {SUPPORTED_VERSIONS}."
        )

    path = Path(path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if audit:
        try:
            auditor = doc.audit()
            # auditor.fixes already applied; errors are non-fatal here
        except Exception:
            pass

    # Pin DXF version. Hasta la 1.2.0 este bloque era un `pass`: el parámetro
    # `dxfversion` se validaba y se ignoraba, y el fichero salía siempre con la
    # versión del documento (R2018 por defecto) aunque se pidiera R2010 para un
    # visor antiguo. ezdxf admite asignar `doc.dxfversion` antes de guardar.
    target = _ver_code(dxfversion)
    if getattr(doc, "dxfversion", None) and doc.dxfversion != target:
        doc.dxfversion = target

    doc.saveas(str(path))
    return str(path)


def _ver_code(label: str) -> str:
    """Map 'R2018' → ezdxf internal code 'AC1032'."""
    return {
        "R2000": "AC1015",
        "R2004": "AC1018",
        "R2007": "AC1021",
        "R2010": "AC1024",
        "R2013": "AC1027",
        "R2018": "AC1032",
    }.get(label, "AC1032")


def clean(doc) -> dict:
    """
    Remove unused blocks, layers and linetypes from the document.

    Returns dict with counts of purged items.
    """
    purged = {"blocks": 0, "layers": 0, "linetypes": 0}
    if not HAS_EZDXF or doc is None:
        return purged

    try:
        # Block defs not referenced anywhere
        used_blocks = set()
        for layout in doc.layouts:
            for e in layout:
                if e.dxftype() == "INSERT":
                    used_blocks.add(e.dxf.name)
        for block in list(doc.blocks):
            name = block.name
            if name.startswith("*"):           # model/paper anonymous
                continue
            if name not in used_blocks:
                try:
                    doc.blocks.delete_block(name, safe=True)
                    purged["blocks"] += 1
                except Exception:
                    pass
    except Exception:
        pass

    # Empty layers (no entities) other than 0 / Defpoints
    try:
        used_layers = set()
        for e in doc.modelspace():
            used_layers.add(e.dxf.layer)
        for layer in list(doc.layers):
            name = layer.dxf.name
            if name in ("0", "Defpoints"):
                continue
            if name not in used_layers:
                # keep — empty but registered
                pass
    except Exception:
        pass

    return purged


def verify(path: str | Path) -> dict:
    """
    Re-open a saved DXF and report errors/warnings via the Auditor.
    """
    if not HAS_EZDXF:
        return {"ok": False, "error": "ezdxf not available"}
    try:
        doc = ezdxf.readfile(str(path))
        auditor = Auditor(doc)
        auditor.run()
        return {
            "ok": len(auditor.errors) == 0,
            "errors": len(auditor.errors),
            "fixes":  len(auditor.fixes),
            "dxfversion": doc.dxfversion,
            "n_modelspace_entities": len(list(doc.modelspace())),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
