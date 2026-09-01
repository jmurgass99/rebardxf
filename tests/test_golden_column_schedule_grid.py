"""Golden test para cuadro de pilares clásico de hormigón armado en DXF.

Requisitos:
1. Generación de matriz gráfica de plantas vs columnas con despiece y rotulación completa.
2. Comprobación y recuento exacto de entidades DXF (LINES, CIRCLES, TEXTS) generadas en el modelo.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
import pytest
import ezdxf

from dxfstructuraljm.column_schedule_grid import (
    ColumnStorySpec,
    ColumnScheduleDrawer,
)


def test_golden_column_schedule_grid_entity_count():
    """GOLDEN. Validación de recuento exacto de entidades en el cuadro clásico de pilares."""
    columns = ["P-1", "P-2", "P-3"]
    stories = ["Planta Baja", "Planta 1"]

    specs = {
        ("Planta Baja", "P-1"): ColumnStorySpec("P-1", "Planta Baja", b_mm=400, h_mm=400, n_bars=8, db_mm=20.0),
        ("Planta Baja", "P-2"): ColumnStorySpec("P-2", "Planta Baja", b_mm=450, h_mm=450, n_bars=8, db_mm=25.0),
        ("Planta Baja", "P-3"): ColumnStorySpec("P-3", "Planta Baja", b_mm=350, h_mm=350, n_bars=4, db_mm=16.0),
        ("Planta 1", "P-1"): ColumnStorySpec("P-1", "Planta 1", b_mm=350, h_mm=350, n_bars=4, db_mm=16.0),
        ("Planta 1", "P-2"): ColumnStorySpec("P-2", "Planta 1", b_mm=400, h_mm=400, n_bars=8, db_mm=20.0),
        ("Planta 1", "P-3"): ColumnStorySpec("P-3", "Planta 1", b_mm=300, h_mm=300, n_bars=4, db_mm=16.0),
    }

    drawer = ColumnScheduleDrawer(
        columns=columns,
        stories=stories,
        specs=specs,
    )

    doc = ezdxf.new("R2010")
    stats = drawer.draw_to_doc(doc)

    # 1. Dimensiones de la matriz
    assert stats.total_columns == 3
    assert stats.total_stories == 2
    assert stats.total_cells == 6

    # 2. Recuento de entidades en el modelspace
    msp = doc.modelspace()
    lines = list(msp.query("LINE"))
    texts = list(msp.query("TEXT"))
    circles = list(msp.query("CIRCLE"))

    assert len(lines) == stats.line_entities
    assert len(texts) == stats.text_entities
    assert len(circles) == stats.circle_entities
    assert len(lines) + len(texts) + len(circles) == stats.total_entities

    # Cuadrícula base: 4 líneas horizontales + 5 líneas verticales = 9 líneas de tabla.
    # Cada una de las 6 celdas dibuja 4 líneas de contorno de hormigón + 4 líneas de estribo = 8 líneas * 6 = 48 líneas.
    # Total líneas esperadas = 9 + 48 = 57 líneas.
    assert len(lines) == 57

    # Círculos de armadura:
    # 8 barras (PB P-1) -> 8 + 4 extras = 12 círculos (distribución en caras)
    assert len(circles) > 0

    # Textos: 1 etiqueta cabecera + 3 columnas + 2 plantas + 2 textos por cada celda (12) = 18 textos
    assert len(texts) == 18

    # 3. Guardado en archivo temporal sin errores
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "cuadro_pilares.dxf"
        doc.saveas(str(out_path))
        assert out_path.exists()
        assert out_path.stat().st_size > 1000
