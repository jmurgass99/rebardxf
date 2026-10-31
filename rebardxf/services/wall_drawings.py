"""Servicios para dibujos DXF de muros estructurales."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..wall_detail import WallDetail
from ..exceptions import ConfigurationError, GeometryError

logger = logging.getLogger(__name__)


@dataclass
class WallSectionInput:
    """Entrada para :func:`draw_wall_section`."""
    label: str = "M-1"
    Lw_mm: float = 4000.0
    tw_mm: float = 250.0
    Lbe_mm: float = 600.0
    n_bars_be: int = 8
    db_be_mm: float = 20.0
    db_web_v_mm: float = 12.0
    db_web_h_mm: float = 12.0
    s_web_v_mm: float = 200.0
    s_web_h_mm: float = 200.0
    db_stirrup_mm: float = 10.0
    cover_mm: float = 30.0
    fc_MPa: float = 28.0
    Fy_MPa: float = 420.0

    def validate(self) -> None:
        if self.Lw_mm <= 0 or self.tw_mm <= 0 or self.Lbe_mm <= 0:
            raise GeometryError("Lw, tw, Lbe deben ser positivos")
        if 2 * self.Lbe_mm >= self.Lw_mm:
            raise GeometryError("Los elementos de borde no caben en el muro")
        if self.n_bars_be < 4:
            raise ConfigurationError("n_bars_be debe ser al menos 4")
        if self.s_web_v_mm <= 0 or self.s_web_h_mm <= 0:
            raise ConfigurationError("Espaciamientos web deben ser positivos")


def draw_wall_section(inp: WallSectionInput, output_path: str | Path) -> dict[str, Any]:
    """Genera DXF de seccion horizontal de muro estructural."""
    inp.validate()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generando seccion de muro %s en %s", inp.label, output_path)

    wall = WallDetail(
        Lw=inp.Lw_mm, tw=inp.tw_mm, Lbe=inp.Lbe_mm,
        n_bars_be=inp.n_bars_be, db_be=inp.db_be_mm,
        db_web_v=inp.db_web_v_mm, db_web_h=inp.db_web_h_mm,
        s_web_v=inp.s_web_v_mm, s_web_h=inp.s_web_h_mm,
        db_stirrup=inp.db_stirrup_mm, cover=inp.cover_mm,
        label=inp.label, fc=inp.fc_MPa, Fy=inp.Fy_MPa,
    )
    doc = wall.draw(str(output_path))
    ent = doc.n_entities()
    return {
        "path": str(output_path.resolve()),
        "label": inp.label,
        "n_entities": ent,
        "n_total_entities": sum(ent.values()),
        "summary": wall.summary(),
    }
