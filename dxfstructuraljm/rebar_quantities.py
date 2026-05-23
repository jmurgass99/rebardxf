"""
Cuadro de cuantías por elemento (idea #6).

Genera resumen de acero (kg, kg/m3) por elemento estructural a partir
de una lista de barras. Soporta etiquetado por código:
- ACI (USA), Eurocode (EU), NSR-10 (CO), AS (AU), SG.

Densidad acero = 7850 kg/m3. Diámetros normalizados según código:
- USA/ACI: #3..#11 -> mm equivalente.
- EU/SG: 6, 8, 10, 12, 16, 20, 25, 32 mm.
- AU/AS: N12..N40.
- NSR: similar EU/ACI mixto.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

STEEL_DENSITY_kg_m3 = 7850.0

_DIAMETERS_MM = {
    "USA": {"#3": 9.5, "#4": 12.7, "#5": 15.9, "#6": 19.1, "#7": 22.2,
            "#8": 25.4, "#9": 28.7, "#10": 32.3, "#11": 35.8},
    "EU": {"6": 6, "8": 8, "10": 10, "12": 12, "16": 16, "20": 20, "25": 25, "32": 32},
    "SG": {"6": 6, "8": 8, "10": 10, "12": 12, "16": 16, "20": 20, "25": 25, "32": 32},
    "AU": {"N12": 12, "N16": 16, "N20": 20, "N24": 24, "N28": 28, "N32": 32, "N36": 36, "N40": 40},
    "NSR": {"#3": 9.5, "#4": 12.7, "#5": 15.9, "#6": 19.1, "#8": 25.4, "12": 12, "16": 16, "20": 20, "25": 25},
}


@dataclass(frozen=True)
class RebarItem:
    element_id: str          # "V-101", "C-3", etc.
    designation: str         # "#5" or "16"
    length_m: float
    count: int = 1


@dataclass(frozen=True)
class ElementGeometry:
    element_id: str
    volume_m3: float         # volumen de hormigón del elemento


@dataclass(frozen=True)
class QuantityRow:
    element_id: str
    total_weight_kg: float
    volume_m3: float
    cuantia_kg_per_m3: float


def diameter_mm(designation: str, code: str = "USA") -> float:
    c = code.upper()
    if c == "USA" or c == "ACI":
        table = _DIAMETERS_MM["USA"]
    elif c in ("EU", "EUROCODE"):
        table = _DIAMETERS_MM["EU"]
    elif c in ("AU", "AS"):
        table = _DIAMETERS_MM["AU"]
    elif c in ("NSR", "CO"):
        table = _DIAMETERS_MM["NSR"]
    elif c in ("SG", "SS"):
        table = _DIAMETERS_MM["SG"]
    else:
        raise ValueError(f"Código desconocido: {code}")
    if designation not in table:
        raise ValueError(f"Designación {designation} no encontrada para {code}")
    return table[designation]


def bar_weight_per_m(designation: str, code: str = "USA") -> float:
    """kg/m de la barra."""
    d = diameter_mm(designation, code)
    area_m2 = 3.14159265 * (d / 1000.0) ** 2 / 4.0
    return area_m2 * STEEL_DENSITY_kg_m3


def summarize_quantities(
    bars: List[RebarItem],
    geometries: List[ElementGeometry],
    code: str = "USA",
) -> List[QuantityRow]:
    """Calcula cuantía total por elemento."""
    if not bars:
        return []
    weight_by_el: Dict[str, float] = {}
    for b in bars:
        w_per_m = bar_weight_per_m(b.designation, code)
        weight_by_el[b.element_id] = weight_by_el.get(b.element_id, 0.0) + w_per_m * b.length_m * b.count
    vol_by_el = {g.element_id: g.volume_m3 for g in geometries}
    rows: List[QuantityRow] = []
    for el, w in weight_by_el.items():
        v = vol_by_el.get(el, 0.0)
        cu = (w / v) if v > 0 else 0.0
        rows.append(QuantityRow(element_id=el, total_weight_kg=w, volume_m3=v, cuantia_kg_per_m3=cu))
    rows.sort(key=lambda r: r.element_id)
    return rows


def total_project_steel_kg(bars: List[RebarItem], code: str = "USA") -> float:
    return sum(bar_weight_per_m(b.designation, code) * b.length_m * b.count for b in bars)
