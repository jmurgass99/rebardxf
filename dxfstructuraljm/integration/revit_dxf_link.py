"""
Genera DXF compatible con Revit "Link CAD".

Buenas prácticas (https://help.autodesk.com/view/RVT/2024 — Importing CAD):
    - Solo entidades 2D (LINE, LWPOLYLINE, CIRCLE, ARC, TEXT). NO 3DSOLID.
    - Unidades MM (INSUNITS = 4).
    - Layers en colores AIA estándar (índices ACI).
    - SHX fonts (no TrueType) → STYLE con `font` no `bigfont` apuntando a un .shx.
    - Sin XREFs externos (los binding pierden info).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import ezdxf
from ezdxf.document import Drawing


# Colores AIA (NCS) básicos para disciplinas estructurales
AIA_COLORS: dict[str, int] = {
    "S-COLU": 1,    # rojo
    "S-BEAM": 2,    # amarillo
    "S-SLAB": 3,    # verde
    "S-FNDN": 4,    # cian
    "S-WALL": 5,    # azul
    "S-DIMS": 7,    # blanco/negro
    "S-TEXT": 7,
    "S-ANNO": 6,    # magenta
}

# Entidades NO permitidas (rompen el Link CAD)
_FORBIDDEN_TYPES = {"3DSOLID", "BODY", "REGION", "MESH", "SURFACE"}


@dataclass
class DXFEntity:
    """
    Representación neutra de una entidad 2D.

    `type`: LINE | LWPOLYLINE | CIRCLE | ARC | TEXT
    `data`: parámetros específicos (ver constructores).
    `layer`: nombre AIA, ej. "S-COLU-CONC".
    """
    type: str
    data: dict[str, Any]
    layer: str = "S-ANNO"


@dataclass
class RevitDXFOptions:
    units: str = "MM"
    shx_font: str = "txt.shx"
    aci_overrides: dict[str, int] = field(default_factory=dict)


# ---- API principal ----------------------------------------------------

def make_revit_compatible_dxf(
    entities: Iterable[DXFEntity],
    path: str | Path,
    options: RevitDXFOptions | None = None,
) -> Drawing:
    """
    Construye un DXF apto para `Insert → Link CAD` en Revit.
    Devuelve el Drawing por si se quiere inspeccionar.
    """
    opt = options or RevitDXFOptions()
    doc = ezdxf.new(dxfversion="R2010", setup=True)

    # Unidades
    if opt.units.upper() == "MM":
        doc.header["$INSUNITS"] = 4
    elif opt.units.upper() == "M":
        doc.header["$INSUNITS"] = 6
    else:
        raise ValueError(f"Unidades '{opt.units}' no soportadas (use MM o M).")

    # STYLE con SHX
    if "REVIT_STD" in doc.styles:
        doc.styles.remove("REVIT_STD")
    doc.styles.add("REVIT_STD", font=opt.shx_font)

    msp = doc.modelspace()
    aci_map = {**AIA_COLORS, **opt.aci_overrides}

    for ent in entities:
        if ent.type.upper() in _FORBIDDEN_TYPES:
            raise ValueError(
                f"Entidad '{ent.type}' no compatible con Revit Link CAD."
            )
        _ensure_layer(doc, ent.layer, aci_map)
        _add_entity(msp, ent)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(out)
    return doc


# ---- helpers ----------------------------------------------------------

def _ensure_layer(doc: Drawing, name: str, aci_map: dict[str, int]) -> None:
    if name in doc.layers:
        return
    # Busca prefijo AIA (S-COLU-XXX → S-COLU)
    prefix = "-".join(name.split("-")[:2]) if "-" in name else name
    color = aci_map.get(prefix, aci_map.get(name, 7))
    doc.layers.add(name=name, color=color)


def _add_entity(msp: Any, ent: DXFEntity) -> None:
    t = ent.type.upper()
    d = ent.data
    attribs = {"layer": ent.layer}

    if t == "LINE":
        msp.add_line(d["start"], d["end"], dxfattribs=attribs)
    elif t == "LWPOLYLINE":
        msp.add_lwpolyline(d["points"], dxfattribs=attribs, close=d.get("close", False))
    elif t == "CIRCLE":
        msp.add_circle(d["center"], d["radius"], dxfattribs=attribs)
    elif t == "ARC":
        msp.add_arc(
            d["center"], d["radius"], d["start_angle"], d["end_angle"],
            dxfattribs=attribs,
        )
    elif t == "TEXT":
        text_attribs = {**attribs, "style": "REVIT_STD", "height": float(d.get("height", 200))}
        msp.add_text(d["text"], dxfattribs=text_attribs).set_placement(d["pos"])
    else:
        raise ValueError(f"Tipo de entidad no soportado: {ent.type}")


# ---- atajos de construcción ------------------------------------------

def line(start: Sequence[float], end: Sequence[float], layer: str = "S-ANNO") -> DXFEntity:
    return DXFEntity("LINE", {"start": tuple(start), "end": tuple(end)}, layer)


def polyline(points: Iterable[Sequence[float]], layer: str = "S-ANNO", close: bool = False) -> DXFEntity:
    return DXFEntity("LWPOLYLINE", {"points": [tuple(p) for p in points], "close": close}, layer)


def circle(center: Sequence[float], radius: float, layer: str = "S-ANNO") -> DXFEntity:
    return DXFEntity("CIRCLE", {"center": tuple(center), "radius": float(radius)}, layer)


def text(pos: Sequence[float], txt: str, height: float = 200.0, layer: str = "S-TEXT") -> DXFEntity:
    return DXFEntity("TEXT", {"pos": tuple(pos), "text": str(txt), "height": float(height)}, layer)


__all__ = [
    "AIA_COLORS",
    "DXFEntity",
    "RevitDXFOptions",
    "make_revit_compatible_dxf",
    "line",
    "polyline",
    "circle",
    "text",
]
