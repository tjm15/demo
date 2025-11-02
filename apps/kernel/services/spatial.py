"""Spatial constraint analysis service via PostGIS."""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from db import get_conn

router = APIRouter()

class Constraint(BaseModel):
    type: str
    name: str
    impact: str
    geometry: Optional[dict] = None

class SpatialRequest(BaseModel):
    lat: float
    lng: float
    radius_m: int = 100

@router.post("/constraints", response_model=List[Constraint])
async def get_constraints(req: SpatialRequest):
    """Get spatial constraints for a point buffer using SRID transforms."""
    constraints: List[Constraint] = []
    sql = """
        WITH pt AS (
          SELECT ST_Transform(ST_SetSRID(ST_MakePoint(%s, %s), 4326), 27700) AS g
        )
        SELECT l.layer_type, COALESCE(g.name, l.name) AS name
        FROM layer l
        JOIN layer_geom g ON g.layer_id = l.id
        CROSS JOIN pt
        WHERE ST_DWithin(g.geom, pt.g, %s)
        LIMIT 25
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (req.lng, req.lat, req.radius_m))
            for layer_type, name in cur.fetchall():
                # Impact is heuristic; could be derived from layer_type later
                impact = "high" if layer_type.lower() in {"constraint", "designation"} else "moderate"
                constraints.append(Constraint(type=layer_type, name=name or "", impact=impact))
    return constraints
