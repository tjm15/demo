import json
import sys
from pathlib import Path

sys.path.append('/home/tjm/code/demo')

from fastapi.testclient import TestClient
from apps.kernel.main import app


client = TestClient(app)


def test_retrieve_minimal():
    body = {"question": "conservation area roof extensions", "top_k": 5}
    r = client.post("/retrieve", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "chunks" in data and isinstance(data["chunks"], list)
    # allow empty but shape must be correct
    if data["chunks"]:
        c0 = data["chunks"][0]
        assert "text" in c0 and "score" in c0


def test_synthesise_shape():
    body = {"question": "add two storeys in CA", "top_k": 5}
    r = client.post("/synthesise", json=body)
    assert r.status_code == 200
    data = r.json()
    assert "constraints" in data
    if data["constraints"]:
        c = data["constraints"][0]
        assert c["type"] in ["requirement", "advisory", "conflict"]


def test_map_overlays_empty_without_geom():
    # Should fail validation if missing site_geom
    r = client.post("/map-overlays", json={})
    assert r.status_code in (400, 422)
