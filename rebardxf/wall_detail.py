"""
wall_detail.py — Structural wall cross-section detail.

Draws a horizontal section through a structural wall with:
- Concrete outline and hatch.
- Boundary elements (confined zones) at each end with longitudinal bars
  and a closed stirrup.
- Distributed horizontal and vertical web reinforcement (two curtains).
- Minimum reinforcement ratios per ACI 318 §11.6 / Eurocode 8 §5.4.3.

Inputs are nominal — designer must verify against governing code.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from .core import DXFDocument, Layer


# Code minima
RHO_MIN_HORIZONTAL = 0.0025   # ACI 318 §11.6.2
RHO_MIN_VERTICAL   = 0.0025
RHO_BE_MIN         = 0.01     # boundary element longitudinal


@dataclass
class WallDetail:
    """
    Horizontal section of a structural wall.

    Parameters
    ----------
    Lw : float  total wall length [mm]
    tw : float  wall thickness    [mm]
    Lbe : float  length of each boundary element [mm]
    n_bars_be : int  longitudinal bars per boundary element
    db_be : float  diameter of boundary longitudinal bars [mm]
    db_web_v : float  web vertical bar diameter [mm]
    db_web_h : float  web horizontal bar diameter [mm]
    s_web_v : float  vertical bar spacing [mm]
    s_web_h : float  horizontal bar spacing [mm]
    db_stirrup : float  boundary element stirrup diameter
    cover : float
    label : str
    fc, Fy : float  material strengths [MPa]
    """
    Lw: float = 4000.0
    tw: float = 250.0
    Lbe: float = 600.0
    n_bars_be: int = 8
    db_be: float = 20.0
    db_web_v: float = 12.0
    db_web_h: float = 12.0
    s_web_v: float = 200.0
    s_web_h: float = 200.0
    db_stirrup: float = 10.0
    cover: float = 30.0
    label: str = "M-1"
    fc: float = 28.0
    Fy: float = 420.0

    # ------------------------------------------------------------------
    # Reinforcement ratios
    # ------------------------------------------------------------------
    def rho_web_v(self) -> float:
        """Vertical web reinforcement ratio (two curtains)."""
        a_bar = math.pi * self.db_web_v**2 / 4
        per_m = 2 * a_bar * (1000.0 / self.s_web_v)   # mm²/m
        return per_m / (self.tw * 1000.0)

    def rho_web_h(self) -> float:
        a_bar = math.pi * self.db_web_h**2 / 4
        per_m = 2 * a_bar * (1000.0 / self.s_web_h)
        return per_m / (self.tw * 1000.0)

    def rho_be(self) -> float:
        a_bars = self.n_bars_be * math.pi * self.db_be**2 / 4
        return a_bars / (self.tw * self.Lbe)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self, output_path: str | None = None) -> DXFDocument:
        out = output_path or f"{self.label}.dxf"
        doc = DXFDocument(out)

        # -------- Wall outline & hatch
        doc.rectangle(0, 0, self.Lw, self.tw,
                      layer=Layer.CONCRETE, lineweight=0.50)
        doc.hatch_concrete([(0, 0), (self.Lw, 0),
                            (self.Lw, self.tw), (0, self.tw)])

        # -------- Boundary elements (resaltado)
        be_x = [0.0, self.Lw - self.Lbe]
        for bx in be_x:
            doc.rectangle(bx, 0, self.Lbe, self.tw,
                          layer=Layer.MURO if hasattr(Layer, "MURO") else Layer.CONCRETE,
                          lineweight=0.70)

            # Closed stirrup
            doc.draw_stirrup(bx, 0, self.Lbe, self.tw,
                             self.cover, self.db_stirrup)

            # Longitudinal bars: two rows along long edges of BE
            self._draw_be_bars(doc, bx)

        # -------- Web vertical bars (two curtains => bars in section appear as dots)
        x_start = self.Lbe + self.s_web_v / 2
        x_end   = self.Lw - self.Lbe
        x = x_start
        d_curtain_top = self.tw - self.cover - self.db_stirrup - self.db_web_v / 2
        d_curtain_bot = self.cover + self.db_stirrup + self.db_web_v / 2
        while x < x_end:
            doc.draw_rebar_circle(x, d_curtain_top, self.db_web_v, layer=Layer.REBAR)
            doc.draw_rebar_circle(x, d_curtain_bot, self.db_web_v, layer=Layer.REBAR)
            x += self.s_web_v

        # Horizontal web bars (continuous through section => long lines)
        for y in (d_curtain_bot, d_curtain_top):
            doc.line((self.Lbe, y), (self.Lw - self.Lbe, y),
                     layer=Layer.REBAR, lineweight=0.15)

        # -------- Annotations
        rv = self.rho_web_v() * 100
        rh = self.rho_web_h() * 100
        rbe = self.rho_be() * 100
        doc.text((self.Lw / 2 - 80, -25), self.label, height=15)
        doc.text((0, -45),
                 f"tw={self.tw:.0f}  Lw={self.Lw:.0f}  Lbe={self.Lbe:.0f} mm",
                 height=8)
        doc.text((0, -60),
                 f"rho_be={rbe:.2f}%  rho_v={rv:.2f}%  rho_h={rh:.2f}% "
                 f"(min {RHO_MIN_VERTICAL*100:.2f}%)",
                 height=8)
        doc.text((0, -75),
                 f"Web: Ø{int(self.db_web_v)}@{int(self.s_web_v)} V  "
                 f"Ø{int(self.db_web_h)}@{int(self.s_web_h)} H",
                 height=8)

        # Dimensions
        doc.dimension_linear((0, 0), (self.Lw, 0), dim_line_offset=-15)
        doc.dimension_linear((0, 0), (0, self.tw), dim_line_offset=-15)

        doc.save()
        return doc

    def _draw_be_bars(self, doc: DXFDocument, bx: float) -> None:
        """Distribute n_bars_be evenly around the BE rectangle perimeter."""
        n = self.n_bars_be
        if n < 4:
            return
        d = self.cover + self.db_stirrup + self.db_be / 2
        x0 = bx + d
        y0 = d
        w  = self.Lbe - 2 * d
        h  = self.tw  - 2 * d

        # Distribute along long sides (Lbe) — n/2 per side, then corners shared
        n_per_long = max(2, n // 2)
        for i in range(n_per_long):
            x = x0 + i * w / (n_per_long - 1)
            doc.draw_rebar_circle(x, y0, self.db_be, layer=Layer.REBAR)
            doc.draw_rebar_circle(x, y0 + h, self.db_be, layer=Layer.REBAR)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def summary(self) -> dict:
        return {
            "label": self.label,
            "Lw_mm": self.Lw,
            "tw_mm": self.tw,
            "Lbe_mm": self.Lbe,
            "n_bars_be": self.n_bars_be,
            "db_be_mm": self.db_be,
            "rho_be_pct":  round(self.rho_be() * 100, 3),
            "rho_v_pct":   round(self.rho_web_v() * 100, 3),
            "rho_h_pct":   round(self.rho_web_h() * 100, 3),
            "rho_min_pct": RHO_MIN_VERTICAL * 100,
            "check_v":  self.rho_web_v() >= RHO_MIN_VERTICAL,
            "check_h":  self.rho_web_h() >= RHO_MIN_HORIZONTAL,
            "check_be": self.rho_be() >= RHO_BE_MIN,
            "fc_MPa": self.fc,
            "Fy_MPa": self.Fy,
        }
