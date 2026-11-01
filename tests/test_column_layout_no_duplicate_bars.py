# -*- coding: utf-8 -*-
"""ColumnDetail reparte las barras por el perímetro sin superponerlas.

Hasta la 1.2.0, n_h = (total − 4·(n_b − 2))//2 dejaba 2–4 posiciones sin cubrir para
12, 14 y 16 barras y se rellenaban repitiendo la última: el DXF mostraba 10 círculos
donde el rótulo decía 12Ø20. La identidad correcta es 2·n_b + 2·(n_h − 2) = total.
"""
from __future__ import annotations

import pytest

from rebardxf import ColumnDetail


@pytest.mark.parametrize("total", [4, 6, 8, 10, 12, 14, 16, 20, 24])
@pytest.mark.parametrize("b,h", [(500.0, 500.0), (300.0, 600.0), (800.0, 400.0)])
def test_even_counts_give_distinct_positions(total, b, h):
    col = ColumnDetail(b=b, h=h, cover=40.0, bars=[(20.0, total)], db_stirrup=10.0)
    pts = col._bar_positions
    assert len(pts) == total
    assert len({(round(x, 6), round(y, 6)) for x, y in pts}) == total
    # las cuatro esquinas siempre armadas
    d = 40.0 + 10.0 + 10.0
    corners = {(d, d), (b - d, d), (b - d, h - d), (d, h - d)}
    assert corners <= {(round(x, 6), round(y, 6)) for x, y in pts}
    # todas sobre el perímetro del rectángulo de centros
    for x, y in pts:
        assert abs(x - d) < 1e-9 or abs(x - (b - d)) < 1e-9 or abs(y - d) < 1e-9 or abs(y - (h - d)) < 1e-9


def test_odd_count_repeats_exactly_one_position():
    col = ColumnDetail(b=500.0, h=500.0, cover=40.0, bars=[(20.0, 9)], db_stirrup=10.0)
    pts = col._bar_positions
    assert len(pts) == 9
    assert len({(round(x, 6), round(y, 6)) for x, y in pts}) == 8
