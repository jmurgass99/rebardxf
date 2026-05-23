"""
Layers normalizados según AIA CAD Layer Guidelines (US National CAD Standard)
adaptados para ingeniería estructural en castellano.

Estructura: <Disciplina>-<Mayor>-<Menor>-<Status>
Ejemplos: S-COLU-RBAR, S-WALL-CONC, S-BEAM-DIMS
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIALayer:
    name: str
    description: str
    color_aci: int           # AutoCAD Color Index
    linetype: str = "Continuous"
    lineweight_mm: float = 0.25


STRUCTURAL_LAYERS: list[AIALayer] = [
    # Estructura — concreto
    AIALayer("S-COLU-CONC",  "Columnas - Hormigón",       3),
    AIALayer("S-COLU-RBAR",  "Columnas - Refuerzo",       1, lineweight_mm=0.50),
    AIALayer("S-BEAM-CONC",  "Vigas - Hormigón",          5),
    AIALayer("S-BEAM-RBAR",  "Vigas - Refuerzo",          1, lineweight_mm=0.50),
    AIALayer("S-SLAB-CONC",  "Losas - Hormigón",          4),
    AIALayer("S-SLAB-RBAR",  "Losas - Refuerzo",          1),
    AIALayer("S-WALL-CONC",  "Muros - Hormigón",          6),
    AIALayer("S-WALL-RBAR",  "Muros - Refuerzo",          1),
    AIALayer("S-FNDN-CONC",  "Fundaciones - Hormigón",    9),
    AIALayer("S-FNDN-RBAR",  "Fundaciones - Refuerzo",    1, lineweight_mm=0.50),
    # Estructura — acero
    AIALayer("S-COLS-STEL",  "Columnas - Acero",          2),
    AIALayer("S-BEAM-STEL",  "Vigas - Acero",             2),
    AIALayer("S-CONN-WELD",  "Conexiones - Soldadura",    1, lineweight_mm=0.70),
    AIALayer("S-CONN-BOLT",  "Conexiones - Pernos",       2),
    # Anotaciones
    AIALayer("S-ANNO-DIMS",  "Cotas",                     7, lineweight_mm=0.15),
    AIALayer("S-ANNO-TEXT",  "Textos",                    7, lineweight_mm=0.15),
    AIALayer("S-ANNO-SYMB",  "Símbolos",                  7),
    AIALayer("S-ANNO-NPLT",  "Líneas de no impresión",    8, lineweight_mm=0.0),
    AIALayer("S-ANNO-LEGN",  "Leyendas",                  7),
    # Grilla
    AIALayer("S-GRID",       "Ejes / Grillas",            8, linetype="DASHDOT"),
    AIALayer("S-GRID-IDEN",  "Identificadores de eje",    7),
]


def get_layer(name: str) -> AIALayer | None:
    for L in STRUCTURAL_LAYERS:
        if L.name == name:
            return L
    return None


def apply_to_dxf(doc) -> int:
    """Inyecta todos los layers en un Document de ezdxf."""
    n = 0
    for L in STRUCTURAL_LAYERS:
        if L.name in doc.layers:
            continue
        layer = doc.layers.new(L.name)
        layer.color = L.color_aci
        layer.dxf.lineweight = int(L.lineweight_mm * 100)  # ezdxf usa cents-mm
        try:
            layer.dxf.linetype = L.linetype
        except Exception:
            pass
        n += 1
    return n


__all__ = ["AIALayer", "STRUCTURAL_LAYERS", "get_layer", "apply_to_dxf"]
