"""
Cuadro de revisiones estándar para planos estructurales.

Genera un bloque DXF parametrizable: encabezado + filas de revisión
(número, fecha, descripción, autor). Útil para todos los planos
generados por RebarDXF.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    import ezdxf
    _HAS_EZDXF = True
except ImportError:
    _HAS_EZDXF = False


@dataclass(frozen=True)
class RevisionEntry:
    number: int
    date_iso: str        # YYYY-MM-DD
    description: str
    author: str


@dataclass(frozen=True)
class RevisionBlockConfig:
    origin_xy: tuple[float, float] = (0.0, 0.0)
    row_height_mm: float = 8.0
    col_widths_mm: tuple[float, float, float, float] = (10, 25, 80, 20)
    text_height_mm: float = 2.5
    revisions: list[RevisionEntry] = field(default_factory=list)


def build_revision_block_geometry(cfg: RevisionBlockConfig
                                    ) -> dict[str, Any]:
    """Devuelve la geometría sin depender de ezdxf — útil para tests y
    para portar a otros backends DXF/SVG/PDF.

    Returns:
        dict con keys 'rectangles' (list of (x,y,w,h)) y 'texts'
        (list of {'pos': (x,y), 'text': str, 'height': float}).
    """
    ox, oy = cfg.origin_xy
    total_w = sum(cfg.col_widths_mm)
    n_rows = len(cfg.revisions) + 1  # +1 header
    rects: list[tuple[float, float, float, float]] = []
    texts: list[dict[str, Any]] = []

    # Marco exterior
    rects.append((ox, oy, total_w, n_rows * cfg.row_height_mm))

    # Líneas horizontales
    for i in range(1, n_rows):
        y = oy + i * cfg.row_height_mm
        rects.append((ox, y, total_w, 0))  # alto 0 = línea

    # Líneas verticales
    x_acc = ox
    for w in cfg.col_widths_mm[:-1]:
        x_acc += w
        rects.append((x_acc, oy, 0, n_rows * cfg.row_height_mm))

    # Header
    headers = ["Rev", "Fecha", "Descripción", "Autor"]
    x_acc = ox
    y_h = oy + (n_rows - 0.5) * cfg.row_height_mm
    for h, w in zip(headers, cfg.col_widths_mm):
        texts.append({"pos": (x_acc + 1, y_h - 1.5), "text": h,
                      "height": cfg.text_height_mm})
        x_acc += w

    # Filas
    for i, rev in enumerate(cfg.revisions):
        row_y = oy + (n_rows - 2 - i) * cfg.row_height_mm
        x_acc = ox
        for value, w in zip(
            (str(rev.number), rev.date_iso, rev.description, rev.author),
            cfg.col_widths_mm,
        ):
            texts.append({"pos": (x_acc + 1, row_y + 1.5), "text": value,
                          "height": cfg.text_height_mm})
            x_acc += w

    return {"rectangles": rects, "texts": texts}


def draw_revision_block_dxf(msp, cfg: RevisionBlockConfig) -> None:
    """Dibuja el bloque sobre un modelspace de ezdxf."""
    if not _HAS_EZDXF:
        raise ImportError("ezdxf no instalado")
    geom = build_revision_block_geometry(cfg)
    for x, y, w, h in geom["rectangles"]:
        if w == 0 and h > 0:
            msp.add_line((x, y), (x, y + h))
        elif h == 0 and w > 0:
            msp.add_line((x, y), (x + w, y))
        elif w > 0 and h > 0:
            msp.add_lwpolyline([
                (x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)
            ], close=True)
    for t in geom["texts"]:
        msp.add_text(t["text"], height=t["height"]).set_placement(t["pos"])


__all__ = ["RevisionEntry", "RevisionBlockConfig",
           "build_revision_block_geometry", "draw_revision_block_dxf"]
