"""
rebar_schedule.py — Automatic rebar bill of materials (despiece).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field


STEEL_DENSITY = 7850.0  # kg/m³


@dataclass
class RebarEntry:
    """Single rebar entry in the schedule."""
    mark: str          # bar mark (e.g. "1", "2A")
    element: str       # element label (e.g. "C-1", "V-2")
    diameter: float    # db [mm]
    count: int         # number of bars
    length: float      # cut length [mm]
    shape: str = "straight"   # 'straight', 'L', 'U', 'hook'


@dataclass
class RebarSchedule:
    """
    Rebar bill of materials (despiece de armadura).

    Automatically computes:
    - Unit weight per bar
    - Total weight per mark
    - Grand total weight

    Parameters
    ----------
    entries : list[RebarEntry]  list of rebar entries to include
    """
    entries: list[RebarEntry] = field(default_factory=list)

    def add(self, mark: str, element: str, diameter: float,
            count: int, length: float, shape: str = "straight") -> None:
        """Add a rebar entry."""
        self.entries.append(RebarEntry(mark, element, diameter, count, length, shape))

    def unit_weight(self, db: float) -> float:
        """Weight per linear meter [kg/m] for diameter db [mm]."""
        return STEEL_DENSITY * math.pi * (db / 1000)**2 / 4

    def total_weight(self) -> float:
        """Grand total steel weight [kg]."""
        total = 0.0
        for e in self.entries:
            wpm = self.unit_weight(e.diameter)       # kg/m
            L_m = e.length / 1000                    # m
            total += wpm * L_m * e.count
        return round(total, 2)

    def to_table(self) -> list[dict]:
        """
        Return rebar schedule as list of dicts for export/display.

        Columns: mark, element, db, count, L_mm, L_total_m, unit_wt_kg_m, total_kg
        """
        rows = []
        for e in self.entries:
            wpm = self.unit_weight(e.diameter)
            L_m = e.length / 1000
            total_kg = round(wpm * L_m * e.count, 3)
            rows.append({
                "mark": e.mark,
                "element": e.element,
                "shape": e.shape,
                "db_mm": int(e.diameter),
                "count": e.count,
                "L_mm": e.length,
                "L_total_m": round(e.count * L_m, 2),
                "unit_wt_kg_m": round(wpm, 4),
                "total_kg": total_kg,
            })
        return rows

    def summary_by_diameter(self) -> dict[int, dict]:
        """Group total weight by bar diameter."""
        groups: dict[int, float] = {}
        for e in self.entries:
            db = int(e.diameter)
            wpm = self.unit_weight(e.diameter)
            kg = wpm * e.length / 1000 * e.count
            groups[db] = groups.get(db, 0.0) + kg
        return {db: {"total_kg": round(kg, 2)} for db, kg in sorted(groups.items())}

    def print_table(self) -> None:
        """Print formatted schedule to console."""
        rows = self.to_table()
        header = f"{'Mark':>5} {'Element':>8} {'db':>4} {'n':>4} {'L(mm)':>8} {'Total(kg)':>10}"
        print(header)
        print("-" * len(header))
        for r in rows:
            print(f"{r['mark']:>5} {r['element']:>8} {r['db_mm']:>4} {r['count']:>4} "
                  f"{r['L_mm']:>8.0f} {r['total_kg']:>10.3f}")
        print("=" * len(header))
        print(f"{'TOTAL':>40} {self.total_weight():>10.2f} kg")
