# rebardxf

[Español](README.md) · **English**

Reinforced concrete drawings and rebar detailing to DXF, using `ezdxf`.

[![CI](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## What it does

- Beam, column and wall sections with their reinforcement, and detailing drawings of columns and footings with schedule and title block.
- Foundation plan that distributes the bars from A_s and states the calculation status.
- Bar shapes with the ACI 318-19 §25.3 bend diameters, cut lengths (BS 8666), schedules and reinforcement ratios.
- A1/A3 title blocks in paper space, layers in Spanish or AIA/ISO 13567, and export to several DXF versions (R2000 to R2018).

## Install

```bash
pip install git+https://github.com/jmurgass99/rebardxf.git
```

Optional extra: `api`. Requires Python 3.11 or later.

## Example

Plan of a 450 × 450 mm column with 8 Ø20 bars and Ø10 stirrups:

```python
from rebardxf import ColumnDetail

column = ColumnDetail(b=450.0, h=450.0, cover=40.0, bars=[(20.0, 8)],
                      db_stirrup=10.0, label="P-5", fc=30.0, Fy=500.0)
column.draw("P-5.dxf")
```

More cases in [`examples/`](examples).

## What it does not do

- Design: it does not calculate A_s, anchorage or laps; it draws and distributes what it receives and checks spacing and minimum ratios.
- Full construction drawings with details (joints, starter bars, construction joints): it generates parts and schedules, not a BIM.
- Sections with mixed diameters in one layer, or circular columns.
- Replace review of the drawing: the `REQUIERE_REVISION` status exists so someone looks at it.

Details are in [docs/LIMITACIONES.md](docs/LIMITACIONES.md) (in Spanish).

## Tests

```bash
pip install -e ".[test]"
pytest -q
```

## License

MIT. See [LICENSE](LICENSE). Author: [Jesús Murgas](https://github.com/jmurgass99).
