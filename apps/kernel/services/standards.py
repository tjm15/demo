"""Design standards checking service using policy_test table where possible."""
from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel
from db import get_conn

router = APIRouter()

class StandardCheck(BaseModel):
    standard: str
    required: str
    provided: str
    compliant: bool
    notes: Optional[str] = None

class StandardsRequest(BaseModel):
    proposal: dict

@router.post("/check", response_model=List[StandardCheck])
async def check_standards(req: StandardsRequest):
    """Check proposal against design standards stored in policy_test.
    Heuristics: map known test names to proposal keys and compare by operator.
    """
    proposal = req.proposal or {}
    checks: List[StandardCheck] = []

    # Gather tests
    tests = []
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT test_name, operator, value, unit FROM policy_test")
            tests = cur.fetchall()

    # Simple key mapping
    key_map = {
        "density": ["density", "units_per_hectare", "dph"],
        "height": ["height_storeys", "storeys"],
        "parking": ["parking_spaces_per_unit", "parking_per_unit"],
    }

    def find_value(keys):
        for k in keys:
            if k in proposal:
                return proposal[k]
        return None

    for name, op, val, unit in tests:
        lname = (name or '').lower()
        if "density" in lname:
            pval = find_value(key_map["density"])  # expected numeric
        elif "height" in lname:
            pval = find_value(key_map["height"])  # storeys
        elif "parking" in lname:
            pval = find_value(key_map["parking"])  # spaces per unit
        else:
            pval = None

        required = f"{op} {val} {unit or ''}".strip()
        provided = "n/a" if pval is None else str(pval)

        compliant = None
        notes = None
        try:
            if pval is not None and val is not None and op:
                if op == ">=":
                    compliant = float(pval) >= float(val)
                elif op == "<=":
                    compliant = float(pval) <= float(val)
                elif op in ("=", "=="):
                    compliant = float(pval) == float(val)
                else:
                    notes = f"Unsupported operator {op}"
        except Exception:
            notes = "Comparison failed"

        checks.append(StandardCheck(
            standard=name or "standard",
            required=required,
            provided=provided,
            compliant=bool(compliant) if compliant is not None else False,
            notes=notes,
        ))

    return checks
