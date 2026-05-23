"""
Bridge a AutoCAD vía COM — dibuja directo en la sesión activa.

Requisitos:
    pip install dxfstructuraljm[autocad]
    AutoCAD debe estar corriendo en la misma sesión Windows.

Uso típico:
    from dxfstructuraljm.integration.autocad_live import AutoCADClient

    with AutoCADClient() as cad:
        cad.set_layer("S-COLU-CONC", color=1)
        cad.draw_polyline([(0, 0), (1000, 0), (1000, 500), (0, 500), (0, 0)])
        cad.draw_text((500, 250), "VIGA-1", height=200)
"""
from __future__ import annotations

from typing import Any, Iterable, Sequence

from dxfstructuraljm.layer_standards import naming_for, LayerStandard


# --- helpers ------------------------------------------------------------

def _import_pyautocad() -> Any:
    """Importa pyautocad de forma perezosa (deja tests funcionar sin la dep)."""
    try:
        import pyautocad  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "pyautocad no instalado. `pip install dxfstructuraljm[autocad]` "
            "y asegúrate de tener AutoCAD corriendo."
        ) from exc
    return pyautocad


def _flatten_points(points: Iterable[Sequence[float]]) -> list[float]:
    """[(x,y), ...] -> [x1, y1, 0, x2, y2, 0, ...]  (AutoCAD COM exige 3D)."""
    out: list[float] = []
    for p in points:
        if len(p) == 2:
            out.extend([float(p[0]), float(p[1]), 0.0])
        elif len(p) == 3:
            out.extend([float(p[0]), float(p[1]), float(p[2])])
        else:
            raise ValueError(f"Point must have 2 or 3 components, got {p!r}")
    return out


# --- client -------------------------------------------------------------

def connect_to_autocad(visible: bool = True) -> Any:
    """
    Conecta a una instancia AutoCAD existente (o crea una).
    Devuelve el objeto pyautocad.Autocad.
    """
    pyautocad = _import_pyautocad()
    acad = pyautocad.Autocad(create_if_not_exists=True, visible=visible)
    # fuerza activación
    _ = acad.doc.Name
    return acad


class AutoCADClient:
    """
    Wrapper conveniente sobre pyautocad.Autocad.

    Uso como context manager:
        with AutoCADClient() as cad:
            cad.draw_polyline([...])

    Se puede inyectar `acad` (mock) para tests:
        AutoCADClient(acad=mock_acad)
    """

    def __init__(self, acad: Any | None = None, visible: bool = True) -> None:
        self._acad = acad
        self._visible = visible
        self._current_layer = "0"

    # context manager ------------------------------------------------
    def __enter__(self) -> "AutoCADClient":
        if self._acad is None:
            self._acad = connect_to_autocad(visible=self._visible)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # Nada que cerrar: pyautocad no abre handles propios.
        return None

    # propiedades base ----------------------------------------------
    @property
    def acad(self) -> Any:
        if self._acad is None:
            raise RuntimeError("Cliente no conectado. Usa `with AutoCADClient() as cad:`.")
        return self._acad

    @property
    def model(self) -> Any:
        return self.acad.ActiveDocument.ModelSpace

    # capas ----------------------------------------------------------
    def set_layer(self, name: str, color: int | None = None) -> Any:
        """
        Crea (o reutiliza) layer y la pone como activa.
        `color`: índice ACI (1=rojo, 2=amarillo, ...).
        """
        layers = self.acad.ActiveDocument.Layers
        try:
            layer = layers.Item(name)
        except Exception:
            layer = layers.Add(name)
        if color is not None:
            layer.color = int(color)
        self.acad.ActiveDocument.ActiveLayer = layer
        self._current_layer = name
        return layer

    def apply_layer_standard(self, country: str) -> LayerStandard | None:
        """
        Aplica el estándar de capas predominante en `country`.
        Crea una capa de muestra basada en `example` para que el usuario tenga
        un punto de partida.
        """
        std = naming_for(country)
        if std is None:
            return None
        self.set_layer(std.example, color=7)
        return std

    # entidades ------------------------------------------------------
    def draw_polyline(self, points: Iterable[Sequence[float]]) -> Any:
        """Dibuja una polilínea 3D (AddPolyline)."""
        pyautocad = _import_pyautocad()
        coords = _flatten_points(points)
        try:
            vertices = pyautocad.aDouble(*coords)
        except Exception:
            vertices = coords
        return self.model.AddPolyline(vertices)

    def draw_text(self, p: Sequence[float], text: str, height: float = 100.0) -> Any:
        """Texto AutoCAD (TextStyle activo)."""
        pyautocad = _import_pyautocad()
        if len(p) == 2:
            origin = (float(p[0]), float(p[1]), 0.0)
        else:
            origin = tuple(float(x) for x in p)
        try:
            point = pyautocad.APoint(*origin)
        except Exception:
            point = origin
        return self.model.AddText(text, point, float(height))

    def insert_block(
        self,
        name: str,
        p: Sequence[float],
        scale: float = 1.0,
        rotation: float = 0.0,
    ) -> Any:
        """Inserta un bloque ya definido (o externo .dwg)."""
        pyautocad = _import_pyautocad()
        if len(p) == 2:
            origin = (float(p[0]), float(p[1]), 0.0)
        else:
            origin = tuple(float(x) for x in p)
        try:
            point = pyautocad.APoint(*origin)
        except Exception:
            point = origin
        return self.model.InsertBlock(
            point, name, float(scale), float(scale), float(scale), float(rotation)
        )


__all__ = [
    "AutoCADClient",
    "connect_to_autocad",
]
