"""Configuracion compartida de pytest."""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

# Asegura el package importable sin instalar
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def tmp_dxf(tmp_path: Path) -> Path:
    """Devuelve una ruta temporal para escribir un DXF."""
    return tmp_path / "out.dxf"
