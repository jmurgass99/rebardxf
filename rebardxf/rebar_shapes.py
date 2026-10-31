"""
rebar_shapes.py — Standard rebar bending shapes.

Each constructor returns a list of (x, y) polyline vertices in model units
(millimetres) ready to be inserted with DXFDocument.line / add_lwpolyline.

Standard hook lengths follow ACI 318-19 / ACI Detailing Manual:
    - 90 deg hook  : extension = max(12 db, 150 mm)
    - 135 deg hook : extension = max(6 db, 75 mm) — typical for stirrups
    - 180 deg hook : extension = max(4 db, 65 mm)

Minimum inside bend diameter D follows ACI 318-19 §25.3 (see
``min_bend_diameter_aci``). The legacy ``bend_radius`` function is preserved
for backward compatibility; new code should pass ``bar=`` to the shape
constructors so the normative ACI table is used.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Optional, Union


# ---------------------------------------------------------------------------
# ACI 318-19 §25.3 — Bar designations and nominal diameters
# ---------------------------------------------------------------------------
# Imperial bar sizes — ASTM A615 / ACI nominal diameters [mm].
# Values are the official imperial diameters converted to millimetres:
#   #3 = 0.375 in = 9.525 mm,  #4 = 0.500 in = 12.700 mm, etc.
BAR_DIAMETERS_MM: dict[str, float] = {
    "#3":  9.525,
    "#4":  12.700,
    "#5":  15.875,
    "#6":  19.050,
    "#7":  22.225,
    "#8":  25.400,
    "#9":  28.65,    # 1.128 in
    "#10": 32.26,    # 1.270 in
    "#11": 35.81,    # 1.410 in
    "#14": 43.00,    # 1.693 in
    "#18": 57.33,    # 2.257 in
}

# Metric bar designations (ISO 6935-2 / Eurocode 2 common sizes) [mm].
BAR_DIAMETERS_METRIC_MM: dict[str, float] = {
    "M8":  8.0,
    "M10": 10.0,
    "M12": 12.0,
    "M16": 16.0,
    "M20": 20.0,
    "M25": 25.0,
    "M28": 28.0,
    "M32": 32.0,
    "M40": 40.0,
}

# Mapping of metric bar -> closest imperial equivalent for ACI table lookup.
# Selected by closest nominal diameter.
_METRIC_TO_IMPERIAL: dict[str, str] = {
    "M8":  "#3",
    "M10": "#3",
    "M12": "#4",
    "M16": "#5",
    "M20": "#6",
    "M25": "#8",
    "M28": "#9",
    "M32": "#10",
    "M40": "#11",
}


def _resolve_bar(bar: Union[str, float, int]) -> tuple[str, float]:
    """
    Return ``(imperial_designation, db_mm)`` for any accepted ``bar`` input.

    Accepts:
      * Imperial designation: ``"#5"``
      * Metric designation:   ``"M16"`` (mapped to closest imperial size)
      * Numeric db [mm]:      ``16`` or ``16.0`` (mapped by nearest imperial)
    """
    if isinstance(bar, str):
        key = bar.strip().upper()
        if key in BAR_DIAMETERS_MM:
            return key, BAR_DIAMETERS_MM[key]
        if key in BAR_DIAMETERS_METRIC_MM:
            db = BAR_DIAMETERS_METRIC_MM[key]
            imperial = _METRIC_TO_IMPERIAL[key]
            return imperial, db
        raise KeyError(f"Unknown bar designation: {bar!r}")
    # numeric db in mm — find nearest imperial size by db
    db = float(bar)
    imperial = min(BAR_DIAMETERS_MM.items(), key=lambda kv: abs(kv[1] - db))[0]
    return imperial, db


# ---------------------------------------------------------------------------
# ACI 318-19 §25.3 — Minimum inside bend diameter D
# ---------------------------------------------------------------------------
# §25.3.1 — Standard hooks for development of deformed bars in tension:
#   #3..#8  : D = 6 db
#   #9..#11 : D = 8 db
#   #14,#18 : D = 10 db
# §25.3.2 — Stirrups, ties, hoops (90° and 135° hooks):
#   #3..#5  : D = 4 db
#   #6..#8  : D = 6 db
#   (#9..#11 not standardly used as stirrups in ACI table)
# §25.3.4 — Seismic hooks (special moment frames):
#   #3..#8 stirrups/hoops : D >= 6 db
#   #9..#11 stirrups/hoops: D >= 8 db
_STD_HOOK_FACTOR = {  # §25.3.1 (90° and 180° standard hooks)
    "#3": 6, "#4": 6, "#5": 6, "#6": 6, "#7": 6, "#8": 6,
    "#9": 8, "#10": 8, "#11": 8,
    "#14": 10, "#18": 10,
}
_STIRRUP_HOOK_FACTOR = {  # §25.3.2 (stirrups 90° / 135°)
    "#3": 4, "#4": 4, "#5": 4,
    "#6": 6, "#7": 6, "#8": 6,
}
_SEISMIC_HOOK_FACTOR = {  # §25.3.4 (seismic stirrups, ties, hoops)
    "#3": 6, "#4": 6, "#5": 6, "#6": 6, "#7": 6, "#8": 6,
    "#9": 8, "#10": 8, "#11": 8,
}

_VALID_HOOK_TYPES = {
    "standard_90", "standard_180", "stirrup_90", "stirrup_135", "seismic",
}


def min_bend_diameter_aci(bar_designation: Union[str, float, int],
                          hook_type: str = "standard_90") -> float:
    """
    Minimum inside bend diameter ``D`` [mm] per ACI 318-19 §25.3.

    Parameters
    ----------
    bar_designation : str or float
        Imperial designation (``"#3"``..``"#18"``), metric designation
        (``"M10"``..``"M40"``) or numeric ``db`` in mm.
    hook_type : str
        One of ``{"standard_90", "standard_180", "stirrup_90",
        "stirrup_135", "seismic"}``.

    Returns
    -------
    float
        Minimum inside bend diameter D, in millimetres. The corresponding
        inside bend *radius* is ``D / 2``.

    Raises
    ------
    NotImplementedError
        If the requested ``(bar, hook_type)`` combination is not covered by
        the ACI table (e.g. stirrups for #14/#18 are not standardised).
    """
    if hook_type not in _VALID_HOOK_TYPES:
        raise ValueError(f"hook_type must be one of {_VALID_HOOK_TYPES}")

    imperial, db = _resolve_bar(bar_designation)

    if hook_type in ("standard_90", "standard_180"):
        factor = _STD_HOOK_FACTOR.get(imperial)
    elif hook_type in ("stirrup_90", "stirrup_135"):
        factor = _STIRRUP_HOOK_FACTOR.get(imperial)
    else:  # seismic
        factor = _SEISMIC_HOOK_FACTOR.get(imperial)

    if factor is None:
        raise NotImplementedError(
            f"ACI 318-19 §25.3 does not tabulate {hook_type!r} for bar "
            f"{imperial!r}. Consult §25.3 for special cases."
        )
    return factor * db


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
def hook_extension(db: float, angle: int = 90) -> float:
    """Free length of the straight tail after the bend [mm]."""
    if angle == 90:
        return max(12.0 * db, 150.0)
    if angle == 135:
        return max(6.0 * db, 75.0)
    if angle == 180:
        return max(4.0 * db, 65.0)
    return 12.0 * db


def bend_radius(db: float) -> float:
    """
    Legacy inside bend *radius* [mm] (linear approximation).

    Retained for backward compatibility. New code should call
    :func:`min_bend_diameter_aci` and divide by 2, or pass ``bar=`` to the
    shape constructors so the normative ACI 318-19 §25.3 table is used.
    """
    if db <= 25:
        return 3.0 * db
    if db <= 36:
        return 4.0 * db
    return 5.0 * db


def _bend_radius_for(bar: Optional[Union[str, float, int]],
                     db: float,
                     hook_type: str) -> float:
    """
    Resolve the inside bend *radius* used by shape constructors.

    If ``bar`` is provided, use the ACI 318-19 §25.3 table
    (radius = D / 2). Otherwise fall back to the legacy linear
    approximation ``bend_radius(db)``.
    """
    if bar is None:
        return bend_radius(db)
    return min_bend_diameter_aci(bar, hook_type) / 2.0


def _arc_points(cx: float, cy: float, r: float,
                a0_deg: float, a1_deg: float, n: int = 8) -> list[tuple[float, float]]:
    """Discretize an arc into n+1 points (centerline of bar)."""
    pts = []
    a0 = math.radians(a0_deg)
    a1 = math.radians(a1_deg)
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


# ---------------------------------------------------------------------------
# Standard shapes
# ---------------------------------------------------------------------------
def straight(length: float, x: float = 0.0, y: float = 0.0) -> list[tuple[float, float]]:
    """Straight bar — two endpoints."""
    return [(x, y), (x + length, y)]


def L_shape(leg1: float, leg2: float, db: float = 12.0,
            x: float = 0.0, y: float = 0.0) -> list[tuple[float, float]]:
    """L bar: leg1 horizontal, leg2 vertical (up). Bend at the corner."""
    r = bend_radius(db)
    pts = [(x, y), (x + leg1 - r, y)]
    pts += _arc_points(x + leg1 - r, y + r, r, -90, 0)
    pts.append((x + leg1, y + leg2))
    return pts


def U_shape(width: float, depth: float, db: float = 12.0,
            x: float = 0.0, y: float = 0.0) -> list[tuple[float, float]]:
    """U bar — open at top. width is mouth opening, depth is leg length."""
    r = bend_radius(db)
    pts = [(x, y + depth)]                      # top-left
    pts.append((x, y + r))
    pts += _arc_points(x + r, y + r, r, 180, 270)
    pts.append((x + width - r, y))
    pts += _arc_points(x + width - r, y + r, r, 270, 360)
    pts.append((x + width, y + depth))
    return pts


def S_shape(h1: float, offset: float, h2: float, db: float = 12.0,
            x: float = 0.0, y: float = 0.0) -> list[tuple[float, float]]:
    """S / Z offset bar: vertical h1, sloped offset, vertical h2."""
    pts = [(x, y), (x, y + h1)]
    pts.append((x + offset, y + h1 + abs(offset) * 0.5))
    pts.append((x + offset, y + h1 + abs(offset) * 0.5 + h2))
    return pts


def hook_90(leg: float, db: float = 12.0,
            x: float = 0.0, y: float = 0.0,
            bar: Optional[Union[str, float]] = None) -> list[tuple[float, float]]:
    """
    Straight bar terminated by a 90° standard hook.

    Bend radius per ACI 318-19 §25.3.1 when ``bar`` is provided (otherwise
    the legacy :func:`bend_radius` approximation is used for compatibility).
    Tail extension = max(12 db, 150 mm) per ACI 318-19 §25.3.1.
    """
    ext = hook_extension(db, 90)
    r = _bend_radius_for(bar, db, "standard_90")
    pts = [(x, y), (x + leg - r, y)]
    pts += _arc_points(x + leg - r, y + r, r, -90, 0)
    pts.append((x + leg, y + ext))
    return pts


def hook_135(leg: float, db: float = 12.0,
             x: float = 0.0, y: float = 0.0,
             bar: Optional[Union[str, float]] = None) -> list[tuple[float, float]]:
    """
    Straight bar terminated by a 135° seismic hook.

    Bend radius per ACI 318-19 §25.3.2 (stirrups) when ``bar`` is provided;
    legacy approximation otherwise. Tail = max(6 db, 75 mm) per §25.3.2.
    """
    ext = hook_extension(db, 135)
    r = _bend_radius_for(bar, db, "stirrup_135")
    pts = [(x, y), (x + leg - r, y)]
    pts += _arc_points(x + leg - r, y + r, r, -90, 45)
    # tail at 45 deg upwards
    tx = x + leg - r + r * math.cos(math.radians(45)) + ext * math.cos(math.radians(45))
    ty = y + r + r * math.sin(math.radians(45)) + ext * math.sin(math.radians(45))
    pts.append((tx, ty))
    return pts


def closed_stirrup(b: float, h: float, cover: float = 25.0,
                   db: float = 8.0,
                   x: float = 0.0, y: float = 0.0,
                   bar: Optional[Union[str, float]] = None) -> list[tuple[float, float]]:
    """
    Closed rectangular stirrup with 135° seismic hooks at the splice.

    Bend radius per ACI 318-19 §25.3.2 (stirrups/ties) when ``bar`` is
    provided; legacy approximation otherwise.
    """
    bw = b - 2 * cover - db
    hh = h - 2 * cover - db
    r = _bend_radius_for(bar, db, "stirrup_135")
    x0 = x + cover + db / 2
    y0 = y + cover + db / 2

    pts: list[tuple[float, float]] = []
    pts.append((x0 + r, y0))
    pts.append((x0 + bw - r, y0))
    pts += _arc_points(x0 + bw - r, y0 + r, r, -90, 0)
    pts.append((x0 + bw, y0 + hh - r))
    pts += _arc_points(x0 + bw - r, y0 + hh - r, r, 0, 90)
    pts.append((x0 + r, y0 + hh))
    pts += _arc_points(x0 + r, y0 + hh - r, r, 90, 180)
    pts.append((x0, y0 + r))
    pts += _arc_points(x0 + r, y0 + r, r, 180, 270)
    pts.append((x0 + r, y0))                     # close at start

    # 135 deg seismic hook tail at the corner
    ext = hook_extension(db, 135)
    hx = x0 + r + ext * math.cos(math.radians(45))
    hy = y0 + ext * math.sin(math.radians(45))
    pts.append((hx, hy))
    return pts


def open_stirrup(b: float, h: float, cover: float = 25.0,
                 db: float = 8.0,
                 x: float = 0.0, y: float = 0.0,
                 bar: Optional[Union[str, float]] = None) -> list[tuple[float, float]]:
    """
    U-shaped open stirrup (open at top) — typical for one-way slabs / beams.

    Bend radius per ACI 318-19 §25.3.2 (stirrups, 90° hook) when ``bar`` is
    provided; legacy approximation otherwise.
    """
    bw = b - 2 * cover - db
    hh = h - 2 * cover - db
    r = _bend_radius_for(bar, db, "stirrup_90")
    x0 = x + cover + db / 2
    y0 = y + cover + db / 2
    ext = hook_extension(db, 90)

    pts: list[tuple[float, float]] = []
    pts.append((x0, y0 + hh))
    pts.append((x0, y0 + r))
    pts += _arc_points(x0 + r, y0 + r, r, 180, 270)
    pts.append((x0 + bw - r, y0))
    pts += _arc_points(x0 + bw - r, y0 + r, r, 270, 360)
    pts.append((x0 + bw, y0 + hh))
    # 90 deg hook tails at the top of each leg, bent inwards
    pts.insert(0, (x0 + ext, y0 + hh))
    pts.append((x0 + bw - ext, y0 + hh))
    return pts


# ---------------------------------------------------------------------------
# DXF insertion helper
# ---------------------------------------------------------------------------
def insert_polyline(doc, points: list[tuple[float, float]],
                    layer: str = "ARMADURA",
                    lineweight: int = 18,
                    closed: bool = False) -> None:
    """
    Insert a polyline into an ezdxf modelspace through a DXFDocument-like
    wrapper. Falls back to consecutive lines if add_lwpolyline is unavailable.
    """
    if doc is None or not points:
        return
    msp = getattr(doc, "_msp", None)
    if msp is not None:
        try:
            msp.add_lwpolyline(
                [(p[0], p[1]) for p in points],
                dxfattribs={"layer": layer, "lineweight": lineweight},
                close=closed,
            )
            return
        except Exception:
            pass
    # fallback: line by line
    line = getattr(doc, "line", None)
    if line is None:
        return
    from .core import Layer
    try:
        ly = Layer(layer)
    except Exception:
        ly = Layer.REBAR
    for i in range(len(points) - 1):
        line(points[i], points[i + 1], layer=ly, lineweight=lineweight / 100)
    if closed:
        line(points[-1], points[0], layer=ly, lineweight=lineweight / 100)


@dataclass
class ShapeCatalog:
    """
    Quick dispatch table of named shapes for use in rebar_schedule output.

    Example
    -------
    >>> ShapeCatalog.get('hook90')(leg=500, db=16)
    """
    @staticmethod
    def get(name: str):
        return {
            "straight": straight,
            "L":        L_shape,
            "U":        U_shape,
            "S":        S_shape,
            "hook90":   hook_90,
            "hook135":  hook_135,
            "stirrup":  closed_stirrup,
            "open_stirrup": open_stirrup,
        }[name]
