"""Golden test para cuadro de pilares clásico de hormigón armado en DXF.

Requisitos:
1. Generación de matriz gráfica de plantas vs columnas con despiece y rotulación completa.
2. Comprobación y recuento exacto de entidades DXF (LINES, CIRCLES, TEXTS) generadas en el modelo.
3. Validación estricta de que el número de círculos dibujados coincide exactamente con spec.n_bars.
4. Validación de que las 4 esquinas de la sección están siempre armadas.
5. Validación de que números impares o menores de 4 lanzan ValueError.
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

    # Total barras en la matriz de 6 celdas:
    # Planta Baja: P-1 (8) + P-2 (8) + P-3 (4) = 20 barras
    # Planta 1:    P-1 (4) + P-2 (8) + P-3 (4) = 16 barras
    # Total círculos esperados = 20 + 16 = 36 círculos exactamente.
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

    # Círculos de armadura: coincidencia exacta con la suma de barras especificadas
    assert len(circles) == 36
    assert stats.circle_entities == 36

    # Textos: 1 etiqueta cabecera + 3 columnas + 2 plantas + 2 textos por cada celda (12) = 18 textos
    assert len(texts) == 18

    # Comprobación de que los rótulos tienen formato dimensional consistente y unidad explícita
    text_values = [t.dxf.text for t in texts]
    assert any("40x40 cm - 8Ø20" in tv for tv in text_values)
    assert any("45x45 cm - 8Ø25" in tv for tv in text_values)
    assert any("35x35 cm - 4Ø16" in tv for tv in text_values)
    assert any("30x30 cm - 4Ø16" in tv for tv in text_values)

    # 3. Guardado en archivo temporal sin errores
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "cuadro_pilares.dxf"
        doc.saveas(str(out_path))
        assert out_path.exists()
        assert out_path.stat().st_size > 1000


@pytest.mark.parametrize("n_bars", [4, 6, 8, 10, 12, 16, 20])
def test_golden_column_schedule_exact_bar_circle_count(n_bars: int):
    """GOLDEN. Verifica que para cualquier n_bars par >= 4, se dibujen exactamente n_bars círculos."""
    columns = ["C1"]
    stories = ["Nivel 1"]
    spec = ColumnStorySpec(
        column_tag="C1",
        story_name="Nivel 1",
        b_mm=400.0,
        h_mm=500.0,
        n_bars=n_bars,
        db_mm=20.0,
        cover_mm=40.0,
    )
    drawer = ColumnScheduleDrawer(
        columns=columns,
        stories=stories,
        specs={("Nivel 1", "C1"): spec},
    )

    doc = ezdxf.new("R2010")
    stats = drawer.draw_to_doc(doc)
    msp = doc.modelspace()
    circles = list(msp.query("CIRCLE"))

    # Validación exacta de recuento
    assert len(circles) == n_bars, f"Se esperaban {n_bars} círculos y se dibujaron {len(circles)}"
    assert stats.circle_entities == n_bars

    # Validación de esquinas ocupadas
    center_points = [(round(c.dxf.center.x, 2), round(c.dxf.center.y, 2)) for c in circles]
    xs = [p[0] for p in center_points]
    ys = [p[1] for p in center_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    assert (min_x, min_y) in center_points, "Esquina inferior-izquierda desocupada"
    assert (max_x, min_y) in center_points, "Esquina inferior-derecha desocupada"
    assert (max_x, max_y) in center_points, "Esquina superior-derecha desocupada"
    assert (min_x, max_y) in center_points, "Esquina superior-izquierda desocupada"


@pytest.mark.parametrize("invalid_n", [1, 2, 3, 5, 7, 9, 11])
def test_golden_column_schedule_rejects_invalid_bar_counts(invalid_n: int):
    """GOLDEN. Rechazo explícito con ValueError de armaduras impares o menores de 4 en columnas rectangulares."""
    spec = ColumnStorySpec(
        column_tag="C_ERR",
        story_name="Piso 1",
        b_mm=400.0,
        h_mm=400.0,
        n_bars=invalid_n,
        db_mm=16.0,
    )
    drawer = ColumnScheduleDrawer(
        columns=["C_ERR"],
        stories=["Piso 1"],
        specs={("Piso 1", "C_ERR"): spec},
    )
    doc = ezdxf.new("R2010")
    with pytest.raises(ValueError, match="spec.n_bars must be"):
        drawer.draw_to_doc(doc)
