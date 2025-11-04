# Evidence Base - API Reference & Usage Guide

> **Note**: For the complete Evidence Base specification and architecture, see [AGENTS.md](AGENTS.md#evidence-base-mode).  
> This guide focuses on API endpoints, component usage, and practical implementation details.

## Quick Links

- [Database Setup](#database-setup)
- [API Endpoints](#api-endpoints)
- [Frontend Components](#frontend-components)
- [Example Workflows](#example-workflows)
- [For implementation status and roadmap, see [EVIDENCE_IMPROVEMENT_PLAN.md](EVIDENCE_IMPROVEMENT_PLAN.md)

---

## Database Setup

### Apply Schema

```bash
# Run the setup script
./scripts/setup_evidence.sh

# Or manually:
psql -U tpa -d tpa -f scripts/evidence_schema.sql
```

### Seed Sample Data

```bash
cd scripts
python seed_evidence.py  # Loads 46 evidence items with versions
python embed_evidence_chunks.py  # Generates vector embeddings
```

### Verify Installation

```bash
psql -U tpa -d tpa -c "SELECT COUNT(*) FROM evidence;"
psql -U tpa -d tpa -c "SELECT COUNT(*) FROM evidence_chunk WHERE embedding IS NOT NULL;"
```

---

## API Endpoints

Base URL: `http://localhost:8081/evidence`

### 1. Search Evidence

**Endpoint**: `POST /evidence/search`

**Request Body**:
```json
{
  "q": "housing needs assessment",
  "topic": ["housing"],
  "type": "SHMA",
  "year_min": 2020,
  "year_max": 2024,
  "status": "adopted",
  "publisher": "Westminster",
  "spatial_only": false,
  "scope": "db",
  "limit": 20
}
```

**Response**:
```json
{
  "items": [
    {
      "id": 1,
      "title": "Westminster Strategic Housing Market Assessment 2024",
      "type": "SHMA",
      "topic_tags": ["housing", "economy"],
      "geographic_scope": "Westminster City Council",
      "author": "Turley Associates",
      "publisher": "Westminster City Council",
      "year": 2024,
      "source_type": "upload",
      "status": "adopted",
      "key_findings": "Identified need for 985 homes per annum...",
      "created_at": "2024-11-01T10:00:00Z"
    }
  ],
  "total": 1,
  "scope": "db"
}
```

**Scope Values**:
- `"db"` - Local database only
- `"db_cache"` - Database + proxy cache
- `"db_cache_live"` - Database + cache + live web fetch

---

### 2. Semantic Search

**Endpoint**: `POST /evidence/search_semantic`

Uses vector embeddings for similarity search.

**Request Body**:
```json
{
  "q": "flood risk in urban areas",
  "limit": 10
}
```

**Response**: Same structure as `/search`

---

### 3. Get Evidence Detail

**Endpoint**: `GET /evidence/{id}`

**Response**:
```json
{
  "id": 1,
  "title": "Westminster SHMA 2024",
  "type": "SHMA",
  "versions": [
    {
      "version_id": 1,
      "created_at": "2024-11-01T10:00:00Z",
      "source_url": "https://...",
      "cas_hash": "sha256:abc123...",
      "file_size": 2048576,
      "mime_type": "application/pdf"
    }
  ],
  "policy_links": [
    {
      "policy_id": 15,
      "policy_ref": "H1",
      "policy_title": "Housing Supply",
      "strength": "core",
      "rationale": "Primary evidence base for housing targets"
    }
  ],
  "spatial_layers": [],
  "related_evidence": [2, 5, 8]
}
```

---

### 4. Gap Analysis

**Endpoint**: `GET /evidence/gaps`

**Response**:
```json
{
  "no_evidence": [
    {
      "policy_id": 23,
      "policy_ref": "ENV3",
      "policy_title": "Air Quality",
      "issue": "No evidence items linked"
    }
  ],
  "stale_evidence": [
    {
      "policy_id": 15,
      "evidence_id": 3,
      "evidence_title": "Housing Study 2018",
      "age_years": 6,
      "issue": "Evidence older than 5 years"
    }
  ],
  "weak_links": [
    {
      "policy_id": 42,
      "evidence_count": 2,
      "max_strength": "tangential",
      "issue": "Only weak evidence links"
    }
  ]
}
```

---

### 5. Dependency Graph

**Endpoint**: `GET /evidence/graph/dependencies?policy_id=15`

**Response**:
```json
{
  "nodes": [
    {
      "id": "evidence_1",
      "type": "evidence",
      "label": "Westminster SHMA 2024",
      "metadata": {...}
    },
    {
      "id": "policy_15",
      "type": "policy",
      "label": "H1: Housing Supply",
      "metadata": {...}
    }
  ],
  "edges": [
    {
      "from": "evidence_1",
      "to": "policy_15",
      "strength": "core",
      "rationale": "..."
    }
  ]
}
```

---

### 6. Link Evidence to Policy

**Endpoint**: `POST /evidence/{id}/link-policy`

**Request Body**:
```json
{
  "policy_id": 15,
  "rationale": "Core evidence for housing targets",
  "strength": "core"
}
```

**Strength Values**: `"core"` | `"supporting"` | `"tangential"`

---

### 7. Get Related Evidence

**Endpoint**: `GET /evidence/{id}/related?limit=5`

Returns evidence items with similar topics/types.

---

### 8. Compare Versions

**Endpoint**: `GET /evidence/{id}/versions/diff?from_version=1&to_version=2`

**Response**:
```json
{
  "changes": {
    "key_findings": {
      "old": "985 homes per annum",
      "new": "1020 homes per annum"
    },
    "year": {
      "old": 2023,
      "new": 2024
    }
  }
}
```

---

### 9. Spatial Layer Metadata

**Endpoint**: `GET /evidence/{id}/spatial`

**Response**:
```json
{
  "layers": [
    {
      "layer_name": "flood_zones",
      "table_name": "layer_flood_zones",
      "bbox": [500000, 150000, 510000, 160000],
      "srid": 27700,
      "feature_count": 127
    }
  ]
}
```

---

## Frontend Components

### EvidenceBrowser

**Props**:
```typescript
{
  items: EvidenceItem[];
  onSelectItem: (item: EvidenceItem) => void;
  onSearch: (query: string, filters: Filters) => void;
}
```

**Features**:
- Search bar with real-time filtering
- Topic tag chips (multi-select)
- Year range filter
- Status badges (adopted/draft/superseded)
- Source badges (LOCAL/CACHED/LIVE)
- Currency alerts (stale evidence warnings)

---

### EvidenceRecord

**Props**:
```typescript
{
  evidenceId: number;
  data?: EvidenceDetail;
}
```

**Sections**:
- Metadata (title, author, year, type)
- Key findings (expandable)
- Version timeline
- Policy links with strength badges
- Spatial layer references
- Actions (download, link to policy, refresh)

---

### EvidenceGaps

**Props**:
```typescript
{
  gaps: GapAnalysis;
}
```

**Displays**:
- **No Evidence** (red): Policies with no linked evidence
- **Stale Evidence** (orange): Evidence >5 years old
- **Weak Links** (amber): Only tangential evidence

---

### DependencyGraph

**Props**:
```typescript
{
  nodes: GraphNode[];
  edges: GraphEdge[];
}
```

**Visualization**:
- Force-directed graph layout
- Purple nodes = evidence items
- Blue nodes = policies
- Edge colors by strength (green=core, blue=supporting, gray=tangential)

---

## Example Workflows

### 1. Search Evidence
4. Validate weak/tangential links
5. Request updates or add new evidence

### Linking to Policies

1. Select evidence item
2. Choose policy from list
3. Add rationale and strength (core/supporting/tangential)
4. Link recorded in `evidence_policy_link`
5. Dependency graph auto-updates

## Security & Compliance

### Allowed Sources (`apps/proxy/allowed_sources.yml`)

```yaml
allowed_domains:
  - gov.uk
  - london.gov.uk
  - planningportal.co.uk
  - ons.gov.uk
  - environment-agency.gov.uk
```

### Module-Aware Citations

Evidence module restricts citations to:
- GOV.UK (central government)
- LPA domains
- DLUHC, ONS, EA (agencies)
- Planning Inspectorate

### Provenance Audit

Every fetch/download recorded with:
- Source URL and domain
- Fetch timestamp
- SHA-256 hash
- Robots.txt compliance
- License terms

## Database Setup

```bash
# Apply base schema
psql -U tpa -d tpa -f scripts/schema.sql

# Apply evidence schema
psql -U tpa -d tpa -f scripts/evidence_schema.sql

# Grant permissions (already in script)
```

## API Examples

### Search Evidence

```bash
curl -X POST http://localhost:8081/evidence/search \
  -H "Content-Type: application/json" \
  -d '{
    "q": "housing needs assessment",
    "topic": ["housing"],
    "year_min": 2020,
    "scope": "db",
    "limit": 10
  }'
```

### Get Evidence Detail

```bash
curl http://localhost:8081/evidence/42
```

### Link to Policy

```bash
curl -X POST http://localhost:8081/evidence/42/link-policy \
  -H "Content-Type: application/json" \
  -d '{
    "policy_id": 15,
    "rationale": "SHMA provides core housing need figures",
    "strength": "core"
  }'
```

### Gap Analysis

```bash
curl http://localhost:8081/evidence/gaps
```

### Dependency Graph

```bash
curl "http://localhost:8081/evidence/graph/dependencies?policy_id=15"
```

## Frontend Integration

### Using EvidenceBrowser

```tsx
import { EvidenceBrowser } from './panels/EvidenceBrowser';

<EvidenceBrowser
  items={evidenceItems}
  onSelectItem={(item) => showEvidenceRecord(item)}
  onSearch={(query, filters) => fetchEvidence(query, filters)}
/>
```

### Panel Intents from Kernel

```python
# From evidence_module.py
intents.append({
    "type": "intent",
    "data": {
        "action": "show_panel",
        "panel": "evidence_browser",
        "id": f"evidence_browser_{timestamp}",
        "data": {
            "items": [],  # Frontend fetches via API
            "filters": {"topics": ["housing"], "scope": "db"}
        }
    }
})
```

## Testing

```bash
# Test evidence service endpoints
pytest tests/test_evidence_service.py

# Test evidence module reasoning
pytest tests/test_evidence_module.py

# Frontend component tests
cd website && pnpm test -- panels/Evidence
```

## Maintenance

### Refresh Evidence from Source

```bash
# Re-fetch cached URLs (checks ETag/Last-Modified)
curl -X POST http://localhost:8081/evidence/42/refresh
```

### Garbage Collection

```bash
# Remove orphaned CAS blobs (admin only)
python scripts/evidence_gc.py --dry-run
```

## Roadmap

- [ ] Automatic refresh jobs (cron)
- [ ] Neighbour LPA benchmarking
- [ ] Evidence templates (SHMA, SFRA, etc.)
- [ ] Bulk import from data packs
- [ ] Advanced spatial overlay queries
- [ ] ML-powered gap detection
- [ ] Citation extraction from PDFs
- [ ] Evidence quality scoring model

## References

- **Spec**: `AGENTS.md` (Evidence Base section)
- **Schema**: `scripts/evidence_schema.sql`
- **Service**: `apps/kernel/services/evidence.py`
- **Module**: `apps/kernel/modules/evidence_module.py`
- **Components**: `website/components/app/panels/Evidence*.tsx`
- **Contracts**: `contracts/schemas.ts` (Evidence*DataSchema)
