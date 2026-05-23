# Testing — DXFStructuralJm

## Suites disponibles

Markers configurados en `pyproject.toml`:

| Marker        | Descripcion                                              |
|---------------|----------------------------------------------------------|
| `unit`        | Tests unitarios rapidos                                  |
| `integration` | Tests que escriben DXF a disco                           |
| `property`    | Tests basados en propiedades (hypothesis)                |
| `api`         | Tests del REST API (FastAPI TestClient)                  |
| `slow`        | Tests > 1s                                               |

## Ejecucion local

```bash
# todo
pytest

# solo unit
pytest -m unit

# excluir slow / property
pytest -m "not slow and not property"

# con cobertura
pytest --cov=dxfstructuraljm --cov-report=term-missing
```

En Windows:
```powershell
pwsh -File scripts/run_coverage.ps1
```

## Gate de cobertura

`pyproject.toml` define `fail_under = 75` en `[tool.coverage.report]`.
La build CI fallara si la cobertura agregada sobre `dxfstructuraljm/`
cae por debajo de 75%.

Modulos excluidos del calculo:
- `dxfstructuraljm/cli.py`
- `dxfstructuraljm/_brand.py`

## Dependencias de testing

Instalables via extras:
```bash
pip install -e .[test,api]
```

Incluye: `pytest`, `pytest-cov`, `hypothesis`, `httpx`.
