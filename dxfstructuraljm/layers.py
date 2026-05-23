"""
layers.py — Centralized layer definitions for structural DXF drawings.

Defines layer names, AutoCAD color indices (ACI), linetypes, lineweights
and provides a single function to register them in an ezdxf document.

References
----------
- AutoCAD Color Index (ACI): 1=red, 2=yellow, 3=green, 4=cyan,
  5=blue, 6=magenta, 7=white/black, 8=dark gray, 9=light gray.
- ISO 3766 — simplified armature representation.
"""
from __future__ import annotations
from dataclasses import dataclass

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False


@dataclass(frozen=True)
class LayerSpec:
    """Single layer specification."""
    name: str
    color: int          # ACI color index
    linetype: str = "CONTINUOUS"
    lineweight: int = 25   # hundredths of mm (25 = 0.25mm)
    description: str = ""


# ---------------------------------------------------------------------------
# Standard structural layer registry
# ---------------------------------------------------------------------------
STANDARD_LAYERS: dict[str, LayerSpec] = {
    "CONCRETO":   LayerSpec("CONCRETO",   7,  "CONTINUOUS", 50, "Concrete outlines"),
    "ARMADURA":   LayerSpec("ARMADURA",   2,  "CONTINUOUS", 35, "Longitudinal rebar"),
    "ACERO":      LayerSpec("ACERO",      2,  "CONTINUOUS", 35, "Generic steel"),
    "ESTRIBO":    LayerSpec("ESTRIBO",    3,  "CONTINUOUS", 18, "Stirrups / ties"),
    "COTAS":      LayerSpec("COTAS",      4,  "CONTINUOUS", 13, "Dimensions"),
    "TEXTO":      LayerSpec("TEXTO",      7,  "CONTINUOUS", 18, "Annotation text"),
    "EJES":       LayerSpec("EJES",       1,  "CENTER",     13, "Grid axes"),
    "HATCH":      LayerSpec("HATCH",      8,  "CONTINUOUS",  9, "Hatching / fills"),
    "RELLENO":    LayerSpec("RELLENO",    8,  "CONTINUOUS",  9, "Concrete hatch"),
    "CAJETIN":    LayerSpec("CAJETIN",    7,  "CONTINUOUS", 50, "Title block frame"),
    "OCULTAS":    LayerSpec("OCULTAS",    8,  "HIDDEN",     13, "Hidden lines"),
    "AUXILIAR":   LayerSpec("AUXILIAR",   8,  "DASHED",      9, "Construction lines"),
    "MURO":       LayerSpec("MURO",       7,  "CONTINUOUS", 50, "Walls"),
    "ZAPATA":     LayerSpec("ZAPATA",     7,  "CONTINUOUS", 50, "Footings"),
}


# Linetypes that must exist in the DXF (ezdxf loads them from standard table)
REQUIRED_LINETYPES = ["CONTINUOUS", "CENTER", "DASHED", "HIDDEN", "DASHDOT"]


def apply_layers(doc, layers: dict[str, LayerSpec] | None = None) -> None:
    """
    Register all layers and required linetypes in an ezdxf Drawing.

    Parameters
    ----------
    doc : ezdxf.Drawing
    layers : dict mapping name -> LayerSpec. Defaults to STANDARD_LAYERS.
    """
    if not HAS_EZDXF or doc is None:
        return
    layers = layers or STANDARD_LAYERS

    # Ensure linetypes
    lt_table = doc.linetypes
    for lt in REQUIRED_LINETYPES:
        if lt not in lt_table:
            try:
                # ezdxf bundles standard linetype patterns
                from ezdxf.tools.standards import linetypes as _std_lts
                for name, desc, pattern in _std_lts():
                    if name == lt and lt not in lt_table:
                        lt_table.add(name=name, pattern=pattern, description=desc)
                        break
            except Exception:
                pass

    # Register layers
    table = doc.layers
    for spec in layers.values():
        if spec.name in table:
            layer = table.get(spec.name)
        else:
            layer = table.add(name=spec.name)
        try:
            layer.color = spec.color
            layer.dxf.linetype = spec.linetype if spec.linetype in lt_table else "CONTINUOUS"
            layer.dxf.lineweight = spec.lineweight
            if spec.description:
                layer.description = spec.description
        except Exception:
            pass


def color_of(layer_name: str) -> int:
    """Return ACI color for a registered layer, or 7 if unknown."""
    spec = STANDARD_LAYERS.get(layer_name)
    return spec.color if spec else 7


def list_layers() -> list[str]:
    """Return the registered layer names."""
    return list(STANDARD_LAYERS.keys())
