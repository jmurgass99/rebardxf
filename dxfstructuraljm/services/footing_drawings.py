"""Servicios para dibujos DXF de zapatas y planos de fundacion."""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from ..foundation_plan import FoundationPlan, FootingData
from ..footing_rebar_detail import FootingRebarDetail, render_footing_rebar_detail
from ..column_rebar_detail import ColumnRebarBar
from ..exceptions import ConfigurationError, GeometryError

logger = logging.getLogger(__name__)


@dataclass
class FootingPlanInput:
    """Entrada para :func:`draw_footing_plan`."""
    footings: list[dict]  # cada dict: label,x,y,B,L,d,As_x,As_y,db?
    column_size_mm: float = 400.0
    draw_rebar: bool = True

    def validate(self) -> None:
        if not self.footings:
            raise ConfigurationError("Debe haber al menos una zapata")
        for f in self.footings:
            for k in ("label", "x", "y", "B", "L", "d"):
                if k not in f:
                    raise ConfigurationError(f"Zapata sin campo obligatorio '{k}'")
            if f["B"] <= 0 or f["L"] <= 0 or f["d"] <= 0:
                raise GeometryError(
                    f"Dimensiones invalidas en {f.get('label', '?')}"
                )


def draw_footing_plan(inp: FootingPlanInput, output_path: str | Path) -> dict[str, Any]:
    """Genera plano de fundacion con multiples zapatas."""
    inp.validate()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generando plano de fundacion (%d zapatas)", len(inp.footings))

    footings = [
        FootingData(
            label=f["label"], x=f["x"], y=f["y"],
            B=f["B"], L=f["L"], d=f["d"],
            As_x=f.get("As_x"), As_y=f.get("As_y"),
            db=f.get("db"),
            fc=f.get("fc"), Fy=f.get("Fy"),
            design_code=f.get("design_code", "ACI318-19"),
            cover_mm=f.get("cover_mm", 75.0),
            d_agg_mm=f.get("d_agg_mm"),
            s_max_override_mm=f.get("s_max_override_mm"),
            s_min_override_mm=f.get("s_min_override_mm"),
            s_commercial_step_mm=f.get("s_commercial_step_mm", 25.0),
        )
        for f in inp.footings
    ]
    plan = FoundationPlan(
        footings=footings, column_size=inp.column_size_mm,
        draw_rebar=inp.draw_rebar,
    )
    doc = plan.draw(str(output_path))
    ent = doc.n_entities()
    return {
        "path": str(output_path.resolve()),
        "n_footings": len(footings),
        "n_entities": ent,
        "n_total_entities": sum(ent.values()),
        "schedule": plan.schedule_table(),
    }


# ---------------------------------------------------------------------------
# Despiece de zapata
# ---------------------------------------------------------------------------
@dataclass
class _RebarSpec:
    mark: str
    diameter_mm: float
    length_m: float
    quantity: int
    shape: str = "L1"


@dataclass
class FootingRebarInput:
    """Entrada para :func:`draw_footing_rebar`."""
    name: str = "Z-1"
    Lx_mm: float = 2000.0
    Ly_mm: float = 2000.0
    h_mm: float = 500.0
    cover_mm: float = 50.0
    bottom_x: Optional[_RebarSpec] = None
    bottom_y: Optional[_RebarSpec] = None
    top_x: Optional[_RebarSpec] = None
    top_y: Optional[_RebarSpec] = None
    column_b_mm: float = 400.0
    column_h_mm: float = 400.0
    project: str = ""

    def validate(self) -> None:
        if self.Lx_mm <= 0 or self.Ly_mm <= 0 or self.h_mm <= 0:
            raise GeometryError("Dimensiones de zapata deben ser positivas")
        if not any([self.bottom_x, self.bottom_y, self.top_x, self.top_y]):
            raise ConfigurationError("Debe especificar al menos una posicion de armadura")


def _to_bar(s: _RebarSpec | None) -> ColumnRebarBar | None:
    if s is None:
        return None
    return ColumnRebarBar(
        mark=s.mark, diameter_mm=s.diameter_mm,
        length_m=s.length_m, quantity=s.quantity, shape=s.shape,
    )


def draw_footing_rebar(inp: FootingRebarInput, output_path: str | Path) -> dict[str, Any]:
    """Genera el despiece de armadura de una zapata."""
    inp.validate()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Generando despiece de zapata %s", inp.name)

    detail = FootingRebarDetail(
        name=inp.name, Lx_mm=inp.Lx_mm, Ly_mm=inp.Ly_mm, h_mm=inp.h_mm,
        cover_mm=inp.cover_mm,
        bottom_x=_to_bar(inp.bottom_x), bottom_y=_to_bar(inp.bottom_y),
        top_x=_to_bar(inp.top_x), top_y=_to_bar(inp.top_y),
        column_b_mm=inp.column_b_mm, column_h_mm=inp.column_h_mm,
        project=inp.project,
    )
    result_path = render_footing_rebar_detail(detail, output_path)
    total_kg = 0.0
    for bar in (detail.bottom_x, detail.bottom_y, detail.top_x, detail.top_y):
        if bar is not None:
            total_kg += bar.weight_kg
    return {
        "path": str(Path(result_path).resolve()),
        "name": inp.name,
        "total_kg": round(total_kg, 2),
    }
