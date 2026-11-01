"""API REST sin servidor: pilar, viga, planta de cimentación y muro por POST, respuesta JSON con el DXF en base64 o como fichero, y 422 cuando la geometría no es válida.

`rebardxf.api.app` expone `/api/drawings/{health,column,beam,footing,wall}`; cada POST valida con
Pydantic, llama al servicio y devuelve metadatos (entidades, resumen, cuadro) más el DXF en base64
(`format=json`) o el fichero (`format=file`, media type application/dxf). Los errores tipados del
servicio (`GeometryError`, `ConfigurationError`) se traducen a 422 con el motivo. Requiere el extra
`api`.

Ejecutar:  python examples/rest_api_drawings_column_beam_footing_wall_testclient_json_base64_file_and_422.py
"""
import base64
import os
from collections import Counter
from pathlib import Path

OUT = Path(os.environ.get("JM_EXAMPLES_OUT_DIR", Path(__file__).resolve().parent / "out"))
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    try:
        import ezdxf
        from fastapi.testclient import TestClient

        from rebardxf.api.app import app
    except ImportError as exc:
        print(f"FastAPI no disponible ({exc}): instala `rebardxf[api]`.")
        return
    client = TestClient(app)
    print(f"API «{app.title}» v{app.version}; GET /api/drawings/health → {client.get('/api/drawings/health').json()}\n")
    r = client.post("/api/drawings/column", json={"label": "C-12", "b_mm": 500, "h_mm": 500, "cover_mm": 40, "bars": [[20, 12]], "db_stirrup_mm": 10, "fc_MPa": 30, "Fy_MPa": 500})
    j = r.json()
    dxf_bytes = base64.b64decode(j["dxf_base64"])
    p = OUT / "api_C-12.dxf"
    p.write_bytes(dxf_bytes)
    cnt = Counter(e.dxftype() for e in ezdxf.readfile(str(p)).modelspace())
    print(f"POST /column (12Ø20) → {r.status_code}; {j['bytes']} bytes en base64, entidades {j['n_entities']}, resumen ρ = {j['summary']['rho_pct']} %, A_s = {j['summary']['As_mm2']} mm²; DXF decodificado: {dict(cnt)}")
    r = client.post("/api/drawings/beam?format=file", json={"label": "V-201", "b_mm": 300, "h_mm": 600, "bars_top": [[16, 2]], "bars_bot": [[20, 4]], "db_stirrup_mm": 10})
    print(f"POST /beam?format=file → {r.status_code}, {r.headers['content-type']}, {len(r.content)} bytes, empieza por {r.content[:12]!r}")
    r = client.post("/api/drawings/footing", json={"footings": [{"label": "Z-1", "x": 0, "y": 0, "B": 2400, "L": 2400, "d": 600, "As_x": 1150, "As_y": 1150, "db": 16},
                                                                {"label": "Z-2", "x": 6000, "y": 0, "B": 2000, "L": 2000, "d": 500}], "column_size_mm": 400})
    j = r.json()
    print(f"POST /footing (2 zapatas) → {r.status_code}; cuadro: " + "; ".join(f"{row['label']} {row['status']}" for row in j["schedule"]) + f"; {j['n_total_entities']} entidades")
    r = client.post("/api/drawings/wall", json={"label": "M-3", "Lw_mm": 5000, "tw_mm": 300, "Lbe_mm": 700, "n_bars_be": 10, "db_be_mm": 20, "s_web_v_mm": 150, "s_web_h_mm": 150})
    j = r.json()
    print(f"POST /wall → {r.status_code}; ρ_be = {j['summary']['rho_be_pct']} %, ρ_v = {j['summary']['rho_v_pct']} %, check_v = {j['summary']['check_v']}")
    for payload, ruta, desc in (({"label": "C-x", "b_mm": 300, "h_mm": 300, "cover_mm": 160, "bars": [[16, 4]]}, "column", "recubrimiento ≥ b/2"),
                                ({"label": "V-x", "b_mm": 300, "h_mm": 500, "bars_top": [], "bars_bot": [[20, 3]]}, "beam", "sin barras superiores"),
                                ({"footings": []}, "footing", "sin zapatas"),
                                ({"label": "M-x", "Lw_mm": 1000, "Lbe_mm": 600}, "wall", "bordes que no caben")):
        r = client.post(f"/api/drawings/{ruta}", json=payload)
        print(f"  {ruta} con {desc} → {r.status_code}: {r.json()['detail'] if r.status_code == 422 else r.json()}")
    r = client.post("/api/drawings/column?format=pdf", json={"label": "C-1"})
    print(f"  format=pdf → {r.status_code} (solo json|file)")
    print("\nLa API escribe cada DXF en un directorio temporal y lo devuelve; no guarda estado ni autentica: es para montar detrás de un gateway o para pruebas. Sin endpoints de despiece de pilar/zapata ni de cuadro de pilares: esos van por los servicios de Python.")


if __name__ == "__main__":
    main()
