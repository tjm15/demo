"""Map overlays service.

Endpoint:
- POST /map-overlays → GeoJSON FeatureCollection for intersecting designations
"""
from __future__ import annotations
from typing import List, Dict, Any
import json

from fastapi import APIRouter

from db import get_conn
from contracts.schemas import MapOverlaysRequest, MapOverlaysResponse

router = APIRouter()


@router.post("/map-overlays", response_model=MapOverlaysResponse)
async def map_overlays(req: MapOverlaysRequest) -> MapOverlaysResponse:
    features: List[Dict[str, Any]] = []
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                sql = """
                    WITH site AS (
                      SELECT ST_Transform(ST_GeomFromGeoJSON(%s), 27700) AS g
                    )
                    SELECT g.id, l.layer_type, COALESCE(g.name, l.name) AS name,
                           ST_AsGeoJSON(ST_Transform(g.geom, 4326))
                    FROM layer l
                    JOIN layer_geom g ON g.layer_id = l.id
                    CROSS JOIN site
                    WHERE ST_Intersects(g.geom, site.g)
                      AND (%s::text IS NULL OR l.layer_type = ANY(string_to_array(%s, ',')))
                    LIMIT %s
                """
                types = None
                types_csv = None
                if req.types:
                    types = req.types
                    types_csv = ",".join(req.types)
                cur.execute(sql, (json.dumps(req.site_geom.dict()), types_csv, types_csv, req.limit))
                for gid, ltype, name, gj in cur.fetchall():
                    geom = json.loads(gj) if isinstance(gj, str) else gj
                    features.append({
                        "type": "Feature",
                        "id": int(gid),
                        "properties": {
                            "layer_type": ltype,
                            "name": name or "",
                        },
                        "geometry": geom,
                    })
    except Exception:
        # If DB unavailable, return empty FeatureCollection gracefully
        features = []

    return MapOverlaysResponse(features=features)
