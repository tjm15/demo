# Evidence Base Mode: Comprehensive Improvement Plan

**Date**: November 3, 2025  
**Status**: ⚠️ REVISED - Most Features Already Implemented!  
**Goal**: Complete evidence base setup and add remaining integrations

---

## 🎉 KEY FINDINGS: EVIDENCE MODE IS MOSTLY COMPLETE!

After careful code review, **most features marked as "missing" actually exist**:

### ✅ ALREADY IMPLEMENTED (Backend):
- ✅ Vector/semantic search (`search_semantic()` with pgvector)
- ✅ Related evidence finder (`get_related_evidence()`)
- ✅ Version diff comparison (`diff_versions()`)
- ✅ Spatial layer metadata (`get_spatial_metadata()`)
- ✅ Gap analysis endpoint (`/gaps`)
- ✅ Dependency graph (`/graph/dependencies`)
- ✅ Currency alerts (>5yr flagging)

### ✅ ALREADY IMPLEMENTED (Frontend):
- ✅ EvidenceRecord component (comprehensive detail view)
- ✅ EvidenceRecordPanel wrapper
- ✅ EvidenceBrowser with search/filter
- ✅ EvidenceGaps visualization
- ✅ DependencyGraph visualization
- ✅ All panels registered in registry

### ✅ ALREADY IMPLEMENTED (Module):
- ✅ Rich reasoning narrative with token streaming
- ✅ Semantic search integration
- ✅ Gap analysis workflow
- ✅ Evidence categorization by type/authority
- ✅ Currency warnings in output

### ✅ ALREADY IMPLEMENTED (Data):
- ✅ 46 comprehensive evidence items (exceeds 40+ target!)
- ✅ Multiple versions per item
- ✅ Policy links with strength indicators
- ✅ All evidence types covered (housing, economy, environment, infrastructure, spatial, heritage)

### ❌ ACTUALLY MISSING:
1. **Database Setup**: Schema not yet applied, data not seeded, embeddings not generated
2. **Cross-Module Integration**: Evidence not shown in policy/scenario/spatial modes
3. **Advanced Features**: Document parser, cross-authority comparison, upload handler (post-demo)

### 🎯 IMMEDIATE ACTION REQUIRED:
**Phase 0 is CRITICAL**: Apply schema, seed data, generate embeddings, then test everything!

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
- ✅ **Enhanced Retrieval** - Vector search over evidence_chunk embeddings (IMPLEMENTED: search_semantic)
- ✅ **Version Diff** - Compare key findings between versions (IMPLEMENTED: diff_versions)
- ✅ **Spatial Layer Metadata** - Return PostGIS layer details (IMPLEMENTED: get_spatial_metadata)
- ❌ **Upload Handler** - Process file uploads (PDF/CSV/XLSX/ZIP/GeoPackage/Shapefile)
- ✅ **Currency Alerts** - Automated flagging of >5yr old evidence (IMPLEMENTED: in module + UI)

#### Service Enhancements Needed:
- Current search doesn't use embeddings effectively
- No benchmarking against neighboring authorities
- No automated quality/reliability scoring
- No integration with proxy for on-demand fetching

### 2. **Frontend Component Gaps**

#### Missing Components:
- ✅ **EvidenceRecordView** - Detailed item view (IMPLEMENTED: EvidenceRecord.tsx with EvidenceRecordPanel.tsx)
  - ✅ Full metadata (author, publisher, year, source, license)
  - ✅ Key findings (expandable section)
  - ✅ Version timeline with superseded chains
  - ✅ Policy links with strength indicators
  - ✅ Spatial layer preview
  - ✅ Actions: Download, Link to Policy, Refresh Cache
  
- ❌ **EvidenceTimeline** - Standalone version history visualization component
  - Would provide enhanced diff view for comparing versions
  - More visual timeline representation
  - (Note: Basic timeline exists in EvidenceRecord)
  
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

Current module needs enhancements:
- ✅ Rich reasoning narrative (IMPLEMENTED: extensive token streaming)
- ✅ Leverages vector search (IMPLEMENTED: uses search_semantic)
- ✅ Generates helpful summaries (IMPLEMENTED: categorizes by type/authority)
- ❌ No automated cross-validation analysis (needs LLM-based conflict detection)
- ❌ Limited integration with other modules (needs policy/scenario/spatial hooks)

### 4. **Database/Fixtures Status**

- ✅ `seed_evidence.py` has 46 comprehensive items (EXCEEDS target of 40+!)
- ✅ Covers all required evidence types:
  - ✅ Housing: SHMA, HENA, Viability, Housing Delivery, Specialist Housing, G&T
  - ✅ Economy: Employment Land Review, Retail Needs, Town Centre, Economic Strategy
  - ✅ Environment: SFRA, Climate, Biodiversity, Air Quality, Contamination, Green Infrastructure
  - ✅ Infrastructure: Transport, Utilities, Digital, Education, Health
  - ✅ Spatial: SHELAA, Brownfield, Green Belt, Heritage, Design Code
- ✅ evidence_version records included (multiple versions per item)
- ✅ Policy links seeded (with strength indicators)
- ⚠️ Spatial layer links may need verification (evidence_layer table population)

### 5. **Integration Gaps**

- ✅ Evidence panels registered in panel registry (evidence_browser, evidence_record, evidence_gaps, evidence_snapshot)
- ❌ Policy mode doesn't show linked evidence on policy cards
- ❌ Scenario mode doesn't pull parameters from evidence
- ❌ Spatial mode doesn't overlay evidence layers
- ⚠️ Citations exist in module output but could be enhanced with structured citation formatting

---

## 🎯 Revised Implementation Priorities

### Phase 0: Verification & Database Setup (CRITICAL FIRST STEPS)

#### P0.1: Apply Evidence Schema & Seed Data
**Status**: Must verify and execute
**Effort**: 30 minutes
**Files**: `scripts/evidence_schema.sql`, `scripts/seed_evidence.py`, `scripts/embed_evidence_chunks.py`

**Tasks**:
1. Apply evidence_schema.sql to database
2. Run seed_evidence.py (populates 46 items with versions and policy links)
3. Run embed_evidence_chunks.py (generates vector embeddings)
4. Verify tables: evidence, evidence_version, evidence_chunk, evidence_policy_link

#### P0.2: Test Existing Endpoints
**Status**: Verify functionality
**Effort**: 1 hour

**Tasks**:
1. Test `/evidence/search` and `/evidence/search_semantic`
2. Test `/evidence/{id}` detail view
3. Test `/evidence/gaps` gap analysis
4. Test `/evidence/graph/dependencies` dependency graph
5. Test `/evidence/{id}/related` related evidence
6. Test `/evidence/{id}/spatial` spatial metadata

### Phase 1: Critical Gaps (High Priority)

#### P1.1: ~~Evidence Record View~~ (✅ ALREADY EXISTS)
**Status**: COMPLETE - EvidenceRecord.tsx + EvidenceRecordPanel.tsx fully implemented
**Action**: Update documentation only

#### P1.2: ~~Enhanced Evidence Search~~ (✅ ALREADY EXISTS)
**Status**: COMPLETE - search_semantic() with pgvector fully implemented
**Action**: Verify embeddings are generated

#### P1.3: ~~Richer Evidence Module Reasoning~~ (✅ MOSTLY COMPLETE)
**Status**: Extensive reasoning already implemented
**Remaining**: Add LLM-based cross-validation analysis (optional enhancement)

### Phase 2: True Missing Features (Medium Priority)

#### P2.1: Cross-Module Integration
**What**: Connect evidence to policy, scenario, and spatial modes
**Why**: Evidence must inform other planning functions
**Effort**: 4-6 hours
**Files**:
- Policy panels (show linked evidence)
- Scenario module (pull parameters from evidence)
- MapPanel (overlay evidence spatial layers)

**Requirements**:
- Policy cards show evidence badges with links
- Scenario defaults populated from evidence parameters
- Map layers toggleable from evidence browser
- Cross-module citation tracking

#### P2.2: Document Parser Service
**What**: Auto-extract metadata and text from uploaded PDFs
**Why**: Enable future evidence uploads (post-demo enhancement)
**Effort**: 5-6 hours
**Files**:
- `apps/kernel/services/parser.py` (new)
- Add `/evidence/parse` endpoint

**Requirements**:
- PDF text extraction (pdfminer.six)
- OCR fallback for scanned documents (Surya)
- Extract title, author, date, key sections
- Generate initial key_findings summary via LLM
- Store in evidence_chunk for retrieval

#### P2.3: Enhanced EvidenceBrowser UI
**What**: Add advanced filters, sorting, and comparison features
**Why**: Power users need fine-grained control
**Effort**: 3-4 hours
**Files**:
- `website/components/app/panels/EvidenceBrowser.tsx`

**Requirements**:
- Year range slider (dual thumb)
- Currency badges (fresh/stale/superseded with icons)
- Reliability score display (0-100 with color coding)
- Multi-select for bulk operations
- "Compare" mode for side-by-side analysis
- Improved related evidence suggestions display

#### P2.4: Standalone Evidence Timeline Component
**What**: Enhanced version history visualization
**Why**: Better than inline timeline in record view
**Effort**: 3-4 hours
**Files**:
- `website/components/app/panels/EvidenceTimeline.tsx` (new)

**Requirements**:
- Vertical timeline with visual markers
- Interactive diff view for key findings
- Version metadata tooltips
- Download all versions button
- Export timeline as PDF

### Phase 3: Advanced Features (Lower Priority - Post Demo)

#### P3.1: Cross-Authority Comparison
**What**: Fetch and compare evidence from neighboring LPAs
**Why**: Benchmarking is critical for plan robustness
**Effort**: 4-5 hours
**Files**:
- `apps/kernel/services/evidence.py` (add `compare_authorities()`)
- Requires proxy integration

**Requirements**:
- Whitelist of neighboring LPAs
- Proxy fetch for similar evidence types
- Comparison table (our evidence vs theirs)
- Highlight methodology differences

#### P3.2: Automated Cross-Validation
**What**: LLM-based conflict detection across evidence items
**Why**: Catch inconsistencies in housing vs employment projections
**Effort**: 4-5 hours
**Files**:
- New `apps/kernel/services/validation.py`
- `website/components/app/panels/EvidenceCrossValidation.tsx`

**Requirements**:
- Extract numerical targets from multiple evidence items
- Compare projections across topics
- Flag conflicts with severity
- Suggest resolution strategies

#### P3.3: Evidence Refresh Workflow
**What**: Revalidate cached evidence via proxy (ETag/Last-Modified)
**Why**: Keep evidence current automatically
**Effort**: 3-4 hours
**Files**:
- Add `/evidence/{id}/refresh` endpoint
- Proxy integration for revalidation

**Requirements**:
- Check ETag/Last-Modified headers
- Download if changed
- Create new version automatically
- Notify users of updates

#### P3.4: Upload Handler
**What**: Process file uploads (PDF/CSV/XLSX/ZIP/GeoPackage/Shapefile)
**Why**: Allow users to add local evidence
**Effort**: 6-8 hours (post-demo)
**Files**:
- Add `/evidence/upload` endpoint
- File validation and virus scanning
- Parser integration

**Requirements**:
- Multi-file upload with progress
- Auto-parse and extract metadata
- Create evidence_version records
- Link to policies workflow

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

## 📈 Revised Success Metrics

### Quantitative
- [x] 40+ evidence items in fixture database (✅ 46 items ready)
- [ ] Evidence schema applied to database
- [ ] Evidence chunks embedded with vectors
- [x] All 5 evidence panel types functional (✅ components exist)
- [ ] <2s search response time (needs verification)
- [ ] Vector search recall >80% on test queries (needs verification)
- [x] Gap analysis identifies all policy/evidence mismatches (✅ implemented)

### Qualitative
- [ ] Users can discover relevant evidence quickly (needs end-to-end test)
- [x] Evidence provenance is clear and traceable (✅ version/CAS/source tracking)
- [x] Currency alerts are helpful and accurate (✅ >5yr warning implemented)
- [x] Policy-evidence links are intuitive (✅ strength badges)
- [x] Record view provides complete context (✅ comprehensive component)

### Integration
- [ ] Evidence module streams rich reasoning narratives (needs test)
- [ ] Policy mode shows linked evidence (NOT IMPLEMENTED)
- [ ] Scenario mode pulls evidence parameters (NOT IMPLEMENTED)
- [ ] Spatial mode overlays evidence layers (NOT IMPLEMENTED)

---

## 🚀 Revised Rollout Plan

### Day 1: Database Setup & Verification (CRITICAL)
- **Hour 1**: Apply evidence_schema.sql to database
- **Hour 2**: Run seed_evidence.py and verify 46 items inserted
- **Hour 3**: Run embed_evidence_chunks.py for vector search
- **Hour 4**: Test all evidence service endpoints
- **Hours 5-6**: Run evidence module end-to-end tests

### Day 2: Cross-Module Integration
- **Morning**: Add evidence links to policy cards (PolicyEditor component)
- **Afternoon**: Connect scenario module to evidence parameters
- **Evening**: Wire up spatial layer overlays from evidence

### Day 3: UI Enhancements (Optional)
- **Morning**: Enhanced EvidenceBrowser filters (year slider, badges)
- **Afternoon**: Standalone EvidenceTimeline component
- **Evening**: Polish and bug fixes

### Week 2+: Advanced Features (Post-Demo)
- Cross-authority comparison via proxy
- Document parser with OCR
- Automated cross-validation
- Upload handler
- Evidence refresh workflow

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
