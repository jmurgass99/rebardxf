"""FastAPI REST de DXFStructuralJm.

Endpoints:
- GET  /health
- POST /api/drawings/column   -> seccion de columna
- POST /api/drawings/beam     -> seccion de viga
- POST /api/drawings/footing  -> plano de fundacion
- POST /api/drawings/wall     -> seccion de muro
"""
from __future__ import annotations
import base64
import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..exceptions import DXFError, ConfigurationError, GeometryError
from ..services.column_drawings import (
    ColumnSectionInput, draw_column_section,
)
from ..services.beam_drawings import BeamSectionInput, draw_beam_section
from ..services.footing_drawings import (
    FootingPlanInput, draw_footing_plan,
)
from ..services.wall_drawings import WallSectionInput, draw_wall_section

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic schemas (espejo de dataclasses de servicios)
# ---------------------------------------------------------------------------
class ColumnSectionRequest(BaseModel):
    label: str = "C-1"
    b_mm: float = 500.0
    h_mm: float = 500.0
    cover_mm: float = 40.0
    bars: list[tuple[float, int]] = Field(default_factory=lambda: [(25.0, 8)])
    db_stirrup_mm: float = 10.0
    fc_MPa: float = 28.0
    Fy_MPa: float = 420.0


class BeamSectionRequest(BaseModel):
    label: str = "V-1"
    b_mm: float = 300.0
    h_mm: float = 600.0
    cover_mm: float = 30.0
    bars_top: list[tuple[float, int]] = Field(default_factory=lambda: [(20.0, 2)])
    bars_bot: list[tuple[float, int]] = Field(default_factory=lambda: [(20.0, 3)])
    db_stirrup_mm: float = 8.0
    s_critical_mm: float = 100.0
    s_central_mm: float = 200.0
    span_mm: float = 5000.0
    lc_critical_mm: float = 500.0
    fc_MPa: float = 28.0
    Fy_MPa: float = 420.0


class FootingPlanRequest(BaseModel):
    footings: list[dict]
    column_size_mm: float = 400.0
    draw_rebar: bool = True


class WallSectionRequest(BaseModel):
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _respond(meta: dict[str, Any], fmt: str) -> Any:
    """Empaqueta la respuesta como file o JSON con base64."""
    path = Path(meta["path"])
    if fmt == "file":
        return FileResponse(
            str(path), media_type="application/dxf",
            filename=path.name,
        )
    data = path.read_bytes()
    meta["dxf_base64"] = base64.b64encode(data).decode("ascii")
    meta["bytes"] = len(data)
    return JSONResponse(meta)


def _handle(fn, *args) -> Any:
    """Traduce excepciones tipadas a HTTPException."""
    try:
        return fn(*args)
    except (ConfigurationError, GeometryError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DXFError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Router (mountable en gateway)
# ---------------------------------------------------------------------------
router = APIRouter()


@router.get("/api/drawings/health")
def health() -> dict[str, str]:
    """Healthcheck."""
    return {"status": "ok", "service": "dxfstructuraljm"}


@router.post("/api/drawings/column")
def post_column(
    req: ColumnSectionRequest,
    format: str = Query("json", pattern="^(json|file)$"),
) -> Any:
    """Genera seccion de columna."""
    inp = ColumnSectionInput(**req.model_dump())
    tmp = Path(tempfile.mkdtemp()) / f"{req.label}.dxf"
    meta = _handle(draw_column_section, inp, tmp)
    return _respond(meta, format)


@router.post("/api/drawings/beam")
def post_beam(
    req: BeamSectionRequest,
    format: str = Query("json", pattern="^(json|file)$"),
) -> Any:
    """Genera seccion de viga."""
    inp = BeamSectionInput(**req.model_dump())
    tmp = Path(tempfile.mkdtemp()) / f"{req.label}.dxf"
    meta = _handle(draw_beam_section, inp, tmp)
    return _respond(meta, format)


@router.post("/api/drawings/footing")
def post_footing(
    req: FootingPlanRequest,
    format: str = Query("json", pattern="^(json|file)$"),
) -> Any:
    """Genera plano de fundacion."""
    inp = FootingPlanInput(**req.model_dump())
    tmp = Path(tempfile.mkdtemp()) / "foundation_plan.dxf"
    meta = _handle(draw_footing_plan, inp, tmp)
    return _respond(meta, format)


@router.post("/api/drawings/wall")
def post_wall(
    req: WallSectionRequest,
    format: str = Query("json", pattern="^(json|file)$"),
) -> Any:
    """Genera seccion de muro estructural."""
    inp = WallSectionInput(**req.model_dump())
    tmp = Path(tempfile.mkdtemp()) / f"{req.label}.dxf"
    meta = _handle(draw_wall_section, inp, tmp)
    return _respond(meta, format)


def create_router() -> APIRouter:
    """Devuelve el APIRouter (factory para uniformidad con otros repos)."""
    return router


# ---------------------------------------------------------------------------
# App standalone (preserva import `from x.api.app import app`)
# ---------------------------------------------------------------------------
app = FastAPI(
    title="DXFStructuralJm REST API",
    version="1.2.0",
    description="Generacion automatica de planos estructurales DXF.",
)
app.include_router(router)
