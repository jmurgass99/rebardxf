"""
Estándares internacionales de capas (layers) CAD.

US:   AIA CAD Layer Guidelines / National CAD Standard (NCS)
EU:   ISO 13567 / DIN 6779
SG:   BCA CORENET BIM Layer Guide
AU:   AS 1100 + NATSPEC BIM
CO:   ICONTEC NTC 1960 (uso DIN-like) — referencia NCS
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LayerStandard:
    code_id: str
    description: str
    naming_pattern: str         # ejemplo del patrón
    example: str


STANDARDS: list[LayerStandard] = [
    LayerStandard(
        "AIA-NCS-US", "AIA / US National CAD Standard",
        "<DISCIPLINE>-<MAJOR>-<MINOR>-<STATUS>",
        "S-COLU-CONC",
    ),
    LayerStandard(
        "ISO-13567-EU", "ISO 13567 (Eurocode CAD layers)",
        "A<SUBJECT><ELEMENT><PRESENTATION>",
        "A21S101",  # area 21 (estructura), elemento S, presentación 101
    ),
    LayerStandard(
        "BCA-CORENET-SG", "Singapore CORENET BIM Layer Guide",
        "<DISCIPLINE>_<ELEMENT>_<PROPERTY>",
        "S_COL_RBAR",
    ),
    LayerStandard(
        "NATSPEC-AU", "NATSPEC National BIM Guide (Australia)",
        "<MODEL>-<CATEGORY>-<TYPE>",
        "ST-COL-CONC",
    ),
    LayerStandard(
        "NTC-1960-CO", "ICONTEC NTC 1960 (Colombia)",
        "<DISCIPLINE>-<ELEMENT>-<PROPERTY>",
        "EST-COL-HOR",
    ),
]


def lookup(code_id: str) -> LayerStandard | None:
    for s in STANDARDS:
        if s.code_id == code_id:
            return s
    return None


def naming_for(country: str) -> LayerStandard | None:
    """Devuelve el estándar predominante por país (heurística)."""
    mapping = {
        "US": "AIA-NCS-US", "USA": "AIA-NCS-US",
        "DE": "ISO-13567-EU", "ES": "ISO-13567-EU", "FR": "ISO-13567-EU",
        "SG": "BCA-CORENET-SG",
        "AU": "NATSPEC-AU", "NZ": "NATSPEC-AU",
        "CO": "NTC-1960-CO",
    }
    code = mapping.get(country.upper())
    return lookup(code) if code else None


__all__ = ["LayerStandard", "STANDARDS", "lookup", "naming_for"]
