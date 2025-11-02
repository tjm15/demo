"""
Python schemas for dashboard diffusion system
Mirrors the TypeScript contracts for backend validation
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum


class Module(str, Enum):
    """Planning module types"""
    EVIDENCE = "evidence"
    POLICY = "policy"
    STRATEGY = "strategy"
    VISION = "vision"
    FEEDBACK = "feedback"
    DM = "dm"


class PatchOp(str, Enum):
    """JSON Patch operation types"""
    ADD = "add"
    REPLACE = "replace"
    REMOVE = "remove"
    TEST = "test"


class PanelData(BaseModel):
    """Panel data structure"""
    id: str = Field(..., min_length=1, description="Unique panel identifier")
    type: str = Field(..., min_length=1, description="Panel type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Panel-specific data")
    timestamp: int = Field(..., gt=0, description="Creation timestamp")
    module: Optional[Module] = Field(None, description="Originating module")

    class Config:
        use_enum_values = True


class PatchOperation(BaseModel):
    """JSON Patch operation"""
    op: PatchOp
    path: str = Field(..., min_length=1, description="JSON pointer path")
    value: Optional[Any] = None
    from_: Optional[str] = Field(None, alias="from", description="Source path for move/copy")

    class Config:
        use_enum_values = True


class PatchEnvelope(BaseModel):
    """Batch of patch operations"""
    action: Literal["patch"] = "patch"
    ops: List[PatchOperation] = Field(..., max_items=20, description="Operations to apply")
    session_id: Optional[str] = None
    batch_id: Optional[str] = None

    @validator('ops')
    def validate_ops_not_empty(cls, v):
        if not v:
            raise ValueError("ops list cannot be empty")
        return v


class Intent(BaseModel):
    """High-level intent for UI updates"""
    action: str = Field(..., min_length=1)
    panel: Optional[str] = None
    id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class DashboardState(BaseModel):
    """Complete dashboard state"""
    panels: List[PanelData] = Field(default_factory=list)
    module: Module
    session_id: Optional[str] = None
    safe_mode: bool = False
    error_count: int = Field(0, ge=0)

    class Config:
        use_enum_values = True


# Panel-specific schemas

class PolicyItem(BaseModel):
    """Single policy reference"""
    id: str
    title: str
    text: Optional[str] = None
    relevance: Optional[float] = Field(None, ge=0, le=1)
    source: Optional[str] = None


class ApplicablePoliciesData(BaseModel):
    """Data for applicable_policies panel"""
    policies: List[PolicyItem]


class CaseItem(BaseModel):
    """Single precedent case"""
    ref: str
    title: str
    decision: Optional[str] = None
    relevance: Optional[float] = Field(None, ge=0, le=1)
    url: Optional[str] = None


class PrecedentsData(BaseModel):
    """Data for precedents panel"""
    cases: List[CaseItem]


class IssueWeight(str, Enum):
    """Issue severity levels"""
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class IssueItem(BaseModel):
    """Single planning issue"""
    id: str
    topic: str
    concern: str
    policies: List[str]
    weight: Optional[IssueWeight] = None

    class Config:
        use_enum_values = True


class KeyIssuesMatrixData(BaseModel):
    """Data for key_issues_matrix panel"""
    issues: List[IssueItem]


class FactorWeight(str, Enum):
    """Planning balance weight levels"""
    SUBSTANTIAL = "substantial"
    MODERATE = "moderate"
    LIMITED = "limited"


class BalanceFactor(BaseModel):
    """Single benefit or harm factor"""
    factor: str
    weight: FactorWeight
    description: Optional[str] = None

    class Config:
        use_enum_values = True


class BalanceOutcome(str, Enum):
    """Overall planning balance outcome"""
    APPROVE = "approve"
    REFUSE = "refuse"
    MARGINAL = "marginal"


class PlanningBalanceData(BaseModel):
    """Data for planning_balance panel"""
    benefits: List[BalanceFactor]
    harms: List[BalanceFactor]
    overall: Optional[BalanceOutcome] = None

    class Config:
        use_enum_values = True


class DecisionRecommendation(str, Enum):
    """Decision types"""
    APPROVE = "approve"
    REFUSE = "refuse"
    DEFER = "defer"


class DraftDecisionData(BaseModel):
    """Data for draft_decision panel"""
    recommendation: DecisionRecommendation
    reasons: List[str]
    conditions: Optional[List[str]] = None
    informatives: Optional[List[str]] = None

    class Config:
        use_enum_values = True


class ConstraintSeverity(str, Enum):
    """Constraint severity levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Constraint(BaseModel):
    """Single site constraint"""
    type: str
    description: str
    severity: Optional[ConstraintSeverity] = None

    class Config:
        use_enum_values = True


class EvidenceSnapshotData(BaseModel):
    """Data for evidence_snapshot panel"""
    site: Optional[Dict[str, Any]] = None
    constraints: List[Constraint]
    docs: Optional[List[Dict[str, str]]] = None


# Panel type to data schema mapping
PANEL_DATA_SCHEMAS = {
    "applicable_policies": ApplicablePoliciesData,
    "precedents": PrecedentsData,
    "key_issues_matrix": KeyIssuesMatrixData,
    "planning_balance": PlanningBalanceData,
    "draft_decision": DraftDecisionData,
    "evidence_snapshot": EvidenceSnapshotData,
}


def validate_panel_data(panel_type: str, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate panel data against its schema
    Returns (is_valid, error_message)
    """
    schema_class = PANEL_DATA_SCHEMAS.get(panel_type)
    if not schema_class:
        return False, f"Unknown panel type: {panel_type}"
    
    try:
        schema_class(**data)
        return True, None
    except Exception as e:
        return False, str(e)


def validate_panel(panel: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate a complete panel object
    Returns (is_valid, error_message)
    """
    try:
        panel_obj = PanelData(**panel)
        return validate_panel_data(panel_obj.type, panel_obj.data)
    except Exception as e:
        return False, str(e)


# --- Retrieval & Synthesis API Schemas (Planner pattern) ---

class GeoJSONGeometry(BaseModel):
    """Minimal GeoJSON geometry representation (Polygon/MultiPolygon/Point/LineString)."""
    type: Literal["Point", "LineString", "Polygon", "MultiPolygon"]
    coordinates: Any


class RetrieveRequest(BaseModel):
    """Input for /retrieve: question + optional site geometry and top_k."""
    question: str = Field(..., min_length=1)
    site_geom: Optional[GeoJSONGeometry] = None
    lpa_code: Optional[str] = None
    top_k: int = Field(15, ge=1, le=100)


class ChunkItem(BaseModel):
    """A retrieved chunk (policy clause)."""
    chunk_id: str
    policy_id: Optional[str] = None
    policy_title: Optional[str] = None
    para_ref: Optional[str] = None
    text: str
    page: Optional[int] = None
    score: float
    bm25: Optional[float] = None
    sim: Optional[float] = None
    tags: Optional[List[str]] = None


class GraphContext(BaseModel):
    """Neighborhood graph around retrieved policies."""
    nodes: List[str] = []
    edges: List[Dict[str, str]] = []  # {src, dst, relation}


class RetrieveResponse(BaseModel):
    chunks: List[ChunkItem]
    graph: GraphContext
    designations: Optional[List[str]] = None


class SynthesiseRequest(BaseModel):
    """Input for /synthesise: site + question, optionally seeds from /retrieve."""
    question: str
    site_geom: Optional[GeoJSONGeometry] = None
    lpa_code: Optional[str] = None
    seeds: Optional[List[str]] = None  # chunk_ids
    top_k: int = Field(12, ge=1, le=50)


class ConstraintItem(BaseModel):
    """A synthesised constraint with explanation."""
    type: Literal["requirement", "advisory", "conflict"]
    title: str
    clause: Optional[str] = None
    source_policy: Optional[str] = None
    certainty: float = Field(0.5, ge=0, le=1)
    why: Optional[str] = None
    refs: Optional[List[str]] = None  # para ids/refs


class SynthesiseResponse(BaseModel):
    constraints: List[ConstraintItem]
    graph: Optional[GraphContext] = None


class ExplainRequest(BaseModel):
    items: List[ConstraintItem]
    site_geom: Optional[GeoJSONGeometry] = None
    question: Optional[str] = None


class ExplainItem(BaseModel):
    item: ConstraintItem
    rationale: str


class ExplainResponse(BaseModel):
    explanations: List[ExplainItem]


class MapOverlaysRequest(BaseModel):
    site_geom: GeoJSONGeometry
    types: Optional[List[str]] = None  # e.g., ["conservation_area", "flood"]
    limit: int = Field(25, ge=1, le=200)


class MapOverlaysResponse(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[Dict[str, Any]]
