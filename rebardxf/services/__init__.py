"""Capa de servicios: funciones puras Input->DXF + metadata.

Cada servicio recibe un dataclass `Input` (validable), genera un DXF en
un path dado y retorna metadata (path, n_entities, totales, etc.) util
para clientes REST/CLI sin acoplarse a los wrappers internos.
"""
from .column_drawings import ColumnSectionInput, ColumnRebarInput, draw_column_section, draw_column_rebar
from .beam_drawings import BeamSectionInput, draw_beam_section
from .footing_drawings import FootingPlanInput, FootingRebarInput, draw_footing_plan, draw_footing_rebar
from .wall_drawings import WallSectionInput, draw_wall_section
from .schedules import RebarScheduleInput, build_rebar_schedule

__all__ = [
    "ColumnSectionInput", "ColumnRebarInput",
    "draw_column_section", "draw_column_rebar",
    "BeamSectionInput", "draw_beam_section",
    "FootingPlanInput", "FootingRebarInput",
    "draw_footing_plan", "draw_footing_rebar",
    "WallSectionInput", "draw_wall_section",
    "RebarScheduleInput", "build_rebar_schedule",
]
