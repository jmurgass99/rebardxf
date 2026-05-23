"""Servicios para dibujos DXF de vigas."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..beam_section import BeamDetail
from ..exceptions import ConfigurationError, GeometryError

logger = logging.getLogger(__name__)


@dataclass
class BeamSectionInput:
    """Entrada para :func:`draw_beam_section`."""
    label: str = "V-1"
    b_mm: float = 300.0
    h_mm: float = 600.0
    cover_mm: float = 30.0
    bars_top: list[tuple[float, int]] = field(default_factory=lambda: [(20.0, 2)])
    bars_bot: list[tuple[float, int]] = field(default_factory=lambda: [(20.0, 3)])
    db_stirrup_mm: float = 8.0
    s_critical_mm: float = 100.0
    s_central_mm: float = 200.0
    span_mm: float = 5000.0
    lc_critical_mm: float = 500.0
    fc_MPa: float = 28.0
    Fy_MPa: float = 420.0

    def validate(self) -> None:
        if self.b_mm <= 0 or self.h_mm <= 0:
            raise GeometryError("b_mm y h_mm deben ser positivos")
        if self.cover_mm < 0 or self.cover_mm >= min(self.b_mm, self.h_mm) / 2:
            raise GeometryError("cover_mm fuera de rango")
        if not self.bars_top or not self.bars_bot:
            raise ConfigurationError("Debe especificar bars_top y bars_bot")
        if self.s_critical_mm <= 0 or self.s_central_mm <= 0:
            raise ConfigurationError("Espaciamientos de estribo deben ser positivos")


def draw_beam_section(inp: BeamSectionInput, output_path: str | Path) -> dict[str, Any]:
    """Genera DXF de seccion transversal de viga."""
    inp.validate()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generando seccion de viga %s en %s", inp.label, output_path)

    beam = BeamDetail(
        b=inp.b_mm, h=inp.h_mm, cover=inp.cover_mm,
        bars_top=inp.bars_top, bars_bot=inp.bars_bot,
        db_stirrup=inp.db_stirrup_mm,
        s_critical=inp.s_critical_mm, s_central=inp.s_central_mm,
        span=inp.span_mm, lc_critical=inp.lc_critical_mm,
        label=inp.label, fc=inp.fc_MPa, Fy=inp.Fy_MPa,
    )
    doc = beam.draw_section(str(output_path))
    ent = doc.n_entities()
    return {
        "path": str(output_path.resolve()),
        "label": inp.label,
        "n_entities": ent,
        "n_total_entities": sum(ent.values()),
        "summary": beam.summary(),
    }
