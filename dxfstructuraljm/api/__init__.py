"""REST API para DXFStructuralJm (FastAPI).

Importar :func:`get_app` lazy para no requerir fastapi en instalaciones
sin extras ``[api]``.
"""
from __future__ import annotations


def get_app():
    """Construye la app FastAPI bajo demanda."""
    from .app import app
    return app


__all__ = ["get_app"]
