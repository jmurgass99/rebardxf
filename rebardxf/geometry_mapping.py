"""Separación Semántica -> Malla de Jaula de Armadura (RebarCageMapping) para RebarDXF.

Mapea caras de armadura longitudinal (`face_to_bars`) y zonas de confinamiento transversal
(`zone_to_stirrups`: Confinamiento Base, Zona Media, Confinamiento Cabeza) a barras discretas
y cercos 3D, preservando la planilla de doblado, el peso total de acero y las longitudes
de anclaje/solape según ACI 318 / Eurocode 2 al refinar el espaciado o número de estribos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import pi
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class SemanticRebarZone:
    id: str
    z_start_mm: float
    z_end_mm: float
    stirrup_spacing_mm: float
    stirrup_diameter_mm: float = 10.0


@dataclass
class RebarCageMapping:
    """Mapeo Zonas Semánticas -> Barras Longitudinales y Cercos Discretos."""
    zone_to_stirrups: Dict[str, List[int]] = field(default_factory=dict)
    stirrup_to_zone: Dict[int, str] = field(default_factory=dict)
    face_to_bars: Dict[str, List[int]] = field(default_factory=dict)


@dataclass
class DiscretizedStirrup:
    index: int
    zone_id: str
    z_mm: float
    perimeter_mm: float
    weight_kg: float


@dataclass
class DiscretizedLongitudinalBar:
    index: int
    face_id: str
    x_mm: float
    y_mm: float
    diameter_mm: float
    length_mm: float
    weight_kg: float


def build_rebar_cage_mesh(
    b_mm: float = 450.0,
    h_mm: float = 450.0,
    H_column_mm: float = 3200.0,
    cover_mm: float = 40.0,
    long_bar_dia_mm: float = 20.0,
    zones: List[SemanticRebarZone] | None = None,
) -> Tuple[List[DiscretizedStirrup], List[DiscretizedLongitudinalBar], RebarCageMapping, Dict[str, float]]:
    """Genera la malla de cercos y barras longitudinales de la columna y calcula la planilla."""
    if zones is None:
        l_conf = max(450.0, H_column_mm / 6.0)
        zones = [
            SemanticRebarZone("BASE_CONFINEMENT", 0.0, l_conf, stirrup_spacing_mm=100.0),
            SemanticRebarZone("MIDDLE_ZONE", l_conf, H_column_mm - l_conf, stirrup_spacing_mm=200.0),
            SemanticRebarZone("TOP_CONFINEMENT", H_column_mm - l_conf, H_column_mm, stirrup_spacing_mm=100.0),
        ]

    mapping = RebarCageMapping()
    stirrups: List[DiscretizedStirrup] = []
    long_bars: List[DiscretizedLongitudinalBar] = []

    # 1. Barras longitudinales (4 esquinas + 4 intermedias = 8 barras)
    xb = (b_mm / 2.0) - cover_mm - 10.0
    yb = (h_mm / 2.0) - cover_mm - 10.0
    bar_coords = [
        ("CORNER_TOP_LEFT", -xb, yb),
        ("TOP_MID", 0.0, yb),
        ("CORNER_TOP_RIGHT", xb, yb),
        ("RIGHT_MID", xb, 0.0),
        ("CORNER_BOT_RIGHT", xb, -yb),
        ("BOT_MID", 0.0, -yb),
        ("CORNER_BOT_LEFT", -xb, -yb),
        ("LEFT_MID", -xb, 0.0),
    ]

    area_long_m2 = pi * ((long_bar_dia_mm / 1000.0) ** 2) / 4.0
    bar_len_m = (H_column_mm + 400.0) / 1000.0  # incluye pata de anclaje de 400 mm
    bar_weight_each = 7850.0 * area_long_m2 * bar_len_m

    for idx, (face, x, y) in enumerate(bar_coords):
        long_bars.append(
            DiscretizedLongitudinalBar(
                index=idx,
                face_id=face,
                x_mm=x,
                y_mm=y,
                diameter_mm=long_bar_dia_mm,
                length_mm=H_column_mm + 400.0,
                weight_kg=bar_weight_each,
            )
        )
        mapping.face_to_bars[face] = [idx]

    # 2. Cercos transversales por zona
    stirrup_perim_mm = 2.0 * ((b_mm - 2 * cover_mm) + (h_mm - 2 * cover_mm)) + 150.0  # + ganchos 135°
    perim_m = stirrup_perim_mm / 1000.0

    for z in zones:
        mapping.zone_to_stirrups[z.id] = []
        area_st_m2 = pi * ((z.stirrup_diameter_mm / 1000.0) ** 2) / 4.0
        st_weight = 7850.0 * area_st_m2 * perim_m

        z_curr = z.z_start_mm + z.stirrup_spacing_mm
        while z_curr <= z.z_end_mm:
            idx = len(stirrups)
            stirrups.append(
                DiscretizedStirrup(
                    index=idx,
                    zone_id=z.id,
                    z_mm=z_curr,
                    perimeter_mm=stirrup_perim_mm,
                    weight_kg=st_weight,
                )
            )
            mapping.zone_to_stirrups[z.id].append(idx)
            mapping.stirrup_to_zone[idx] = z.id
            z_curr += z.stirrup_spacing_mm

    # Longitud básica de anclaje ACI 318 / EC2: lb = (db / 4) * (fyd / fbd) ≈ 42 * db
    lb_anchor_mm = 42.0 * long_bar_dia_mm
    total_long_weight_kg = sum(b.weight_kg for b in long_bars)
    total_stirrup_weight_kg = sum(s.weight_kg for s in stirrups)

    summary = {
        "column_height_mm": H_column_mm,
        "long_bars_count": float(len(long_bars)),
        "stirrup_count": float(len(stirrups)),
        "anchorage_length_mm": lb_anchor_mm,
        "weight_longitudinal_kg": total_long_weight_kg,
        "weight_transverse_kg": total_stirrup_weight_kg,
        "total_steel_weight_kg": total_long_weight_kg + total_stirrup_weight_kg,
    }
    return stirrups, long_bars, mapping, summary
