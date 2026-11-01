"""
beam_section.py — RC beam cross-section and elevation DXF detail.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from .core import DXFDocument, Layer


@dataclass
class BeamDetail:
    """
    RC beam detail: cross-section + simplified elevation with stirrup spacing.
    """
    b: float
    h: float
    cover: float = 30.0
    bars_top: list[tuple[float, int]] = field(default_factory=lambda: [(20.0, 2)])
    bars_bot: list[tuple[float, int]] = field(default_factory=lambda: [(20.0, 3)])
    db_stirrup: float = 8.0
    s_critical: float = 100.0    # mm
    s_central: float  = 200.0    # mm
    span: float = 5000.0          # mm (for elevation)
    lc_critical: float = 500.0    # mm (critical zone length at each end)
    label: str = "V-1"
    fc: float = 28.0
    Fy: float = 420.0

    def as_top(self) -> float:
        return sum(math.pi * db**2 / 4 * n for db, n in self.bars_top)

    def as_bot(self) -> float:
        return sum(math.pi * db**2 / 4 * n for db, n in self.bars_bot)

    def _bar_x_positions(self, n: int, db_ref: float | None = None) -> list[float]:
        """Evenly spaced x positions for n bars in the section width."""
        if db_ref is None:
            db_ref = max(db for db, _ in self.bars_bot)
        d = self.cover + self.db_stirrup + db_ref / 2
        usable = self.b - 2 * d
        if n == 1:
            return [self.b / 2]
        return [d + i * usable / (n - 1) for i in range(n)]

    def draw_section(self, output_path: str | None = None,
                     x_offset: float = 0.0,
                     y_offset: float = 0.0) -> DXFDocument:
        """Generate cross-section DXF."""
        if output_path is None:
            output_path = f"{self.label}_section.dxf"

        doc = DXFDocument(output_path)
        x0, y0 = x_offset, y_offset

        # Section outline
        doc.rectangle(x0, y0, self.b, self.h, layer=Layer.CONCRETE, lineweight=0.50)
        doc.hatch_concrete([
            (x0, y0), (x0 + self.b, y0),
            (x0 + self.b, y0 + self.h), (x0, y0 + self.h)
        ])

        # Stirrup
        doc.draw_stirrup(x0, y0, self.b, self.h, self.cover, self.db_stirrup)

        # Top bars
        d_top = self.cover + self.db_stirrup
        n_top = sum(n for _, n in self.bars_top)
        db_t  = max(db for db, _ in self.bars_top)
        y_top = y0 + self.h - d_top - db_t / 2
        for x in self._bar_x_positions(n_top, db_ref=db_t):
            doc.draw_rebar_circle(x0 + x, y_top, db_t, layer=Layer.REBAR)

        # Bottom bars
        n_bot = sum(n for _, n in self.bars_bot)
        db_b  = max(db for db, _ in self.bars_bot)
        y_bot = y0 + self.cover + self.db_stirrup + db_b / 2
        for x in self._bar_x_positions(n_bot, db_ref=db_b):
            doc.draw_rebar_circle(x0 + x, y_bot, db_b, layer=Layer.REBAR)

        # Label
        doc.text((x0 + self.b / 2 - 20, y0 - 12), self.label, height=5)
        doc.text((x0, y0 - 20),
                 f"As,top={self.as_top():.0f} mm²  As,bot={self.as_bot():.0f} mm²",
                 height=3.5)

        doc.save()
        return doc

    def summary(self) -> dict:
        return {
            "label": self.label,
            "b_mm": self.b,
            "h_mm": self.h,
            "cover_mm": self.cover,
            "bars_top": self.bars_top,
            "bars_bot": self.bars_bot,
            "As_top_mm2": round(self.as_top(), 1),
            "As_bot_mm2": round(self.as_bot(), 1),
            "s_critical_mm": self.s_critical,
            "s_central_mm": self.s_central,
            "fc_MPa": self.fc,
            "Fy_MPa": self.Fy,
        }
