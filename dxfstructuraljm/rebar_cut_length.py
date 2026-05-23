"""
rebar_cut_length.py — Longitud de corte de barras dobladas (planilla de despiece).

La longitud de corte se mide por la FIBRA NEUTRA (centerline), no por las cotas
out-to-out: en cada doblez el contorno exterior es mayor que el eje. Dos formas:

  - ``cut_length_centerline``: tramos rectos (medidos al eje) + arcos de doblez.
        arco = (angulo_rad)·(r + db/2),  r = radio interior de doblado.
  - ``bend_deduction``: descuento para pasar de cotas OUT-TO-OUT a longitud de
        corte:  deduccion = 2·(r + db)·tan(theta/2) − arco.

Coherente con ACI Detailing Manual / BS 8666 (la longitud de corte siempre es
menor que la suma de cotas exteriores por los descuentos de doblez).
"""
from __future__ import annotations

import math
from typing import Sequence


def bend_arc_length(angle_deg: float, inside_diameter_mm: float, db_mm: float) -> float:
    """Longitud del arco de doblez por la fibra neutra (mm).

    arco = theta · (r + db/2), con r = inside_diameter/2.
    """
    r = inside_diameter_mm / 2.0
    return math.radians(angle_deg) * (r + db_mm / 2.0)


def bend_deduction(angle_deg: float, inside_diameter_mm: float, db_mm: float) -> float:
    """Descuento de doblez para cotas out-to-out (mm).

    deduccion = 2·(r + db)·tan(theta/2) − arco_fibra_neutra.  (>= 0)
    Para un doblez de 90deg da el clasico descuento de la planilla.
    """
    r = inside_diameter_mm / 2.0
    tangent = 2.0 * (r + db_mm) * math.tan(math.radians(angle_deg) / 2.0)
    ded = tangent - bend_arc_length(angle_deg, inside_diameter_mm, db_mm)
    return max(ded, 0.0)


def cut_length_centerline(straight_legs_mm: Sequence[float],
                          bend_angles_deg: Sequence[float],
                          inside_diameter_mm: float,
                          db_mm: float,
                          hook_tails_mm: Sequence[float] = ()) -> float:
    """Longitud de corte por la fibra neutra (mm).

    = Σ tramos rectos (al eje) + Σ arcos de doblez + Σ colas de gancho.
    El numero de dobleces es len(bend_angles_deg).
    """
    L = sum(straight_legs_mm) + sum(hook_tails_mm)
    for ang in bend_angles_deg:
        L += bend_arc_length(ang, inside_diameter_mm, db_mm)
    return L


def cut_length_from_outside(outside_legs_mm: Sequence[float],
                            bend_angles_deg: Sequence[float],
                            inside_diameter_mm: float,
                            db_mm: float) -> float:
    """Longitud de corte a partir de cotas OUT-TO-OUT, restando deducciones.

    = Σ cotas exteriores − Σ deducciones de doblez.
    """
    L = sum(outside_legs_mm)
    for ang in bend_angles_deg:
        L -= bend_deduction(ang, inside_diameter_mm, db_mm)
    return L


__all__ = [
    "bend_arc_length", "bend_deduction",
    "cut_length_centerline", "cut_length_from_outside",
]
