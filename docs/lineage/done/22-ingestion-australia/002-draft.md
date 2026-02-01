# Australian WAPIMS Data Ingestion Module

## User Story
As a **petroleum data engineer**,
I want **to ingest RCA documents from Western Australia's WAPIMS portal**,
So that **I can access unique geological data from Australian basins (Carnarvon, Perth, Browse, Canning) and leverage the portal's batch download feature for efficient bulk acquisition**.

## Objective
Implement an `AustraliaModule` that discovers and downloads Routine Core Analysis documents from WAPIMS, with support for the portal's basket/batch download feature to improve efficiency over individual downloads.

## UX Flow

### Scenario 1: Standard Ingestion (Happy Path)
1. User runs `python -m src.ingestion ingest australia --limit 20`
2. System queries WAPIMS for wells with core data across priority basins
3. System filters documents for RCA-related content
4. System downloads documents (individually or via batch)
5. System compresses and stores files with basin-organized paths
6. Result: 20 RCA documents stored in `data/raw/australia/{basin}/`

### Scenario 2: Batch Download Success
1. User runs ingestion with batch-eligible count (≥10 wells)
2. System creates basket and adds documents
3. System submits batch request and polls for completion
4. System receives ZIP, extracts contents, maps to jobs
5. Result: Faster acquisition via single batch download

### Scenario 3: Batch Timeout with Fallback
1. User runs batch ingestion
2. Batch request exceeds BATCH_MAX_WAIT (600s)
3. System logs warning and falls back to individual downloads
4. Result: All documents still acquired, slower but reliable

### Scenario 4: Basin Rotation
1. User runs `--limit 50` across multiple basins
2. System queries Carnarvon, Perth, Browse, Canning, Bonaparte in order
3. System distributes downloads across available basins
4. Result: Geographic diversity in acquired data

## Requirements

### Data Discovery
1. Query WAPIMS API for wells with core data by basin
2. Filter for released/public data only
3. Identify RCA-related documents using keyword matching
4. Support priority ordering of basins (Carnarvon first as major hydrocarbon province)

### Download Capabilities
1. Individual document download with rate limiting (1 req/sec)
2. Basket/batch download for bulk efficiency
3. Automatic fallback from batch to individual on failure
4. ZIP extraction and job mapping for batch results

### Batch/Basket Support
1. Create download basket via API
2. Add multiple documents to basket (up to BATCH_SIZE=10)
3. Submit batch request and receive request ID
4. Poll for completion with configurable interval (30s) and timeout (600s)
5. Download and extract ZIP archive

### Storage & Compression
1. Organize by basin: `data/raw/australia/{basin}/{well_name}.pdf.zst`
2. Zstandard compression for all downloaded files
3. Manifest tracking with full metadata
4. Metrics collection for download statistics

## Technical Approach
- **Module Class:** `AustraliaModule(SourceModule)` with WAPIMS-specific configuration
- **Discovery:** Basin-by-basin search with core data filter
- **Batch System:** Basket creation → add items → submit → poll → extract
- **Fallback:** Try batch first, catch timeout/error, iterate individually
- **Session Management:** Persistent session token for basket operations

## Security Considerations
- WAPIMS is a public government portal; no authentication required for released data
- Some data may require registration (document in README)
- Rate limiting respects portal terms of service (1 req/sec)
- No sensitive credentials stored; session tokens are ephemeral

## Files to Create/Modify
- `src/ingestion/modules/australia.py` — New module implementing AustraliaModule class
- `src/ingestion/modules/__init__.py` — Register australia module
- `tests/ingestion/test_australia.py` — Unit and integration tests
- `tests/fixtures/wapims/` — Mock responses for WAPIMS API
- `docs/ingestion/australia.md` — Module documentation and API notes

## Dependencies
- Core ingestion framework must be in place (SourceModule, DownloadJob)
- Compression utilities (zstandard) available
- httpx for async HTTP operations

## Out of Scope (Future)
- **LAS file ingestion** — Focus on PDFs for MVP, LAS parsing deferred
- **Registration/authentication** — Public data only for now
- **Real-time basin monitoring** — No webhook/notification support
- **Geothermal data** — WAPIMS includes geothermal; petroleum focus only for MVP

## Acceptance Criteria
- [ ] `AustraliaModule` discovers RCA documents from at least 3 basins
- [ ] Individual download works with rate limiting (1 req/sec)
- [ ] Batch download creates basket, submits, and extracts ZIP
- [ ] Batch timeout triggers fallback to individual downloads
- [ ] Files stored at `data/raw/australia/{basin}/{well_name}.pdf.zst`
- [ ] Manifest entries include basin, well_name, permit, operator metadata
- [ ] `--dry-run` lists documents without downloading
- [ ] Unit tests cover basin search, RCA filtering, batch polling
- [ ] Integration test confirms end-to-end workflow

## Definition of Done

### Implementation
- [ ] `AustraliaModule` class with discover and download methods
- [ ] Basket/batch download with polling and timeout
- [ ] Fallback mechanism from batch to individual
- [ ] Basin-organized storage with compression
- [ ] Unit tests written and passing
- [ ] Integration tests with mock WAPIMS server

### Tools
- [ ] CLI supports `ingest australia --limit N` command
- [ ] `--dry-run` flag for discovery without download

### Documentation
- [ ] `docs/ingestion/australia.md` with API notes and usage
- [ ] Update README.md with Australia module in supported sources
- [ ] Document any registration requirements discovered
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Smoke test: `ingest australia --limit 1 --dry-run` succeeds
- [ ] Smoke test: `ingest australia --limit 3` downloads files
- [ ] Manifest validates with `jq` inspection
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Unit Test Coverage
```python
class TestAustraliaModule:
    def test_basin_search_returns_wells(self, mock_response): ...
    def test_rca_document_filtering(self): ...
    def test_basket_creation(self, mock_wapims_server): ...
    def test_batch_polling_success(self, mock_wapims_server): ...
    def test_batch_timeout_triggers_fallback(self, slow_mock_server): ...
    def test_zip_extraction_maps_to_jobs(self, mock_zip_response): ...
    def test_target_path_sanitization(self): ...
```

### Forcing Error States
- **Batch timeout:** Set `BATCH_MAX_WAIT=1` and mock slow response
- **Batch failure:** Mock `state: "failed"` response from status endpoint
- **Individual failure:** Mock 404/500 on document download URL
- **Empty basin:** Mock basin search returning zero wells

### Smoke Test Commands
```bash
# Dry run discovery
python -m src.ingestion ingest australia --limit 1 --dry-run

# Actual download
python -m src.ingestion ingest australia --limit 3

# Verify manifest
cat data/raw/australia/manifest.json | jq '.[] | {well: .metadata.well_name, basin: .metadata.basin}'

# Check compression
ls -la data/raw/australia/Carnarvon/
```