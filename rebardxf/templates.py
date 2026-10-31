"""
templates.py — Sheet templates: outer frame, title block and logo placeholder.

Supported sheet sizes (ISO 216): A4, A3, A2, A1, A0.
All coordinates are in paperspace millimetres.

By AutoCAD/LibreCAD convention, the sheet frame and title block belong to a
*paperspace* (a.k.a. layout). Use :meth:`SheetTemplate.apply_to_layout` to draw
them in a layout and to add a viewport that shows the modelspace contents.

A legacy :meth:`SheetTemplate.draw_in_modelspace` method (also aliased as
:meth:`SheetTemplate.draw`) is kept for backwards compatibility — it draws the
same frame and cartouche directly in modelspace and emits a ``DeprecationWarning``.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
import warnings

from .core import DXFDocument, Layer, HAS_EZDXF
from .scales import SHEET_SIZES_MM
from ._brand import NAME as _BRAND_NAME
from .layers import apply_layers, STANDARD_LAYERS
from .exceptions import TemplateError


# Margins (mm): left larger for binding, others identical
MARGIN_LEFT  = 25.0
MARGIN_OTHER = 10.0


@dataclass
class TitleBlockInfo:
    """Metadata shown in the title block."""
    project:  str = "Proyecto"
    drawing:  str = "Plano S-01"
    scale:    str = "1:50"
    date:     str = field(default_factory=lambda: date.today().isoformat())
    revision: str = "A"
    designer: str = "JM"
    checker:  str = "—"
    client:   str = ""
    notes:    str = ""


@dataclass
class SheetTemplate:
    """
    Generate a sheet frame + title block.

    By convention the frame and cartouche are placed in a *paperspace* layout
    via :meth:`apply_to_layout`. The legacy :meth:`draw_in_modelspace` method
    draws them in modelspace and is kept only for backwards compatibility.

    Parameters
    ----------
    size : 'A4' .. 'A0'  ISO sheet code
    info : TitleBlockInfo
    insert : tuple[float,float]  bottom-left corner of the sheet
        (used only by the legacy modelspace path; paperspace always inserts
        at the origin of the layout).
    """
    size: str = "A3"
    info: TitleBlockInfo = field(default_factory=TitleBlockInfo)
    insert: tuple[float, float] = (0.0, 0.0)

    def __post_init__(self) -> None:
        if self.size not in SHEET_SIZES_MM:
            raise TemplateError(f"Tamano de hoja desconocido '{self.size}'")
        self.width, self.height = SHEET_SIZES_MM[self.size]

    # ==================================================================
    # PAPERSPACE / LAYOUT API  (recommended)
    # ==================================================================
    def apply_to_layout(self, doc, layout_name: str | None = None,
                        viewport: bool = True,
                        view_center: tuple[float, float] | None = None,
                        view_height: float | None = None):
        """
        Create (or reuse) a paperspace layout, configure its page setup,
        draw the frame + title block in paperspace and add a viewport that
        shows the contents of modelspace.

        Parameters
        ----------
        doc : ezdxf.Drawing or DXFDocument
            Document where the layout is created. If a DXFDocument wrapper
            is given, its underlying ezdxf doc is used.
        layout_name : str | None
            Name of the layout to create/reuse. Defaults to ``f'{size}_Sheet'``
            (e.g. ``'A3_Sheet'``).
        viewport : bool
            If True (default) add a paperspace viewport showing modelspace.
        view_center : tuple[float,float] | None
            Center of the modelspace view shown through the viewport.
            Defaults to ``(0, 0)``.
        view_height : float | None
            Height of the modelspace view (in model units) shown through
            the viewport. Defaults to the printable height (auto-fit 1:1).

        Returns
        -------
        ezdxf.layouts.Layout
            The configured paperspace layout.
        """
        if not HAS_EZDXF:
            raise RuntimeError("ezdxf is required for paperspace layouts.")

        ez_doc = self._unwrap_doc(doc)

        # Ensure standard layers are present (idempotent)
        try:
            if "CAJETIN" not in ez_doc.layers:
                apply_layers(ez_doc, STANDARD_LAYERS)
        except Exception:
            pass

        layout_name = layout_name or f"{self.size}_Sheet"
        layout = self._get_or_create_layout(ez_doc, layout_name)
        self._configure_page_setup(layout)

        # Paperspace drawing (origin = bottom-left of paper, mm)
        self._draw_outer_border_ps(layout)
        self._draw_inner_frame_ps(layout)
        self._draw_title_block_ps(layout)
        self._draw_logo_placeholder_ps(layout)

        if viewport:
            self._add_viewport(layout, view_center, view_height)

        return layout

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _unwrap_doc(doc):
        """Accept either DXFDocument wrapper or raw ezdxf.Drawing."""
        return getattr(doc, "_doc", doc)

    @staticmethod
    def _get_or_create_layout(ez_doc, name: str):
        """Return existing layout or create a new one."""
        try:
            return ez_doc.layouts.get(name)
        except Exception:
            pass
        try:
            if name in [l.name for l in ez_doc.layouts]:
                return ez_doc.layouts.get(name)
        except Exception:
            pass
        return ez_doc.layouts.new(name)

    def _configure_page_setup(self, layout) -> None:
        """Set the layout paper size (mm), units and printable area."""
        try:
            layout.page_setup(
                size=(self.width, self.height),
                margins=(MARGIN_OTHER, MARGIN_OTHER, MARGIN_OTHER, MARGIN_LEFT),
                units="mm",
                offset=(0, 0),
                rotation=0,
            )
            # Reset PS UCS so paper origin is at (0,0)
            try:
                layout.reset_paper_limits()
            except Exception:
                pass
        except Exception:
            # Some ezdxf builds may not expose page_setup on every layout type
            pass

    # ------------------------------------------------------------------
    # Paperspace primitives (origin at paper bottom-left)
    # ------------------------------------------------------------------
    _LW_OUTER = 35   # 0.35 mm
    _LW_INNER = 70   # 0.70 mm
    _LW_GRID  = 25   # 0.25 mm
    _LW_THIN  = 18   # 0.18 mm

    @staticmethod
    def _ps_rectangle(layout, x: float, y: float, w: float, h: float,
                      layer: str, lineweight: int) -> None:
        pts = [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
        layout.add_lwpolyline(
            pts, close=True,
            dxfattribs={"layer": layer, "lineweight": lineweight},
        )

    @staticmethod
    def _ps_line(layout, p1, p2, layer: str, lineweight: int) -> None:
        layout.add_line(
            start=(p1[0], p1[1]),
            end=(p2[0], p2[1]),
            dxfattribs={"layer": layer, "lineweight": lineweight},
        )

    @staticmethod
    def _ps_text(layout, pos, content: str, height: float, layer: str) -> None:
        layout.add_text(
            content,
            dxfattribs={
                "layer": layer,
                "height": height,
                "insert": (pos[0], pos[1]),
            },
        )

    def _draw_outer_border_ps(self, layout) -> None:
        self._ps_rectangle(layout, 0.0, 0.0, self.width, self.height,
                           layer=Layer.TITLE_BLOCK.value,
                           lineweight=self._LW_OUTER)

    def _draw_inner_frame_ps(self, layout) -> None:
        x0 = MARGIN_LEFT
        y0 = MARGIN_OTHER
        w  = self.width  - MARGIN_LEFT  - MARGIN_OTHER
        h  = self.height - 2 * MARGIN_OTHER
        self._ps_rectangle(layout, x0, y0, w, h,
                           layer=Layer.TITLE_BLOCK.value,
                           lineweight=self._LW_INNER)

    def _draw_title_block_ps(self, layout) -> None:
        cw = 180.0 if self.size in ("A1", "A0", "A2") else 150.0
        ch = 50.0  if self.size in ("A1", "A0", "A2") else 40.0
        x0 = self.width - MARGIN_OTHER - cw
        y0 = MARGIN_OTHER

        self._ps_rectangle(layout, x0, y0, cw, ch,
                           layer=Layer.TITLE_BLOCK.value,
                           lineweight=self._LW_INNER)

        rows, cols = 4, 3
        rh = ch / rows
        cw_each = cw / cols
        for i in range(1, rows):
            self._ps_line(layout, (x0, y0 + i * rh), (x0 + cw, y0 + i * rh),
                          layer=Layer.TITLE_BLOCK.value, lineweight=self._LW_GRID)
        for j in range(1, cols):
            self._ps_line(layout, (x0 + j * cw_each, y0),
                          (x0 + j * cw_each, y0 + ch),
                          layer=Layer.TITLE_BLOCK.value, lineweight=self._LW_GRID)

        info = self.info
        h_label = 2.0
        h_value = 2.8

        def cell(col: int, row: int, label: str, value: str) -> None:
            cx = x0 + col * cw_each + 1.5
            cy = y0 + (rows - 1 - row) * rh
            self._ps_text(layout, (cx, cy + rh - h_label - 1.0),
                          label, h_label, Layer.TEXT.value)
            self._ps_text(layout, (cx, cy + 1.5),
                          value, h_value, Layer.TEXT.value)

        cell(0, 0, "PROYECTO",  info.project)
        cell(1, 0, "CLIENTE",   info.client or "—")
        cell(2, 0, "PLANO",     info.drawing)
        cell(0, 1, "ESCALA",    info.scale)
        cell(1, 1, "FECHA",     info.date)
        cell(2, 1, "REVISION",  info.revision)
        cell(0, 2, "DISENO",    info.designer)
        cell(1, 2, "REVISO",    info.checker)
        cell(2, 2, "HOJA",      "1/1")
        cell(0, 3, "NOTAS",     info.notes[:32])
        cell(1, 3, "",          "")
        cell(2, 3, _BRAND_NAME, "v1.0")

    def _draw_logo_placeholder_ps(self, layout) -> None:
        size = 25.0
        lx = MARGIN_LEFT + 5.0
        ly = self.height - MARGIN_OTHER - size - 5.0
        self._ps_rectangle(layout, lx, ly, size, size,
                           layer=Layer.TITLE_BLOCK.value,
                           lineweight=self._LW_GRID)
        self._ps_text(layout, (lx + 4, ly + size / 2 - 2),
                      "LOGO", 3.0, Layer.TEXT.value)

    # ------------------------------------------------------------------
    # Viewport
    # ------------------------------------------------------------------
    def _add_viewport(self, layout,
                      view_center: tuple[float, float] | None,
                      view_height: float | None):
        """
        Add a paperspace viewport inside the inner frame, leaving the
        cartouche area free.

        Viewport size (paper mm):
            width  = inner_width  - (cartouche_w + small gap)
            height = inner_height
        Default modelspace view: centered at origin, height fits the viewport
        at 1:1 (model units in mm).
        """
        cw = 180.0 if self.size in ("A1", "A0", "A2") else 150.0
        gap = 5.0

        inner_w = self.width  - MARGIN_LEFT  - MARGIN_OTHER
        inner_h = self.height - 2 * MARGIN_OTHER

        vp_w = inner_w - cw - gap
        vp_h = inner_h
        vp_cx = MARGIN_LEFT + vp_w / 2.0
        vp_cy = MARGIN_OTHER + vp_h / 2.0

        vc = view_center if view_center is not None else (0.0, 0.0)
        vh = view_height if view_height is not None else vp_h  # 1:1 fit

        try:
            return layout.add_viewport(
                center=(vp_cx, vp_cy),
                size=(vp_w, vp_h),
                view_center_point=vc,
                view_height=vh,
                dxfattribs={"layer": Layer.TITLE_BLOCK.value},
            )
        except Exception:
            return None

    # ==================================================================
    # LEGACY MODELSPACE API  (deprecated)
    # ==================================================================
    def draw_in_modelspace(self, doc: DXFDocument) -> None:
        """
        Legacy: draw frame + cartouche directly into modelspace.

        Kept for backwards compatibility. New code should use
        :meth:`apply_to_layout` so the cartouche lives in paperspace as
        per AutoCAD/LibreCAD convention.
        """
        warnings.warn(
            "SheetTemplate.draw_in_modelspace() is deprecated; "
            "use SheetTemplate.apply_to_layout(doc) to draw the sheet "
            "in paperspace per AutoCAD/LibreCAD convention.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._draw_outer_border(doc)
        self._draw_inner_frame(doc)
        self._draw_title_block(doc)
        self._draw_logo_placeholder(doc)

    # Backwards-compatible alias
    def draw(self, doc: DXFDocument) -> None:
        """Deprecated alias of :meth:`draw_in_modelspace`."""
        self.draw_in_modelspace(doc)

    # ------------------------------------------------------------------
    # Internal — modelspace drawing (legacy)
    # ------------------------------------------------------------------
    def _draw_outer_border(self, doc: DXFDocument) -> None:
        x, y = self.insert
        doc.rectangle(x, y, self.width, self.height,
                      layer=Layer.TITLE_BLOCK, lineweight=0.35)

    def _draw_inner_frame(self, doc: DXFDocument) -> None:
        x, y = self.insert
        x0 = x + MARGIN_LEFT
        y0 = y + MARGIN_OTHER
        w  = self.width  - MARGIN_LEFT  - MARGIN_OTHER
        h  = self.height - 2 * MARGIN_OTHER
        doc.rectangle(x0, y0, w, h,
                      layer=Layer.TITLE_BLOCK, lineweight=0.70)

    def _draw_title_block(self, doc: DXFDocument) -> None:
        cw = 180.0 if self.size in ("A1", "A0", "A2") else 150.0
        ch = 50.0  if self.size in ("A1", "A0", "A2") else 40.0

        x, y = self.insert
        x0 = x + self.width  - MARGIN_OTHER - cw
        y0 = y + MARGIN_OTHER

        doc.rectangle(x0, y0, cw, ch,
                      layer=Layer.TITLE_BLOCK, lineweight=0.70)

        rows = 4
        cols = 3
        rh = ch / rows
        cw_each = cw / cols
        for i in range(1, rows):
            doc.line((x0, y0 + i * rh), (x0 + cw, y0 + i * rh),
                     layer=Layer.TITLE_BLOCK, lineweight=0.25)
        for j in range(1, cols):
            doc.line((x0 + j * cw_each, y0), (x0 + j * cw_each, y0 + ch),
                     layer=Layer.TITLE_BLOCK, lineweight=0.25)

        info = self.info
        h_label = 2.0
        h_value = 2.8

        def cell(col: int, row: int, label: str, value: str) -> None:
            cx = x0 + col * cw_each + 1.5
            cy = y0 + (rows - 1 - row) * rh
            doc.text((cx, cy + rh - h_label - 1.0), label, height=h_label)
            doc.text((cx, cy + 1.5), value, height=h_value)

        cell(0, 0, "PROYECTO",  info.project)
        cell(1, 0, "CLIENTE",   info.client or "—")
        cell(2, 0, "PLANO",     info.drawing)
        cell(0, 1, "ESCALA",    info.scale)
        cell(1, 1, "FECHA",     info.date)
        cell(2, 1, "REVISION",  info.revision)
        cell(0, 2, "DISENO",    info.designer)
        cell(1, 2, "REVISO",    info.checker)
        cell(2, 2, "HOJA",      "1/1")
        cell(0, 3, "NOTAS",     info.notes[:32])
        cell(1, 3, "",          "")
        cell(2, 3, _BRAND_NAME, "v1.0")

    def _draw_logo_placeholder(self, doc: DXFDocument) -> None:
        x, y = self.insert
        size = 25.0
        lx = x + MARGIN_LEFT + 5.0
        ly = y + self.height - MARGIN_OTHER - size - 5.0
        doc.rectangle(lx, ly, size, size,
                      layer=Layer.TITLE_BLOCK, lineweight=0.25)
        doc.text((lx + 4, ly + size / 2 - 2), "LOGO", height=3.0)


# ---------------------------------------------------------------------------
# Convenience factories
# ---------------------------------------------------------------------------
def A3(info: TitleBlockInfo | None = None,
       insert: tuple[float, float] = (0.0, 0.0)) -> SheetTemplate:
    """A3 landscape template."""
    return SheetTemplate(size="A3", info=info or TitleBlockInfo(), insert=insert)


def A1(info: TitleBlockInfo | None = None,
       insert: tuple[float, float] = (0.0, 0.0)) -> SheetTemplate:
    """A1 landscape template."""
    return SheetTemplate(size="A1", info=info or TitleBlockInfo(), insert=insert)
