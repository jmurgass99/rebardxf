"""Jerarquia de excepciones tipadas de DXFStructuralJm.

Todas heredan de :class:`DXFError`. Algunas tambien multi-heredan de
``ValueError`` o ``ImportError`` para mantener compatibilidad con codigo
cliente que captura esos tipos estandar.
"""
from __future__ import annotations

__all__ = [
    "DXFError",
    "ConfigurationError",
    "GeometryError",
    "TemplateError",
    "DependencyError",
]


class DXFError(Exception):
    """Excepcion base para errores del paquete DXFStructuralJm."""


class ConfigurationError(DXFError, ValueError):
    """Configuracion invalida (parametros de entrada inconsistentes)."""


class GeometryError(DXFError, ValueError):
    """Geometria invalida (dimensiones negativas, recubrimientos
    incompatibles, posiciones imposibles, etc.)."""


class TemplateError(DXFError, ValueError):
    """Error en plantillas de planos (tamano de hoja desconocido,
    cajetin invalido, layout repetido, etc.)."""


class DependencyError(DXFError, ImportError):
    """Falta una dependencia opcional requerida (p.ej. ``ezdxf``)."""
