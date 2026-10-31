"""
column_section.py — RC column cross-section DXF detail.

Generates: section outline + stirrup + longitudinal bars + cover dimensions.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from .core import DXFDocument, Layer


@dataclass
class ColumnDetail:
    """
    Rectangular RC column cross-section detail.

    Parameters
    ----------
    b : float  column width [mm]
    h : float  column height [mm]
    cover : float  clear cover [mm] (to stirrup face)
    bars : list[tuple[float, int]]
        List of (diameter [mm], count) tuples.
        e.g. [(25, 8)] = 8Ø25 bars
    db_stirrup : float  stirrup diameter [mm]
    Fy : float  steel yield strength [MPa]
    fc : float  concrete compressive strength [MPa]
    label : str  element label (e.g. "C-1")
    scale : float  drawing scale (default 1:20 → scale=20)

    Examples
    --------
    >>> col = ColumnDetail(b=500, h=500, cover=40,
    ...                    bars=[(25, 8)], db_stirrup=10,
    ...                    label="C-1")
    >>> col.draw("column_C1.dxf")
    """
    b: float
    h: float
    cover: float = 40.0
    bars: list[tuple[float, int]] = field(default_factory=lambda: [(20.0, 4)])
    db_stirrup: float = 10.0
    Fy: float = 420.0
    fc: float = 28.0
    label: str = "COL-1"
    scale: float = 20.0

    def __post_init__(self) -> None:
        self._total_bars = sum(count for _, count in self.bars)
        self._bar_positions = self._compute_bar_positions()

    def _compute_bar_positions(self) -> list[tuple[float, float]]:
        """
        Compute (x, y) positions of longitudinal bars relative to section origin.
        Distributes bars evenly around the perimeter.
        """
        positions = []
        # Inner rectangle of bar centroids
        d_cover = self.cover + self.db_stirrup + max(db for db, _ in self.bars) / 2
        xi = d_cover
        yi = d_cover
        wi = self.b - 2 * d_cover
        hi = self.h - 2 * d_cover

        total = self._total_bars
        if total == 0:
            return []
        if total == 4:
            # Corners only
            return [(xi, yi), (xi + wi, yi), (xi + wi, yi + hi), (xi, yi + hi)]

        # Distribute around perimeter
        n_per_side_b = max(2, round(self.b / (self.h + self.b) * total / 2))
        n_per_side_h = max(2, (total - 2 * (n_per_side_b - 2) * 2) // 2)

        pts = []
        # Bottom
        for i in range(n_per_side_b):
            pts.append((xi + i * wi / (n_per_side_b - 1), yi))
        # Right
        for i in range(1, n_per_side_h - 1):
            pts.append((xi + wi, yi + i * hi / (n_per_side_h - 1)))
        # Top (reverse)
        for i in range(n_per_side_b - 1, -1, -1):
            pts.append((xi + i * wi / (n_per_side_b - 1), yi + hi))
        # Left (reverse)
        for i in range(n_per_side_h - 2, 0, -1):
            pts.append((xi, yi + i * hi / (n_per_side_h - 1)))

        # Trim or pad to total
        while len(pts) < total:
            pts.append(pts[-1])
        return pts[:total]

    def bar_diameter(self) -> float:
        """Largest bar diameter [mm]."""
        return max(db for db, _ in self.bars)

    def as_total(self) -> float:
        """Total steel area As [mm²]."""
        return sum(math.pi * db**2 / 4 * n for db, n in self.bars)

    def rho(self) -> float:
        """Steel ratio ρ = As / Ag."""
        return self.as_total() / (self.b * self.h)

    def draw(self, output_path: str | None = None) -> DXFDocument:
        """
        Generate DXF drawing of the column section.

        Parameters
        ----------
        output_path : str | None  if None, uses '{label}.dxf'

        Returns
        -------
        DXFDocument object (saved if output_path given)
        """
        if output_path is None:
            output_path = f"{self.label}.dxf"

        doc = DXFDocument(output_path)

        # Section outline
        doc.rectangle(0, 0, self.b, self.h, layer=Layer.CONCRETE, lineweight=0.50)

        # Concrete hatch
        doc.hatch_concrete([
            (0, 0), (self.b, 0), (self.b, self.h), (0, self.h)
        ])

        # Stirrup
        doc.draw_stirrup(0, 0, self.b, self.h, self.cover, self.db_stirrup)

        # Longitudinal bars
        db_main = self.bar_diameter()
        for x, y in self._bar_positions:
            doc.draw_rebar_circle(x, y, db_main, layer=Layer.REBAR)

        # Labels
        doc.text((self.b / 2 - 20, -15), self.label, height=5, layer=Layer.TEXT)
        doc.text((self.b / 2 - 30, -22),
                 f"{self._total_bars}Ø{int(db_main)}  ρ={self.rho()*100:.2f}%",
                 height=4, layer=Layer.TEXT)
        doc.text((self.b / 2 - 25, -29),
                 f"fc={self.fc} MPa  fy={self.Fy} MPa",
                 height=3.5, layer=Layer.TEXT)

        # Cover dimension line
        doc.dimension_linear((0, 0), (self.cover, 0), dim_line_offset=-10)

        if output_path:
            doc.save()

        return doc

    def summary(self) -> dict:
        """Return design summary dict."""
        return {
            "label": self.label,
            "b_mm": self.b,
            "h_mm": self.h,
            "cover_mm": self.cover,
            "bars": self.bars,
            "n_bars": self._total_bars,
            "db_main_mm": self.bar_diameter(),
            "db_stirrup_mm": self.db_stirrup,
            "As_mm2": round(self.as_total(), 1),
            "rho_pct": round(self.rho() * 100, 3),
            "Ag_mm2": self.b * self.h,
            "fc_MPa": self.fc,
            "Fy_MPa": self.Fy,
        }
