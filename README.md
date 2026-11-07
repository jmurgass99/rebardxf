# rebardxf

**Español** · [English](README.en.md)

Planos de hormigón armado y despiece de armaduras a DXF, con `ezdxf`.

[![CI](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml/badge.svg)](https://github.com/jmurgass99/rebardxf/actions/workflows/ci.yml)
[![Licencia: MIT](https://img.shields.io/badge/licencia-MIT-green)](LICENSE)

## Qué hace

- Secciones de viga, pilar y muro con su armado, y planos de despiece de pilares y zapatas con planilla y cajetín.
- Planta de cimentación que reparte las barras a partir de A_s y declara el estado de cálculo.
- Formas de barra con los diámetros de doblado de ACI 318-19 §25.3, longitudes de corte (BS 8666), planillas y cuantías.
- Cajetines A1/A3 en espacio papel, capas en castellano o AIA/ISO 13567, y exportación a varias versiones de DXF (R2000 a R2018).

## Instalación

```bash
pip install git+https://github.com/jmurgass99/rebardxf.git
```

Extra opcional: `api`. Requiere Python 3.11 o superior.

## Ejemplo

Planta de un pilar de 450 × 450 mm con 8 barras de Ø20 y cercos de Ø10:

```python
from rebardxf import ColumnDetail

pilar = ColumnDetail(b=450.0, h=450.0, cover=40.0, bars=[(20.0, 8)],
                     db_stirrup=10.0, label="P-5", fc=30.0, Fy=500.0)
pilar.draw("P-5.dxf")
```

Más casos en [`examples/`](examples).

## Qué no hace

- Dimensionar: no calcula A_s, anclajes ni solapes; dibuja y reparte lo que recibe y comprueba separaciones y cuantías mínimas.
- Planos de ejecución completos con detalles constructivos (nudos, esperas, juntas): genera piezas y cuadros, no un BIM.
- Secciones con diámetros mezclados en una capa, ni pilares circulares.
- Sustituir la revisión del plano: el estado `REQUIERE_REVISION` existe para que alguien lo mire.

El detalle está en [docs/LIMITACIONES.md](docs/LIMITACIONES.md).

## Pruebas

```bash
pip install -e ".[test]"
pytest -q
```

## Licencia

MIT. Ver [LICENSE](LICENSE). Autor: [Jesús Murgas](https://github.com/jmurgass99).
