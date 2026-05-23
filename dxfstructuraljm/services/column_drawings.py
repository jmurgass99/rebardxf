"""Servicios para dibujos DXF de columnas.

Provee dataclasses de entrada validados y funciones puras que generan
el archivo DXF y devuelven metadata para el cliente REST/CLI.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..column_section import ColumnDetail
from ..column_rebar_detail import (
    ColumnRebarBar, ColumnRebarDetail, render_column_rebar_detail,
)
from ..exceptions import ConfigurationError, GeometryError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Seccion de columna
# ---------------------------------------------------------------------------
@dataclass
class ColumnSectionInput:
    """Entrada para :func:`draw_column_section`."""
    label: str = "C-1"
    b_mm: float = 500.0
    h_mm: float = 500.0
    cover_mm: float = 40.0
    bars: list[tuple[float, int]] = field(default_factory=lambda: [(25.0, 8)])
    db_stirrup_mm: float = 10.0
    fc_MPa: float = 28.0
    Fy_MPa: float = 420.0

    def validate(self) -> None:
        """Valida la consistencia geometrica/material."""
        if self.b_mm <= 0 or self.h_mm <= 0:
            raise GeometryError("b_mm y h_mm deben ser positivos")
        if self.cover_mm < 0 or self.cover_mm >= min(self.b_mm, self.h_mm) / 2:
            raise GeometryError("cover_mm fuera de rango")
        if not self.bars:
            raise ConfigurationError("Debe especificar al menos un grupo de barras")
        for db, n in self.bars:
            if db <= 0 or n <= 0:
                raise ConfigurationError(f"Barra invalida: db={db}, n={n}")
        if self.fc_MPa <= 0 or self.Fy_MPa <= 0:
            raise ConfigurationError("fc_MPa y Fy_MPa deben ser positivos")


def draw_column_section(inp: ColumnSectionInput, output_path: str | Path) -> dict[str, Any]:
    """Genera un DXF de seccion de columna y retorna metadata."""
    inp.validate()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generando seccion de columna %s en %s", inp.label, output_path)

    col = ColumnDetail(
        b=inp.b_mm, h=inp.h_mm, cover=inp.cover_mm,
        bars=inp.bars, db_stirrup=inp.db_stirrup_mm,
        fc=inp.fc_MPa, Fy=inp.Fy_MPa, label=inp.label,
    )
    doc = col.draw(str(output_path))
    ent = doc.n_entities()
    return {
        "path": str(output_path.resolve()),
        "label": inp.label,
        "n_entities": ent,
        "n_total_entities": sum(ent.values()),
        "summary": col.summary(),
    }


# ---------------------------------------------------------------------------
# Despiece de armadura de columna (rebar detail)
# ---------------------------------------------------------------------------
@dataclass
class _BarSpec:
    mark: str
    diameter_mm: float
    length_m: float
    quantity: int
    shape: str = "L1"


@dataclass
class ColumnRebarInput:
    """Entrada para :func:`draw_column_rebar`."""
    name: str = "C-1"
    b_mm: float = 500.0
    h_mm: float = 500.0
    H_mm: float = 3000.0
    cover_mm: float = 40.0
    longitudinal: list[_BarSpec] = field(default_factory=list)
    stirrups: list[_BarSpec] = field(default_factory=list)
    project: str = ""
    drawn_by: str = ""

    def validate(self) -> None:
        if self.b_mm <= 0 or self.h_mm <= 0 or self.H_mm <= 0:
            raise GeometryError("Dimensiones b/h/H deben ser positivas")
        if not self.longitudinal:
            raise ConfigurationError("Debe especificar barras longitudinales")


def _to_bar(s: _BarSpec) -> ColumnRebarBar:
    return ColumnRebarBar(
        mark=s.mark, diameter_mm=s.diameter_mm,
        length_m=s.length_m, quantity=s.quantity, shape=s.shape,
    )


def draw_column_rebar(inp: ColumnRebarInput, output_path: str | Path) -> dict[str, Any]:
    """Genera el plano de despiece de armadura de una columna."""
    inp.validate()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generando despiece de armadura columna %s", inp.name)

    detail = ColumnRebarDetail(
        name=inp.name, b_mm=inp.b_mm, h_mm=inp.h_mm, H_mm=inp.H_mm,
        cover_mm=inp.cover_mm,
        longitudinal=[_to_bar(s) for s in inp.longitudinal],
        stirrups=[_to_bar(s) for s in inp.stirrups],
        project=inp.project, drawn_by=inp.drawn_by,
    )
    result_path = render_column_rebar_detail(detail, output_path)
    total_kg = sum(b.weight_kg for b in detail.longitudinal) + \
        sum(b.weight_kg for b in detail.stirrups)
    return {
        "path": str(Path(result_path).resolve()),
        "name": inp.name,
        "total_kg": round(total_kg, 2),
        "n_longitudinal": len(detail.longitudinal),
        "n_stirrups": len(detail.stirrups),
    }
