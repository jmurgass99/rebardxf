"""
DXFStructuralJm — Automatic Structural DXF Drawing Generator
=============================================================
Generates DXF plans from FastSAP / FoundationDesignJm design results.

Usage
-----
>>> from dxfstructuraljm import ColumnDetail, BeamDetail, FoundationPlan
>>> col = ColumnDetail(b=500, h=500, bars=[(25, 8)], cover=40)
>>> col.draw("column_C1.dxf")
"""
from .core import DXFDocument, Layer
from .column_section import ColumnDetail
from .beam_section import BeamDetail
from .foundation_plan import FoundationPlan, FootingData
from .rebar_schedule import RebarSchedule, RebarEntry
from .wall_detail import WallDetail
from .templates import SheetTemplate, TitleBlockInfo, A3, A1
from .scales import Scale, auto_scale, S_1_25, S_1_50, S_1_100
from .layers import STANDARD_LAYERS, LayerSpec, apply_layers
from . import rebar_shapes
from .export import save_dxf, verify, clean
from .column_rebar_detail import (
    ColumnRebarBar, ColumnRebarDetail, render_column_rebar_detail,
)
from .footing_rebar_detail import (
    FootingRebarDetail, render_footing_rebar_detail,
)
from .frame_elevation import FrameElevationDetail
from .exceptions import (
    DXFError, ConfigurationError, GeometryError, TemplateError, DependencyError,
)

from .column_schedule_grid import (
    ColumnStorySpec, ColumnScheduleStats, ColumnScheduleDrawer,
)

__all__ = [
    "DXFError", "ConfigurationError", "GeometryError",
    "TemplateError", "DependencyError",
    "DXFDocument", "Layer",
    "ColumnDetail", "BeamDetail",
    "FrameElevationDetail",
    "FoundationPlan", "FootingData",
    "RebarSchedule", "RebarEntry",
    "WallDetail",
    "SheetTemplate", "TitleBlockInfo", "A3", "A1",
    "Scale", "auto_scale", "S_1_25", "S_1_50", "S_1_100",
    "STANDARD_LAYERS", "LayerSpec", "apply_layers",
    "rebar_shapes",
    "save_dxf", "verify", "clean",
    "ColumnRebarBar", "ColumnRebarDetail", "render_column_rebar_detail",
    "FootingRebarDetail", "render_footing_rebar_detail",
    "ColumnStorySpec", "ColumnScheduleStats", "ColumnScheduleDrawer",
]
__version__ = "1.1.0"

