"""Servicios para planillas (despieces) de armadura."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

from ..rebar_schedule import RebarSchedule
from ..exceptions import ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class _RebarItem:
    mark: str
    element: str
    diameter_mm: float
    count: int
    length_mm: float
    shape: str = "straight"


@dataclass
class RebarScheduleInput:
    """Entrada para :func:`build_rebar_schedule`."""
    entries: list[_RebarItem] = field(default_factory=list)

    def validate(self) -> None:
        if not self.entries:
            raise ConfigurationError("Lista de entradas vacia")
        for e in self.entries:
            if e.diameter_mm <= 0 or e.count <= 0 or e.length_mm <= 0:
                raise ConfigurationError(
                    f"Entrada invalida en marca '{e.mark}'"
                )


def build_rebar_schedule(inp: RebarScheduleInput) -> dict[str, Any]:
    """Construye la planilla y devuelve tabla + totales."""
    inp.validate()
    logger.info("Construyendo planilla de armadura con %d entradas", len(inp.entries))
    sched = RebarSchedule()
    for e in inp.entries:
        sched.add(e.mark, e.element, e.diameter_mm, e.count, e.length_mm, e.shape)
    return {
        "n_entries": len(inp.entries),
        "total_kg": sched.total_weight(),
        "table": sched.to_table(),
        "by_diameter": sched.summary_by_diameter(),
    }
