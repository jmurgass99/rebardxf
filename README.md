# rebardxf

Planos estructurales y despiece de armaduras a DXF desde Python: secciones de viga y pilar con su armado, detalles de armado de zapatas, planta de cimentación, alzados de pórticos, cuadros de despiece con longitudes de corte y pesos, formas de barra, cuadros de pilares, cajetines y bloques de revisión, capas según estándar AIA, escalas y plantillas A1/A3. Los ficheros se abren en AutoCAD, BricsCAD, LibreCAD o cualquier visor DXF.

[![CI](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Paquete independiente. Única dependencia: `ezdxf`.

## Instalación

```bash
pip install git+https://github.com/jmurgass99/rebardxf.git
```

Extras: `api` (REST con FastAPI), `autocad` (envío en vivo a AutoCAD con pyautocad, solo Windows), `test`.

## Inicio rápido

```python
from rebardxf import BeamDetail, ColumnDetail, RebarSchedule

beam = BeamDetail(b=300, h=500, cover=30, bars_top=[(16, 2)], bars_bot=[(20, 3)],
                  db_stirrup=10, s_critical=100, s_central=200, span=6000, label="V-1")
beam.draw_section("V-1_section.dxf")

col = ColumnDetail(b=400, h=400, cover=40, bars=[(20, 8)], db_stirrup=10, label="C-1")
col.draw("C-1_section.dxf")

sched = RebarSchedule()
sched.add("1", "V-1", 20, 3, 6400, "straight")
sched.add("2", "V-1", 16, 2, 6400, "straight")
sched.print_table()                      # cuadro con pesos por marca
print(sched.total_weight(), "kg")
```

Verificación de un DXF generado (entidades, capas, texto):

```python
from rebardxf.export import verify
print(verify("V-1_section.dxf"))
```

Interfaz de línea de comandos: `rebardxf --help`.

El script `examples/01_beam_and_column_sections.py` genera los dos DXF y el despiece.

## Módulos

| Módulo | Contenido |
|---|---|
| `core`, `layers`, `layer_standards`, `aia_layers` | Documento DXF, capas y estándares de nombres |
| `beam_section`, `column_section`, `wall_detail` | Secciones con armado |
| `column_rebar_detail`, `footing_rebar_detail`, `foundation_plan`, `frame_elevation` | Detalles de armado, planta de cimentación, alzados |
| `rebar_schedule`, `rebar_schedule_block`, `rebar_shapes`, `rebar_cut_length`, `rebar_quantities` | Despiece, formas, longitudes de corte y cuantías |
| `column_schedule_grid`, `revision_block`, `templates`, `templates_construction`, `scales` | Cuadros, cajetines, plantillas y escalas |
| `export` | Guardado con auditoría, verificación y limpieza |
| `integration/` | Enlace Revit-DXF y AutoCAD en vivo (opcional) |
| `api/`, `cli` | REST y línea de comandos |

## Validación

Tests golden sobre las entidades exactas de los DXF (alzados, cuadros de pilares, invariantes del documento), longitudes de corte y diámetros de doblado, más tests de propiedades con hypothesis.

## Licencia

MIT. Consulta [LICENSE](LICENSE).

---

Parte del toolkit estructural de código abierto **Loadpath**, de [Jesús Murgas](https://github.com/jmurgass99).
