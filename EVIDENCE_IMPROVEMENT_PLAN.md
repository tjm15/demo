# Evidence Base Mode: Comprehensive Improvement Plan

**Date**: November 3, 2025  
**Status**: Planning Phase  
**Goal**: Bring Evidence Base Mode to specification compliance and production quality

---

## 📊 Current State Analysis

### ✅ What Exists

**Database Schema** (`scripts/evidence_schema.sql`):
- ✅ Core tables: `evidence`, `evidence_version`, `evidence_chunk`, `evidence_policy_link`, `evidence_layer`, `evidence_cache`
- ✅ Vector embeddings for retrieval (`evidence_chunk.embedding`)
- ✅ Full-text search support (`tsv` column with GIN index)
- ✅ Provenance tracking (versions, CAS hash, source URL, etag, robots.txt)
- ✅ Policy linking with strength indicators (core/supporting/tangential)

**Backend Service** (`apps/kernel/services/evidence.py`):
- ✅ Search endpoint with filters (topic, year, type, status, spatial)
- ✅ Detail view with versions, policy links, and layer references
- ✅ Link to policy endpoint
- ✅ Dependency graph generation
- ✅ Gap analysis (no evidence, stale, weak links)

**Frontend Components**:
- ✅ `EvidenceBrowser.tsx` - Search and filter interface with client-side reranking
- ✅ `EvidenceGaps.tsx` - Gap analysis visualization
- ✅ `EvidenceSnapshot.tsx` - Summary for DM module
- ✅ `DependencyGraph.tsx` - Evidence-policy relationship visualization
- ✅ `AddEvidenceDialog.tsx` - Add evidence UI

**Evidence Module** (`apps/kernel/modules/evidence_module.py`):
- ✅ Basic playbook with intent routing
- ✅ Connects to backend search service

---

## ❌ What's Missing (Gaps vs Specification)

### 1. **Backend Service Gaps**

#### Missing Endpoints:
- ❌ **Document Parser** - Auto-extract metadata from PDFs (OCR via Surya, pdfminer)
- ❌ **AI Summary Assistant** - Generate/regenerate summaries
- ❌ **Cross-Authority Comparison** - Fetch similar studies from neighboring LPAs
- ❌ **Refresh from Source** - Revalidate cached evidence via proxy (ETag/Last-Modified)
- ❌ **Enhanced Retrieval** - Vector search over evidence_chunk embeddings
- ❌ **Version Diff** - Compare key findings between versions
- ❌ **Spatial Layer Metadata** - Return PostGIS layer details (bbox, SRID, feature count)
- ❌ **Upload Handler** - Process file uploads (PDF/CSV/XLSX/ZIP/GeoPackage/Shapefile)
- ❌ **Currency Alerts** - Automated flagging of >5yr old evidence

#### Service Enhancements Needed:
- Current search doesn't use embeddings effectively
- No benchmarking against neighboring authorities
- No automated quality/reliability scoring
- No integration with proxy for on-demand fetching

### 2. **Frontend Component Gaps**

#### Missing Components:
- ❌ **EvidenceRecordView** - Detailed item view showing:
  - Full metadata (author, publisher, year, source, license)
  - Key findings (collapsible/expandable)
  - Version timeline with superseded chains
  - Policy links with strength indicators
  - Spatial layer preview (if applicable)
  - Actions: Download, Link to Policy, Refresh Cache, View in Map
  
- ❌ **EvidenceTimeline** - Version history visualization:
  - Chronological timeline of versions
  - Diff view comparing key findings
  - Superseded/adopted status markers
  - Fetch/upload provenance
  
- ❌ **EvidenceCrossValidation** - Cross-policy validation panel:
  - Show conflicting assumptions across evidence items
  - Highlight housing vs employment projection mismatches
  - Flag evidence gaps for policy clusters

#### Component Enhancements Needed:
- **EvidenceBrowser**:
  - Add year range slider
  - Add "Currency" filter (fresh/stale/unknown)
  - Add reliability score badges
  - Add bulk actions (link multiple to policy)
  - Show related evidence items
  - Add "Compare" mode for side-by-side analysis
  
- **EvidenceGaps**:
  - Add quick-fix actions (suggest evidence from proxy)
  - Show severity scoring
  - Group by policy area/topic
  - Export gap report

### 3. **Evidence Module Gaps**

Current module is too simplistic:
- ❌ No rich reasoning narrative
- ❌ Doesn't leverage vector search
- ❌ Doesn't generate helpful summaries
- ❌ No cross-validation analysis
- ❌ Limited integration with other modules

### 4. **Database/Fixtures Gaps**

- ❌ `seed_evidence.py` has only 6 sample items
- ❌ Missing evidence types from spec:
  - Employment Land Review
  - Retail & Town Centre Needs Assessment
  - Climate change baseline studies
  - Air quality/noise/contamination data
  - Utilities capacity studies
  - Health/Education capacity assessments
  - Open space & recreation studies
  - Equality Impact Assessments
  - Local Industrial Strategy inputs
- ❌ No spatial layers linked to evidence items
- ❌ No evidence_version records (no version history demo)
- ❌ No policy links seeded

### 5. **Integration Gaps**

- ❌ Evidence panels not registered in panel registry
- ❌ Policy mode doesn't show linked evidence
- ❌ Scenario mode doesn't pull parameters from evidence
- ❌ Spatial mode doesn't overlay evidence layers
- ❌ No inline citations in reasoning outputs

---

## 🎯 Implementation Priorities

### Phase 1: Core Functionality (High Priority)

#### P1.1: Evidence Record View (Frontend)
**What**: Build comprehensive detail view for individual evidence items
**Why**: Users need to see full metadata, findings, and provenance
**Effort**: 4-6 hours
**Files**:
- `website/components/app/panels/EvidenceRecordView.tsx` (new)
- Update intent handling to support record selection

**Requirements**:
- Display all metadata fields
- Show key findings (with expand/collapse)
- List all versions with fetch dates
- Show policy links with strength badges
- Show spatial layer info (if present)
- Action buttons: Download, Link to Policy, Refresh, View in Map
- Citation-ready format for copying references

#### P1.2: Enhanced Evidence Search (Backend)
**What**: Add vector search, better filtering, and richer results
**Why**: Current search is basic text matching; needs semantic capabilities
**Effort**: 3-4 hours
**Files**:
- `apps/kernel/services/evidence.py`

**Requirements**:
- Add `search_semantic()` using pgvector cosine similarity
- Combine BM25 + vector hybrid search
- Add `get_related_evidence()` for "similar items"
- Return reliability scores with results
- Add evidence type icons/metadata

#### P1.3: Richer Evidence Module Reasoning (Backend)
**What**: Improve evidence_module.py to generate narrative analysis
**Why**: Current module just routes intents; needs to reason about evidence quality
**Effort**: 4-5 hours
**Files**:
- `apps/kernel/modules/evidence_module.py`

**Requirements**:
- Use LLM to summarize evidence quality for a query
- Identify gaps and suggest solutions
- Generate cross-validation warnings
- Stream reasoning tokens with citations
- Emit multiple coordinated panel intents

#### P1.4: Evidence Fixture Data (Database)
**What**: Expand seed_evidence.py with comprehensive realistic examples
**Why**: Demo needs full coverage of evidence types
**Effort**: 2-3 hours
**Files**:
- `scripts/seed_evidence.py`

**Requirements**:
- Add 30-50 evidence items covering all types
- Include evidence_version records (at least 2 versions for some items)
- Seed evidence_policy_link (link to existing policies)
- Add evidence_layer links (connect to fixture spatial layers)
- Include mix of fresh/stale/draft/adopted/superseded

### Phase 2: Enhanced Features (Medium Priority)

#### P2.1: Version Timeline Component (Frontend)
**What**: Visualize evidence version history
**Why**: Users need to see update trail and superseded evidence
**Effort**: 3-4 hours
**Files**:
- `website/components/app/panels/EvidenceTimeline.tsx` (new)

**Requirements**:
- Chronological timeline visualization
- Diff view for key findings
- Version metadata (fetch date, source, size)
- Status markers (draft/adopted/superseded)

#### P2.2: Document Parser Service (Backend)
**What**: Auto-extract metadata and text from uploaded PDFs
**Why**: Manual entry is error-prone; automation is essential
**Effort**: 5-6 hours
**Files**:
- `apps/kernel/services/evidence.py` (add `parse_document()`)
- May need new `apps/kernel/services/parser.py`

**Requirements**:
- PDF text extraction (pdfminer.six)
- OCR fallback for scanned documents (Surya)
- Extract title, author, date, key sections
- Generate initial key_findings summary
- Store in evidence_chunk for retrieval

#### P2.3: Enhanced EvidenceBrowser (Frontend)
**What**: Add advanced filters, sorting, and comparison features
**Why**: Power users need fine-grained control
**Effort**: 3-4 hours
**Files**:
- `website/components/app/panels/EvidenceBrowser.tsx`

**Requirements**:
- Year range slider
- Currency badges (fresh/stale/unknown)
- Reliability score display
- Multi-select for bulk operations
- "Compare" mode for side-by-side
- Related evidence suggestions

#### P2.4: Gap Analysis Enhancements (Backend + Frontend)
**What**: Smarter gap detection with actionable recommendations
**Why**: Current gaps are reactive; need proactive suggestions
**Effort**: 3-4 hours
**Files**:
- `apps/kernel/services/evidence.py` (enhance `/gaps` endpoint)
- `website/components/app/panels/EvidenceGaps.tsx`

**Requirements**:
- Severity scoring (critical/moderate/minor)
- Suggested evidence from proxy search
- Group gaps by topic/policy area
- Export gap report (PDF/CSV)
- Quick-fix actions (auto-link from proxy)

### Phase 3: Advanced Integration (Lower Priority)

#### P3.1: Cross-Authority Comparison
**What**: Fetch and compare evidence from neighboring LPAs
**Why**: Benchmarking is critical for plan robustness
**Effort**: 4-5 hours
**Files**:
- `apps/kernel/services/evidence.py` (add `compare_authorities()`)

**Requirements**:
- Whitelist of neighboring LPAs
- Proxy fetch for similar evidence types
- Comparison table (our evidence vs theirs)
- Highlight methodology differences

#### P3.2: Policy Mode Integration
**What**: Show linked evidence on policy cards
**Why**: Evidence basis must be visible in policy drafting
**Effort**: 2-3 hours
**Files**:
- Update policy panels to show evidence links
- Add "Add Evidence" button to policy editor

#### P3.3: Scenario Mode Integration
**What**: Pull default parameters from evidence
**Why**: Scenarios should be grounded in evidence
**Effort**: 2-3 hours
**Files**:
- Update scenario module to query evidence service

#### P3.4: Spatial Mode Integration
**What**: Overlay evidence spatial layers on map
**Why**: Visual evidence context is powerful
**Effort**: 3-4 hours
**Files**:
- Add evidence layer toggle to MapPanel
- Connect evidence_layer table to layer service

---

## 🔧 Technical Implementation Details

### Backend Service Enhancements

#### 1. Vector Search Integration
```python
@router.post("/search_semantic", response_model=List[EvidenceItem])
async def search_semantic(req: EvidenceSearchRequest):
    """
    Semantic search using pgvector embeddings.
    Combines vector similarity with metadata filters.
    """
    # Generate embedding for query
    query_embedding = await embed_text(req.q)
    
    # Vector search on evidence_chunk
    query = """
        SELECT DISTINCT e.*, 
               MIN(ec.embedding <=> %s) as similarity
        FROM evidence e
        JOIN evidence_version ev ON ev.evidence_id = e.id
        JOIN evidence_chunk ec ON ec.evidence_version_id = ev.id
        WHERE ec.embedding <=> %s < 0.5
        GROUP BY e.id
        ORDER BY similarity ASC
        LIMIT %s
    """
    # Execute with filters...
```

#### 2. Document Parser
```python
@router.post("/parse")
async def parse_document(file: UploadFile):
    """
    Parse uploaded document and extract metadata + text.
    Returns structured data for evidence creation.
    """
    # Save to temp
    # Extract text via pdfminer.six
    # OCR if needed via Surya
    # Extract metadata (title, author, date)
    # Generate initial summary via LLM
    # Return structured data
```

#### 3. Cross-Authority Comparison
```python
@router.get("/compare/{evidence_id}")
async def compare_with_neighbors(evidence_id: int, authorities: List[str]):
    """
    Fetch similar evidence from neighboring authorities.
    Uses proxy to search their public evidence bases.
    """
    # Get our evidence item
    # For each authority:
    #   - Search proxy for similar type/year
    #   - Extract key findings
    #   - Compare methodologies
    # Return comparison table
```

### Frontend Component Specifications

#### EvidenceRecordView Layout
```
┌─────────────────────────────────────────┐
│ 📄 Evidence Record                       │
├─────────────────────────────────────────┤
│ Title: Westminster SHMA 2024            │
│ Type: SHMA  Year: 2024  Status: Adopted │
│ Author: GL Hearn  Publisher: WCC        │
│ Source: [LOCAL]  Spatial: Yes (3 layers)│
├─────────────────────────────────────────┤
│ Key Findings: [Expandable]              │
│ • 1,200 homes/year needed               │
│ • 45% affordable housing requirement    │
│ • Family housing deficit in zones 2-3   │
├─────────────────────────────────────────┤
│ 📚 Versions (3)                         │
│ v3: Jan 2024 [Current] (upload)         │
│ v2: Jun 2023 [Superseded] (cached)      │
│ v1: Jan 2023 [Draft] (upload)           │
├─────────────────────────────────────────┤
│ 🔗 Policy Links (5)                     │
│ • H1 Housing Target [CORE]              │
│ • H2 Affordable Housing [SUPPORTING]    │
│ • H3 Housing Mix [SUPPORTING]           │
├─────────────────────────────────────────┤
│ 🗺️ Spatial Layers (3)                   │
│ • Housing zones (polygon, EPSG:27700)   │
│ • Priority areas (polygon)              │
│ • Constraint overlay (raster)           │
├─────────────────────────────────────────┤
│ Actions:                                │
│ [Download] [Link to Policy] [Refresh]   │
│ [View in Map] [Generate Citation]       │
└─────────────────────────────────────────┘
```

### Evidence Module Reasoning Flow

**Enhanced Workflow**:
```
1. Parse user intent
   → Determine action: search/validate/gap/compare/link

2. Retrieve evidence
   → Use hybrid search (BM25 + vector)
   → Apply filters (topic, year, status, spatial)
   → Score results by relevance + currency

3. Analyze quality
   → Check currency (>5yr warning)
   → Check completeness (missing topics)
   → Check cross-validation (conflicts)
   → Generate reliability scores

4. Generate narrative
   → Stream reasoning tokens via LLM
   → "Found 12 evidence items for housing..."
   → "Warning: SHMA is 6 years old, update recommended"
   → "Housing target (1,200/yr) conflicts with employment projections (1,500/yr equivalent)"

5. Emit panel intents
   → evidence_browser (with scored results)
   → evidence_gaps (if gaps detected)
   → dependency_graph (if policy context)
   → evidence_record_view (if single item selected)

6. Provide citations
   → Format evidence references
   → Include provenance (URL, fetch date, license)
```

---

## 📋 Database Enhancement Tasks

### 1. Expand Fixtures (seed_evidence.py)

**Target: 40-50 evidence items covering:**

**Housing (10 items)**:
- SHMA (3 authorities)
- HENA (2 authorities)
- Affordable housing viability (2)
- Housing delivery study (1)
- Specialist housing needs (1)
- Gypsy & Traveller accommodation (1)

**Economy (8 items)**:
- Employment land review (3)
- Retail needs assessment (2)
- Town centre health checks (2)
- Economic strategy (1)

**Environment (10 items)**:
- SFRA (3 authorities)
- Climate change baseline (2)
- Biodiversity net gain assessment (2)
- Air quality assessment (1)
- Contaminated land register (1)
- Green infrastructure strategy (1)

**Infrastructure (6 items)**:
- Transport assessment (2)
- Utilities capacity study (1)
- Digital infrastructure strategy (1)
- Education capacity assessment (1)
- Health impact assessment (1)

**Spatial (4 items)**:
- SHELAA (2 authorities)
- Brownfield register (1)
- Green Belt review (1)

**Heritage & Design (2 items)**:
- Heritage assessment (1)
- Design code evidence (1)

### 2. Add Version History

**At least 10 items should have 2-3 versions** showing:
- Original draft
- Consultation version
- Adopted version
- Or: v1 (2020) → v2 (2023) → v3 (2024) showing updates

### 3. Add Policy Links

**Link evidence to existing policy fixtures**:
- Housing evidence → H1, H2, H3 policies
- Transport evidence → T1, T2 policies
- Environment evidence → E1, E2 policies
- Economy evidence → EC1, EC2 policies

**Strength distribution**:
- 40% "core" (primary evidence)
- 40% "supporting" (additional evidence)
- 20% "tangential" (background context)

### 4. Add Spatial Layer Links

**Connect to existing layer fixtures** (if present):
- SFRA → Flood zones layer
- SHELAA → Site allocations layer
- Green Belt review → Green Belt layer
- Heritage assessment → Conservation areas layer

---

## 🧪 Testing Requirements

### Unit Tests
- [ ] Evidence search with various filter combinations
- [ ] Vector search returns relevant results
- [ ] Gap analysis identifies all gap types correctly
- [ ] Dependency graph construction
- [ ] Document parser extracts metadata accurately

### Integration Tests
- [ ] Evidence module → service → database flow
- [ ] Frontend → kernel → evidence service
- [ ] Policy linking workflow
- [ ] Spatial layer overlay
- [ ] Proxy fetch and cache

### End-to-End Scenarios
1. **Search for housing evidence**
   - Enter query "housing need assessment"
   - Filter by year 2020+, topic "housing"
   - Select item, view detail
   - Link to policy H1

2. **Gap analysis**
   - Request gap analysis
   - Review policies with no evidence
   - Suggest evidence from proxy
   - Link suggested evidence

3. **Version timeline**
   - Select evidence with multiple versions
   - View timeline
   - Compare key findings between v1 and v2

4. **Cross-authority comparison**
   - Select Westminster SHMA
   - Compare with Camden & Islington
   - Review methodology differences

---

## 📈 Success Metrics

### Quantitative
- [ ] 40+ evidence items in fixture database
- [ ] All 5 evidence panel types functional
- [ ] <2s search response time
- [ ] Vector search recall >80% on test queries
- [ ] Gap analysis identifies all policy/evidence mismatches

### Qualitative
- [ ] Users can discover relevant evidence quickly
- [ ] Evidence provenance is clear and traceable
- [ ] Currency alerts are helpful and accurate
- [ ] Policy-evidence links are intuitive
- [ ] Record view provides complete context

---

## 🚀 Rollout Plan

### Week 1: Core Functionality
- Days 1-2: EvidenceRecordView component
- Days 3-4: Enhanced backend search & module reasoning
- Day 5: Expanded fixture data

### Week 2: Advanced Features
- Days 1-2: Version timeline component
- Days 3-4: Document parser service
- Day 5: Enhanced EvidenceBrowser & gap analysis

### Week 3: Integration & Polish
- Days 1-2: Policy/scenario/spatial integration
- Days 3-4: Cross-authority comparison
- Day 5: Testing & bug fixes

---

## 📝 Notes & Considerations

### Security
- All proxy fetches must respect allow-list
- Document uploads need virus scanning (future)
- License compliance checks on evidence items

### Performance
- Cache vector embeddings
- Paginate large result sets
- Lazy load evidence_chunk records
- Index optimization for complex queries

### UX
- Progressive disclosure (don't overwhelm)
- Contextual help tooltips
- Quick actions (right-click menus)
- Keyboard shortcuts for power users

### Future Enhancements (Post-MVP)
- Automated evidence refresh scheduling
- Email alerts for stale evidence
- Collaborative evidence annotation
- Evidence quality scoring algorithm
- AI-powered gap prediction
- Automated cross-validation rules engine

---

**Document Version**: 1.0  
**Last Updated**: November 3, 2025  
**Owner**: Development Team  
**Status**: Ready for Implementation
