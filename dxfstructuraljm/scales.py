"""
scales.py — Drawing scale utilities for structural plans.

Provides:
- Standard scale presets (1:25, 1:50, 1:100, 1:200, 1:500).
- Text height scaling so that printed height in paper is preserved.
- Automatic scale selection from a drawing bounding box and target sheet.
"""
from __future__ import annotations
from dataclasses import dataclass


# Standard architectural / structural scales (drawing units : 1 paper unit)
STANDARD_SCALES = (10, 20, 25, 50, 75, 100, 200, 250, 500, 1000)


@dataclass
class Scale:
    """
    A drawing scale (e.g. 1:50 → factor=50).

    Parameters
    ----------
    factor : float  scale denominator. drawing_size = factor * paper_size.
    units  : str    'mm' or 'm' for the model.
    """
    factor: float = 50.0
    units: str = "mm"

    # ------------------------------------------------------------------
    # Paper / model conversions
    # ------------------------------------------------------------------
    def to_paper(self, model_length: float) -> float:
        """Convert a length in model units to printed paper length [mm]."""
        if self.units == "m":
            model_length *= 1000.0
        return model_length / self.factor

    def to_model(self, paper_length_mm: float) -> float:
        """Convert a length in paper [mm] to model units."""
        model = paper_length_mm * self.factor
        if self.units == "m":
            model /= 1000.0
        return model

    # ------------------------------------------------------------------
    # Annotation sizing
    # ------------------------------------------------------------------
    def text_height(self, paper_height_mm: float = 2.5) -> float:
        """
        Return text height in model units so that printed height
        matches paper_height_mm. Default is 2.5mm (standard structural).
        """
        return self.to_model(paper_height_mm)

    def dim_offset(self, paper_offset_mm: float = 7.0) -> float:
        """Dimension line offset in model units."""
        return self.to_model(paper_offset_mm)

    def arrow_size(self, paper_arrow_mm: float = 2.5) -> float:
        """Arrow/tick size in model units."""
        return self.to_model(paper_arrow_mm)

    def __str__(self) -> str:
        return f"1:{int(self.factor)}"


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------
S_1_10  = Scale(10)
S_1_20  = Scale(20)
S_1_25  = Scale(25)
S_1_50  = Scale(50)
S_1_100 = Scale(100)
S_1_200 = Scale(200)
S_1_500 = Scale(500)


# Sheet sizes (ISO 216) in mm — usable area (5mm margin)
SHEET_SIZES_MM = {
    "A4": (297, 210),
    "A3": (420, 297),
    "A2": (594, 420),
    "A1": (841, 594),
    "A0": (1189, 841),
}


def auto_scale(model_width: float,
               model_height: float,
               sheet: str = "A3",
               margin_mm: float = 30.0,
               units: str = "mm") -> Scale:
    """
    Choose the smallest standard scale that fits a model bbox on a sheet.

    Parameters
    ----------
    model_width, model_height : float  bounding box of the drawing
    sheet  : str   ISO sheet code ('A4'…'A0')
    margin_mm : float  paper margin reserved for title block / borders
    units  : str   'mm' or 'm'

    Returns
    -------
    Scale instance.
    """
    if units == "m":
        model_width *= 1000.0
        model_height *= 1000.0

    if sheet not in SHEET_SIZES_MM:
        raise ValueError(f"Unknown sheet '{sheet}'. Use one of {list(SHEET_SIZES_MM)}.")

    sw, sh = SHEET_SIZES_MM[sheet]
    avail_w = sw - 2 * margin_mm
    avail_h = sh - 2 * margin_mm
    if avail_w <= 0 or avail_h <= 0:
        raise ValueError("Margin too large for sheet.")

    needed = max(model_width / avail_w, model_height / avail_h)
    for f in STANDARD_SCALES:
        if f >= needed:
            return Scale(float(f), units=units)
    return Scale(float(STANDARD_SCALES[-1]), units=units)


def bbox_of(points: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """Axis-aligned bounding box (xmin, ymin, xmax, ymax) of point list."""
    if not points:
        return (0.0, 0.0, 0.0, 0.0)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))
