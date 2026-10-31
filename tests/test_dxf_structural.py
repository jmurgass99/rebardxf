"""
tests/test_dxf_structural.py — Tests for RebarDXF.
Tests are geometry/logic focused (no DXF file I/O required).
"""
import pytest
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rebardxf.core import DXFDocument, Layer, HAS_EZDXF
from rebardxf.column_section import ColumnDetail
from rebardxf.beam_section import BeamDetail
from rebardxf.foundation_plan import FoundationPlan, FootingData
from rebardxf.rebar_schedule import RebarSchedule
from rebardxf.templates import SheetTemplate, TitleBlockInfo, A3, A1


# ---------------------------------------------------------------------------
# DXFDocument core tests
# ---------------------------------------------------------------------------
class TestDXFDocument:

    def setup_method(self):
        self.doc = DXFDocument(":memory:")  # no actual file

    def test_line_adds_to_list(self):
        self.doc.line((0, 0), (100, 0))
        assert len(self.doc._lines) == 1

    def test_circle_adds_to_list(self):
        self.doc.circle((50, 50), 10)
        assert len(self.doc._circles) == 1

    def test_rectangle_adds_4_lines(self):
        self.doc.rectangle(0, 0, 100, 200)
        assert len(self.doc._lines) == 4

    def test_text_adds_to_list(self):
        self.doc.text((0, 0), "TEST")
        assert len(self.doc._texts) == 1

    def test_n_entities(self):
        self.doc.line((0, 0), (10, 0))
        self.doc.circle((5, 5), 3)
        e = self.doc.n_entities()
        assert e["lines"] == 1
        assert e["circles"] == 1

    def test_multiple_layers(self):
        self.doc.line((0, 0), (10, 0), layer=Layer.REBAR)
        self.doc.line((0, 0), (10, 0), layer=Layer.CONCRETE)
        assert len(self.doc._lines) == 2


# ---------------------------------------------------------------------------
# ColumnDetail tests
# ---------------------------------------------------------------------------
class TestColumnDetail:

    def setup_method(self):
        self.col = ColumnDetail(
            b=500, h=500, cover=40,
            bars=[(25, 8)], db_stirrup=10, label="C-1"
        )

    def test_total_bars(self):
        assert self.col._total_bars == 8

    def test_as_total(self):
        expected = math.pi * 25**2 / 4 * 8
        assert self.col.as_total() == pytest.approx(expected, rel=1e-3)

    def test_rho_in_range(self):
        rho = self.col.rho()
        assert 0.005 <= rho <= 0.08  # EC8 valid range

    def test_bar_positions_count(self):
        assert len(self.col._bar_positions) == 8

    def test_bar_diameter(self):
        assert self.col.bar_diameter() == 25.0

    def test_summary_keys(self):
        s = self.col.summary()
        for k in ["label", "b_mm", "h_mm", "cover_mm", "As_mm2", "rho_pct"]:
            assert k in s

    def test_draw_returns_doc(self):
        doc = self.col.draw(output_path=None)
        assert isinstance(doc, DXFDocument)

    def test_draw_creates_entities(self):
        doc = self.col.draw(output_path=None)
        e = doc.n_entities()
        assert e["lines"] >= 8    # outline + stirrup + dimensions
        assert e["circles"] >= 8  # one per bar

    def test_4_bar_column(self):
        col4 = ColumnDetail(b=400, h=400, cover=40, bars=[(20, 4)])
        assert col4._total_bars == 4
        assert len(col4._bar_positions) == 4

    def test_larger_section_higher_rho_for_same_bars(self):
        col_big   = ColumnDetail(b=700, h=700, bars=[(25, 8)])
        col_small = ColumnDetail(b=300, h=300, bars=[(25, 8)])
        assert col_small.rho() > col_big.rho()

    def test_mixed_bars(self):
        col = ColumnDetail(b=500, h=500, bars=[(25, 4), (16, 4)])
        assert col._total_bars == 8
        assert col.bar_diameter() == 25.0

    def test_rho_below_max_limit(self):
        """Steel ratio should be < 8% for any reasonable input."""
        col = ColumnDetail(b=300, h=300, bars=[(32, 8)])
        assert col.rho() < 0.08


# ---------------------------------------------------------------------------
# BeamDetail tests
# ---------------------------------------------------------------------------
class TestBeamDetail:

    def setup_method(self):
        self.beam = BeamDetail(
            b=300, h=600, cover=30,
            bars_top=[(20, 2)], bars_bot=[(20, 3)],
            db_stirrup=8, label="V-1"
        )

    def test_as_top(self):
        expected = math.pi * 20**2 / 4 * 2
        assert self.beam.as_top() == pytest.approx(expected, rel=1e-3)

    def test_as_bot_greater_than_top(self):
        assert self.beam.as_bot() > self.beam.as_top()

    def test_summary_keys(self):
        s = self.beam.summary()
        for k in ["label", "b_mm", "h_mm", "As_top_mm2", "As_bot_mm2"]:
            assert k in s

    def test_draw_section_returns_doc(self):
        doc = self.beam.draw_section(output_path=None)
        assert isinstance(doc, DXFDocument)

    def test_draw_creates_circles_for_bars(self):
        doc = self.beam.draw_section(output_path=None)
        n_top = sum(n for _, n in self.beam.bars_top)
        n_bot = sum(n for _, n in self.beam.bars_bot)
        assert doc.n_entities()["circles"] >= n_top + n_bot

    def test_bar_positions_cover(self):
        positions = self.beam._bar_x_positions(3)
        assert len(positions) == 3
        assert all(p > self.beam.cover for p in positions)


# ---------------------------------------------------------------------------
# FoundationPlan tests
# ---------------------------------------------------------------------------
class TestFoundationPlan:

    def setup_method(self):
        self.footings = [
            FootingData("Z-1", 0,    0,    2000, 2000, 500, 800, 800, 16),
            FootingData("Z-2", 6000, 0,    2500, 2500, 600, 1000, 1000, 16),
            FootingData("Z-3", 0,    6000, 2000, 2000, 500, 800, 800, 16),
        ]
        self.plan = FoundationPlan(self.footings)

    def test_schedule_table_rows(self):
        rows = self.plan.schedule_table()
        assert len(rows) == 3

    def test_schedule_has_required_keys(self):
        rows = self.plan.schedule_table()
        for k in ["label", "B_m", "L_m", "d_m", "As_x_mm2_m"]:
            assert k in rows[0]

    def test_draw_returns_doc(self):
        doc = self.plan.draw("test_plan.dxf")
        assert isinstance(doc, DXFDocument)

    def test_draw_creates_lines_for_each_footing(self):
        doc = self.plan.draw("test_plan.dxf")
        # Each footing = 4 outline lines + 4 column lines + axis = ≥8 lines
        assert doc.n_entities()["lines"] >= len(self.footings) * 8

    def test_footing_area(self):
        f = self.footings[0]
        area = f.B * f.L / 1e6  # m²
        assert area == pytest.approx(4.0, rel=0.01)


# ---------------------------------------------------------------------------
# RebarSchedule tests
# ---------------------------------------------------------------------------
class TestRebarSchedule:

    def setup_method(self):
        self.sched = RebarSchedule()
        self.sched.add("1", "C-1", 25.0, 8,  3200, "straight")
        self.sched.add("2", "V-1", 16.0, 3,  5200, "straight")
        self.sched.add("3", "V-1", 16.0, 4,  5200, "hook")
        self.sched.add("4", "Z-1", 20.0, 14, 1800, "straight")

    def test_n_entries(self):
        assert len(self.sched.entries) == 4

    def test_unit_weight_16mm(self):
        """Ø16 bar ≈ 1.578 kg/m"""
        w = self.sched.unit_weight(16.0)
        assert w == pytest.approx(1.578, rel=0.02)

    def test_total_weight_positive(self):
        assert self.sched.total_weight() > 0

    def test_table_has_all_rows(self):
        rows = self.sched.to_table()
        assert len(rows) == 4

    def test_table_row_has_required_keys(self):
        rows = self.sched.to_table()
        for k in ["mark", "element", "db_mm", "count", "L_mm",
                  "L_total_m", "unit_wt_kg_m", "total_kg"]:
            assert k in rows[0]

    def test_summary_by_diameter(self):
        groups = self.sched.summary_by_diameter()
        assert 25 in groups
        assert 16 in groups
        assert 20 in groups

    def test_larger_count_gives_more_weight(self):
        s1 = RebarSchedule()
        s1.add("1", "X", 20.0, 4, 3000)
        s2 = RebarSchedule()
        s2.add("1", "X", 20.0, 8, 3000)
        assert s2.total_weight() == pytest.approx(2 * s1.total_weight(), rel=0.001)

    def test_longer_bars_give_more_weight(self):
        s1 = RebarSchedule()
        s1.add("1", "X", 20.0, 4, 2000)
        s2 = RebarSchedule()
        s2.add("1", "X", 20.0, 4, 4000)
        assert s2.total_weight() == pytest.approx(2 * s1.total_weight(), rel=0.001)


# ---------------------------------------------------------------------------
# SheetTemplate paperspace tests
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not HAS_EZDXF, reason="ezdxf not installed")
class TestSheetTemplatePaperspace:

    def _new_doc(self):
        return DXFDocument(":memory:")

    def test_apply_to_layout_creates_layout(self):
        doc = self._new_doc()
        sheet = A3(TitleBlockInfo(project="Test", drawing="S-01"))
        layout = sheet.apply_to_layout(doc)
        assert layout is not None
        assert "A3_Sheet" in [l.name for l in doc._doc.layouts]

    def test_layout_has_frame_and_cartouche_entities(self):
        doc = self._new_doc()
        sheet = A3()
        layout = sheet.apply_to_layout(doc)
        # outer + inner + cartouche box = 3 lwpolylines; grid lines = 5;
        # logo box = 1 lwpolyline; texts >= 12 fields + LOGO label
        entities = list(layout)
        n_poly  = sum(1 for e in entities if e.dxftype() == "LWPOLYLINE")
        n_line  = sum(1 for e in entities if e.dxftype() == "LINE")
        n_text  = sum(1 for e in entities if e.dxftype() == "TEXT")
        n_vport = sum(1 for e in entities if e.dxftype() == "VIEWPORT")
        assert n_poly >= 4         # outer, inner, cartouche, logo
        assert n_line >= 5         # 3 row + 2 col separators
        assert n_text >= 12        # at least the cartouche labels/values
        assert n_vport >= 1        # viewport added by default

    def test_a1_uses_a1_size(self):
        doc = self._new_doc()
        sheet = A1()
        layout = sheet.apply_to_layout(doc, layout_name="A1_Test")
        assert "A1_Test" in [l.name for l in doc._doc.layouts]
        assert sheet.width == 841 and sheet.height == 594

    def test_modelspace_untouched_by_paperspace_draw(self):
        doc = self._new_doc()
        n_msp_before = len(list(doc._doc.modelspace()))
        A3().apply_to_layout(doc)
        n_msp_after = len(list(doc._doc.modelspace()))
        assert n_msp_after == n_msp_before  # nothing added to modelspace

    def test_idempotent_layout_reuse(self):
        doc = self._new_doc()
        sheet = A3()
        sheet.apply_to_layout(doc, layout_name="Reused")
        sheet.apply_to_layout(doc, layout_name="Reused")
        names = [l.name for l in doc._doc.layouts]
        # Layout name appears only once even after second apply
        assert names.count("Reused") == 1

    def test_save_and_reload_no_auditor_errors(self, tmp_path):
        import ezdxf
        out = tmp_path / "sheet_a3.dxf"
        doc = DXFDocument(str(out))
        A3(TitleBlockInfo(project="Reload", drawing="S-99")).apply_to_layout(doc)
        doc.save()
        reloaded = ezdxf.readfile(str(out))
        auditor = reloaded.audit()
        assert len(auditor.errors) == 0
        assert "A3_Sheet" in [l.name for l in reloaded.layouts]

    def test_legacy_draw_in_modelspace_emits_warning(self):
        doc = self._new_doc()
        sheet = A3()
        with pytest.warns(DeprecationWarning):
            sheet.draw_in_modelspace(doc)
        # And it actually drew something in modelspace
        assert doc.n_entities()["lines"] > 0

    def test_legacy_draw_alias_emits_warning(self):
        doc = self._new_doc()
        with pytest.warns(DeprecationWarning):
            A3().draw(doc)

    def test_unknown_size_raises(self):
        with pytest.raises(ValueError):
            SheetTemplate(size="A9")
