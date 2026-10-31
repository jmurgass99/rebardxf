"""CLI minimo para RebarDXF."""
from __future__ import annotations
import argparse
import sys

from . import __version__


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    """Punto de entrada del CLI."""
    p = argparse.ArgumentParser(prog="rebardxf")
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--serve", action="store_true",
                   help="Levantar el REST API con uvicorn (requiere extras [api])")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8000)
    args = p.parse_args(argv)
    if args.serve:
        import uvicorn
        from .api.app import app
        uvicorn.run(app, host=args.host, port=args.port)
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
