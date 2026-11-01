"""
core.py — Core DXF document and layer management using ezdxf.

Provides a clean API over ezdxf for structural drawing generation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import logging
import math

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Layer definitions
# ---------------------------------------------------------------------------
class Layer(str, Enum):
    CONCRETE   = "CONCRETO"
    REBAR      = "ARMADURA"
    STIRRUP    = "ESTRIBO"
    DIMENSION  = "COTAS"
    TEXT       = "TEXTO"
    HATCH      = "RELLENO"
    AXIS       = "EJES"
    TITLE_BLOCK = "CAJETIN"


# Layer colors (AutoCAD color index)
LAYER_COLORS = {
    Layer.CONCRETE:    7,   # white/black
    Layer.REBAR:       2,   # yellow
    Layer.STIRRUP:     3,   # green
    Layer.DIMENSION:   4,   # cyan
    Layer.TEXT:        7,
    Layer.HATCH:       8,   # gray
    Layer.AXIS:        1,   # red
    Layer.TITLE_BLOCK: 7,
}


class DXFDocument:
    """
    Wrapper around ezdxf for structural DXF generation.

    Parameters
    ----------
    filename : str  output DXF file path
    units : str  'mm' or 'm' (drawing units, default 'mm')
    """

    def __init__(self, filename: str, units: str = "mm"):
        self.filename = filename
        self.units = units
        self._lines: list[dict] = []    # fallback if no ezdxf
        self._circles: list[dict] = []
        self._texts: list[dict] = []
        self._rects: list[dict] = []

        if HAS_EZDXF:
            self._doc = ezdxf.new(dxfversion="R2018")
            self._msp = self._doc.modelspace()
            self._setup_layers()
        else:
            self._doc = None
            self._msp = None

    def _setup_layers(self) -> None:
        """Create standard structural layers."""
        if not HAS_EZDXF:
            return
        lt = self._doc.layers
        for layer, color in LAYER_COLORS.items():
            if layer.value not in lt:
                lt.add(name=layer.value, color=color)

    # ------------------------------------------------------------------
    # Drawing primitives
    # ------------------------------------------------------------------
    def line(self, start: tuple, end: tuple,
             layer: Layer = Layer.CONCRETE,
             lineweight: float = 0.25) -> None:
        """Draw a line segment."""
        if HAS_EZDXF:
            self._msp.add_line(
                start=(start[0], start[1], 0),
                end=(end[0],   end[1],   0),
                dxfattribs={"layer": layer.value, "lineweight": int(lineweight * 100)}
            )
        self._lines.append({"start": start, "end": end, "layer": layer.value})

    def circle(self, center: tuple, radius: float,
               layer: Layer = Layer.REBAR) -> None:
        """Draw a filled circle (rebar bar cross-section)."""
        if HAS_EZDXF:
            self._msp.add_circle(
                center=(center[0], center[1], 0),
                radius=radius,
                dxfattribs={"layer": layer.value}
            )
        self._circles.append({"center": center, "radius": radius})

    def rectangle(self, x: float, y: float,
                  width: float, height: float,
                  layer: Layer = Layer.CONCRETE,
                  lineweight: float = 0.50) -> None:
        """Draw a rectangle from bottom-left corner."""
        pts = [(x, y), (x + width, y), (x + width, y + height), (x, y + height)]
        for i in range(4):
            self.line(pts[i], pts[(i + 1) % 4], layer=layer, lineweight=lineweight)
        self._rects.append({"x": x, "y": y, "w": width, "h": height})

    def text(self, position: tuple, content: str, height: float = 2.5,
             layer: Layer = Layer.TEXT) -> None:
        """Add a single-line text entity."""
        if HAS_EZDXF:
            self._msp.add_text(
                content,
                dxfattribs={
                    "layer": layer.value,
                    "height": height,
                    "insert": (position[0], position[1]),
                }
            )
        self._texts.append({"pos": position, "text": content})

    def dimension_linear(self, p1: tuple, p2: tuple,
                          dim_line_offset: float = 5.0,
                          layer: Layer = Layer.DIMENSION) -> None:
        """Add a linear dimension between two points."""
        if HAS_EZDXF:
            try:
                dim = self._msp.add_linear_dim(
                    base=(p1[0], p2[1] + dim_line_offset),
                    p1=p1, p2=p2,
                    dimstyle="EZDXF",
                    dxfattribs={"layer": layer.value}
                )
                dim.render()
            except Exception as exc:
                logger.warning("dimension_linear fallback to line (%s -> %s): %s", p1, p2, exc)
                self._msp.add_line(
                    start=(p1[0], p1[1] + dim_line_offset, 0),
                    end=(p2[0], p2[1] + dim_line_offset, 0),
                    dxfattribs={"layer": layer.value},
                )

    def hatch_concrete(self, boundary_pts: list[tuple]) -> None:
        """Add concrete hatch (cross-hatch) inside boundary polygon."""
        if not HAS_EZDXF:
            return
        try:
            hatch = self._msp.add_hatch(color=8, dxfattribs={"layer": Layer.HATCH.value})
            hatch.set_pattern_fill("ANSI31", scale=5.0, angle=45)
            hatch.paths.add_polyline_path(
                [(p[0], p[1]) for p in boundary_pts], is_closed=True
            )
        except Exception as exc:
            logger.warning("hatch_concrete skipped for %d points: %s", len(boundary_pts), exc)

    def save(self) -> str:
        """Save the DXF document and return filename."""
        if HAS_EZDXF and self._doc:
            self._doc.saveas(self.filename)
        return self.filename

    # ------------------------------------------------------------------
    # Structural shortcuts
    # ------------------------------------------------------------------
    def draw_rebar_circle(self, cx: float, cy: float, db: float,
                           layer: Layer = Layer.REBAR) -> None:
        """Draw rebar bar cross-section (solid circle approximated by circle)."""
        self.circle((cx, cy), db / 2, layer=layer)

    def draw_stirrup(self, x: float, y: float,
                      width: float, height: float,
                      cover: float, db_stirrup: float) -> None:
        """Draw stirrup outline inside a section at given cover."""
        x0 = x + cover
        y0 = y + cover
        w0 = width  - 2 * cover
        h0 = height - 2 * cover
        self.rectangle(x0, y0, w0, h0, layer=Layer.STIRRUP, lineweight=0.18)

    def n_entities(self) -> dict:
        """Return count of all drawn entities (for testing)."""
        return {
            "lines": len(self._lines),
            "circles": len(self._circles),
            "texts": len(self._texts),
            "rects": len(self._rects),
        }
