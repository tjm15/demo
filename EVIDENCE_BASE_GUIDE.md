# Evidence Base Implementation Guide

## Overview

The Evidence Base module provides comprehensive management and analysis of planning evidence items (documents, datasets, spatial layers) with full provenance tracking, version control, and policy linkage capabilities.

## Architecture

### Database Layer

**New Tables** (see `scripts/evidence_schema.sql`):
- `evidence` - Main evidence items catalog
- `evidence_version` - Immutable version history with CAS hashing
- `evidence_chunk` - Text chunks for retrieval with embeddings
- `evidence_policy_link` - Linkage to policies with strength indicators
- `evidence_layer` - Spatial layer associations
- `evidence_cache` - Proxy download cache manifest

### Backend Services

**Evidence Service** (`apps/kernel/services/evidence.py`):
- `/evidence/search` - Search and filter evidence items
- `/evidence/{id}` - Get detailed evidence record
- `/evidence/{id}/link-policy` - Link evidence to policy
- `/evidence/graph/dependencies` - Generate dependency graph
- `/evidence/gaps` - Identify evidence gaps and alerts

**Evidence Module** (`apps/kernel/modules/evidence_module.py`):
- Kernel reasoning module for evidence base workflows
- Handles search, gap analysis, validation, and dependency mapping

### Frontend Components

**Panel Components** (`website/components/app/panels/`):
1. **EvidenceBrowser** - Search and filter interface with scope toggle (DB/Cache/Live)
2. **EvidenceRecord** - Detailed view with versions, policy links, and metadata
3. **EvidenceGaps** - Currency alerts and gap analysis dashboard
4. **DependencyGraph** - Visual graph of evidence↔policy relationships

## Features

### 1. Evidence Search & Classification

- Full-text search across evidence items
- Filter by topic, type, year, status, publisher
- Source badges: LOCAL (upload) | CACHED (proxy) | LIVE (web)
- Topic tags for categorization
- Spatial layer indicators

### 2. Provenance & Versioning

- Content-addressed storage (SHA-256 hashing)
- Immutable version history
- Source URL, ETag, Last-Modified tracking
- License and robots.txt compliance
- Fetch timestamps and file metadata

### 3. Quality & Currency Analysis

- Automatic stale detection (>5 years)
- Methodology flags
- Status tracking (draft/adopted/superseded)
- Reliability scoring

### 4. Policy Integration

- Link evidence to policies with rationale
- Strength indicators: Core | Supporting | Tangential
- Dependency graph visualization
- Gap analysis: policies without evidence

### 5. Spatial Integration

- Associate GeoPackage/Shapefile layers
- PostGIS storage (EPSG:27700)
- Map overlay preview
- Constraint overlay in spatial analysis

## Workflows

### Adding Evidence (Upload)

1. User uploads PDF/CSV/GeoPackage
2. File hashed and stored in CAS
3. New `evidence_version` created
4. Content parsed (OCR for PDFs)
5. Text chunks embedded for retrieval
6. Spatial data imported to PostGIS

### Adding Evidence (URL via Proxy)

1. User provides URL
2. Proxy validates against `allowed_sources.yml`
3. Download and cache with ETag/Last-Modified
4. Extract content and create `evidence_version`
5. Record provenance in `source_provenance` table
6. Ingest chunks with embeddings

### Evidence Validation

1. Run `/evidence/gaps` to identify issues
2. Review no-evidence policies
3. Check stale evidence (>5 years)
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
