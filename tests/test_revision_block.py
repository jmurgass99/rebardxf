"""Tests para revision_block."""
from rebardxf.revision_block import (
    RevisionBlockConfig, RevisionEntry, build_revision_block_geometry,
)


def test_geometria_sin_revisiones():
    cfg = RevisionBlockConfig()
    geom = build_revision_block_geometry(cfg)
    # 1 marco exterior + 3 separadores verticales (4 columnas) + 0 horizontales
    assert len(geom["rectangles"]) >= 4
    # Sólo headers
    assert len(geom["texts"]) == 4


def test_geometria_con_revisiones():
    cfg = RevisionBlockConfig(revisions=[
        RevisionEntry(1, "2026-05-19", "Emisión", "JM"),
        RevisionEntry(2, "2026-06-01", "Corrección comentarios", "JM"),
    ])
    geom = build_revision_block_geometry(cfg)
    # 4 headers + 4 cols × 2 rows = 12 textos
    assert len(geom["texts"]) == 4 + 4 * 2
