"""Cuadro de aceros y cuadro de revisiones como geometría independiente de ezdxf (rectángulos y textos), dibujados en la esquina de un plano DXF.

`build_schedule_geometry` genera marco, cabeceras, filas y totales por diámetro de un cuadro de
aceros en milímetros de papel (filas de 8 mm, texto de 2,5 mm); `build_revision_block_geometry`
hace lo mismo con las revisiones (número, fecha, descripción, autor) y `draw_revision_block_dxf`
lo lleva a un modelspace de ezdxf. La geometría sirve también para SVG o PDF sin tocar ezdxf.

Ejecutar:  python examples/schedule_block_and_revision_block_geometry_drawn_into_dxf_sheet_corner.py
"""
import os
from collections import Counter
from pathlib import Path

import ezdxf

from rebardxf.rebar_schedule_block import RebarItem, RebarScheduleConfig, build_schedule_geometry
from rebardxf.revision_block import RevisionBlockConfig, RevisionEntry, build_revision_block_geometry, draw_revision_block_dxf

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    items = [RebarItem("1", 20, 6350.0, 3, "11"), RebarItem("2", 16, 6350.0, 2, "11"), RebarItem("3", 16, 2400.0, 2, "1"), RebarItem("4", 10, 1544.0, 42, "51"), RebarItem("5", 8, 540.0, 12, "21")]
    cfg = RebarScheduleConfig(origin_xy=(600.0, 60.0), items=items)
    g = build_schedule_geometry(cfg)
    print(f"Cuadro de aceros: {len(items)} marcas → {len(g['rectangles'])} rectángulos/líneas, {len(g['texts'])} textos, total {g['total_weight_kg']:.1f} kg; "
          f"caja {sum(cfg.col_widths_mm):.0f} × {(len(items) + 2) * cfg.row_height_mm:.0f} mm de papel en ({cfg.origin_xy[0]:.0f}, {cfg.origin_xy[1]:.0f})")
    for it in items:
        print(f"  marca {it.mark}: Ø{it.diameter_mm} × {it.length_mm:.0f} mm × {it.quantity} = {it.total_length_m:.2f} m → {it.total_weight_kg:.1f} kg (0,00617·Ø²·L; exacto π/4·7850 = 0,006165·Ø²)")
    print(f"  Cabeceras: {[t['text'] for t in g['texts'][:6]]}; fila de totales: {[t['text'] for t in g['texts'][-6:] if t['text']]}")
    revs = [RevisionEntry(0, "2026-09-15", "Emisión inicial para revisión", "JM"), RevisionEntry(1, "2026-10-02", "Cambio de recubrimiento zapatas a 75 mm", "JM"),
            RevisionEntry(2, "2026-10-28", "Armado de pilares P-3 según nota de cálculo NC-07", "AR")]
    rcfg = RevisionBlockConfig(origin_xy=(600.0, 10.0), revisions=revs)
    rg = build_revision_block_geometry(rcfg)
    print(f"\nCuadro de revisiones: {len(revs)} revisiones → {len(rg['rectangles'])} rectángulos/líneas, {len(rg['texts'])} textos; caja {sum(rcfg.col_widths_mm):.0f} × {(len(revs) + 1) * rcfg.row_height_mm:.0f} mm")
    doc = ezdxf.new("R2018")
    msp = doc.modelspace()
    for x, y, w, h in g["rectangles"]:
        if w and h:
            msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], close=True)
        elif w:
            msp.add_line((x, y), (x + w, y))
        else:
            msp.add_line((x, y), (x, y + h))
    for t in g["texts"]:
        msp.add_text(t["text"], height=t["height"]).set_placement(t["pos"])
    draw_revision_block_dxf(msp, rcfg)
    p = OUT / "cuadros_aceros_revisiones.dxf"
    doc.saveas(str(p))
    cnt = Counter(e.dxftype() for e in ezdxf.readfile(str(p)).modelspace())
    print(f"\nDXF {p.name}: {dict(cnt)} (los dos cuadros en milímetros de papel, listos para pegar en un layout)")
    print("\nLa geometría es una lista de rectángulos (alto 0 = línea horizontal, ancho 0 = vertical) y textos con posición y altura: se prueba sin ezdxf y se dibuja con cualquier backend. "
          "El cuadro de aceros aquí no deduce longitudes de corte ni solapes; pesa con 0,00617·Ø² (0,07 % sobre el exacto).")


if __name__ == "__main__":
    main()
