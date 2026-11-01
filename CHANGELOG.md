# Changelog

## 1.2.0 — 2026-11-01

Correcciones encontradas al ejecutar los casos de uso del README.

- `ColumnDetail`: el reparto perimetral de barras usaba n_h = (total − 4·(n_b − 2))//2, que solo cuadra cuando hay dos barras por cara horizontal; con 12, 14 o 16 barras faltaban 2–4 posiciones y se rellenaban repitiendo la última, de modo que el DXF dibujaba círculos superpuestos en una esquina (12Ø20 se veía como 10 barras) mientras el rótulo y A_s decían 12. Ahora 2·n_b + 2·(n_h − 2) = total; un total impar repite una posición y lo dice el docstring.
- `export.save_dxf`: el parámetro `dxfversion` se validaba y se ignoraba (el bloque de fijación era un `pass`): el fichero salía siempre con la versión del documento. Ahora se asigna `doc.dxfversion` antes de guardar y el fichero releído tiene la versión pedida (R2000…R2018).
- Versión única: `pyproject.toml` decía 1.0.0, `__version__` 1.1.0 y la API 1.2.0; ahora 1.2.0 en los tres sitios. Descripción y keywords del paquete.
- Se retira `C-1_section.dxf` de la raíz del repositorio (artefacto generado; `/*.dxf` ya estaba en `.gitignore`).
- Documentado, sin corregir: `FootingData.s_commercial_step_mm` se acepta pero el rótulo redondea al milímetro; `rebar_schedule_block.RebarItem` pesa con 0,00617·d² (0,07 % sobre π/4·7850); `column_rebar_detail` dibuja cuatro barras de esquina en las secciones y una línea por marca en el alzado; `BeamDetail` dibuja cada capa con el diámetro del primer grupo; `SheetTemplate` escribe «v1.0» en el cajetín.
- 25 casos de uso ejecutados en `examples/` (secciones y detalles; planta de cimentación y alzados; despiece, longitudes de corte y cuantías; cuadros, plantillas, capas y escalas; exportación, integraciones, API y estado de cálculo), con su salida en `examples/output/`; `tests/test_examples.py` los ejecuta en CI. README reescrito.

## 1.1.0

Versión publicada como repositorio independiente (origen: RebarDXF del monorepo Structural JM).
