"""Tests para RebarCageMapping en RebarDXF."""
from rebardxf.geometry_mapping import SemanticRebarZone, build_rebar_cage_mesh


def test_rebar_cage_mapping_refinement():
    zones_coarse = [
        SemanticRebarZone("ZONE_1", 0.0, 1000.0, stirrup_spacing_mm=200.0),
        SemanticRebarZone("ZONE_2", 1000.0, 3000.0, stirrup_spacing_mm=300.0),
    ]
    zones_dense = [
        SemanticRebarZone("ZONE_1", 0.0, 1000.0, stirrup_spacing_mm=100.0),
        SemanticRebarZone("ZONE_2", 1000.0, 3000.0, stirrup_spacing_mm=150.0),
    ]

    st_c, lb_c, map_c, sum_c = build_rebar_cage_mesh(H_column_mm=3000.0, zones=zones_coarse)
    st_d, lb_d, map_d, sum_d = build_rebar_cage_mesh(H_column_mm=3000.0, zones=zones_dense)

    assert len(lb_c) == 8
    assert len(lb_d) == 8
    assert len(st_d) > len(st_c)
    assert len(map_d.zone_to_stirrups["ZONE_1"]) == 10
    assert sum_d["total_steel_weight_kg"] > sum_c["total_steel_weight_kg"]
    assert sum_d["anchorage_length_mm"] == 840.0
