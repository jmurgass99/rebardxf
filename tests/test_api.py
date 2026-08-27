"""Tests del REST API via FastAPI TestClient."""
from __future__ import annotations
import base64
import pytest

fastapi = pytest.importorskip("fastapi")
httpx_lib = pytest.importorskip("httpx")
from fastapi.testclient import TestClient

from dxfstructuraljm.api.app import app

pytestmark = pytest.mark.api

client = TestClient(app)


def test_health():
    r = client.get("/api/drawings/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_column_endpoint_json():
    r = client.post("/api/drawings/column", json={
        "label": "C-API",
        "b_mm": 500, "h_mm": 500,
        "bars": [[25, 8]],
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["label"] == "C-API"
    assert data["bytes"] > 100
    raw = base64.b64decode(data["dxf_base64"])
    assert b"0" in raw[:10]  # DXF header starts with 0 group code
    assert len(raw) == data["bytes"]


def test_column_endpoint_file():
    r = client.post("/api/drawings/column?format=file", json={
        "label": "C-FILE", "b_mm": 400, "h_mm": 400,
        "bars": [[20, 4]],
    })
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/dxf"
    assert len(r.content) > 100


def test_column_endpoint_invalid_returns_422():
    r = client.post("/api/drawings/column", json={
        "label": "BAD", "b_mm": -1, "bars": [[25, 8]],
    })
    assert r.status_code == 422


def test_beam_endpoint():
    r = client.post("/api/drawings/beam", json={"label": "V-API"})
    assert r.status_code == 200, r.text
    assert r.json()["bytes"] > 100


def test_footing_endpoint():
    r = client.post("/api/drawings/footing", json={
        "footings": [{
            "label": "Z-1", "x": 0, "y": 0,
            "B": 2000, "L": 2000, "d": 500,
        }],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["n_footings"] == 1


def test_wall_endpoint():
    r = client.post("/api/drawings/wall", json={"label": "M-API"})
    assert r.status_code == 200, r.text
    assert r.json()["bytes"] > 100


def test_wall_endpoint_invalid_geometry():
    r = client.post("/api/drawings/wall", json={
        "Lw_mm": 1000, "Lbe_mm": 600,
    })
    assert r.status_code == 422
