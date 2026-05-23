"""
Cuadro de aceros — lista paramétrica de refuerzos con totales por φ.

Genera la geometría (rectángulos + textos) lista para enchufarse a un DXF.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RebarItem:
    mark: str
    diameter_mm: int
    length_mm: float
    quantity: int
    shape_id: str = "1"          # shape catalog ID

    @property
    def total_length_m(self) -> float:
        return self.length_mm * self.quantity / 1000.0

    @property
    def total_weight_kg(self) -> float:
        # ρ acero = 0.00617 kg/mm·m por mm² → simplificado
        unit_kg_per_m = (self.diameter_mm ** 2) * 0.00617
        return unit_kg_per_m * self.total_length_m


@dataclass(frozen=True)
class RebarScheduleConfig:
    origin_xy: tuple[float, float] = (0.0, 0.0)
    row_height_mm: float = 8.0
    col_widths_mm: tuple[float, ...] = (15, 15, 30, 15, 25, 25)
    text_height_mm: float = 2.5
    items: list[RebarItem] = field(default_factory=list)


def build_schedule_geometry(cfg: RebarScheduleConfig) -> dict[str, Any]:
    """Marco + headers + filas + totales por diámetro."""
    ox, oy = cfg.origin_xy
    total_w = sum(cfg.col_widths_mm)
    items = cfg.items
    n_rows = len(items) + 2  # +1 header +1 totales

    rects = [(ox, oy, total_w, n_rows * cfg.row_height_mm)]
    # líneas
    for i in range(1, n_rows):
        rects.append((ox, oy + i * cfg.row_height_mm, total_w, 0))
    x_acc = ox
    for w in cfg.col_widths_mm[:-1]:
        x_acc += w
        rects.append((x_acc, oy, 0, n_rows * cfg.row_height_mm))

    headers = ["Marca", "φ (mm)", "L (mm)", "Cant.", "Σ L (m)", "Σ peso (kg)"]
    texts = []
    x_acc = ox
    y_h = oy + (n_rows - 0.5) * cfg.row_height_mm
    for h, w in zip(headers, cfg.col_widths_mm):
        texts.append({"pos": (x_acc + 1, y_h - 1.5), "text": h,
                      "height": cfg.text_height_mm})
        x_acc += w

    # filas
    total_kg = 0.0
    for i, it in enumerate(items):
        row_y = oy + (n_rows - 2 - i) * cfg.row_height_mm
        x_acc = ox
        values = [it.mark, str(it.diameter_mm), f"{it.length_mm:.0f}",
                   str(it.quantity), f"{it.total_length_m:.2f}",
                   f"{it.total_weight_kg:.1f}"]
        for v, w in zip(values, cfg.col_widths_mm):
            texts.append({"pos": (x_acc + 1, row_y + 1.5), "text": v,
                          "height": cfg.text_height_mm})
            x_acc += w
        total_kg += it.total_weight_kg

    # fila totales
    total_y = oy + 0.5 * cfg.row_height_mm
    x_acc = ox
    totals = ["TOTAL", "", "", "", "", f"{total_kg:.1f}"]
    for v, w in zip(totals, cfg.col_widths_mm):
        texts.append({"pos": (x_acc + 1, total_y - 1.5), "text": v,
                      "height": cfg.text_height_mm})
        x_acc += w

    return {"rectangles": rects, "texts": texts, "total_weight_kg": total_kg}


__all__ = ["RebarItem", "RebarScheduleConfig", "build_schedule_geometry"]
