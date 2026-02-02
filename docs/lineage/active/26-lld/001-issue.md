# Issue #26: UK National Data Repository Ingestion Module

# UK National Data Repository Ingestion Module

## User Story
As a **data engineer building the RCA training corpus**,
I want **to ingest well data from the UK National Data Repository**,
So that **the model has exposure to North Sea offshore, deep-water, and diverse lithology types not available in US sources**.

## Objective
Implement a UK NDR ingestion module that performs quadrant-by-quadrant well discovery and per-well document enumeration to download RCA reports from the UK Continental Shelf.

## UX Flow

### Scenario 1: Successful Quadrant Discovery and Download
1. User runs `python -m src.ingestion ingest uk --limit 10`
2. System searches priority quadrants (9, 16, 22, 30, 21, 15) for wells with core data
3. System enumerates documents per well, filtering for RCA-related content
4. System downloads PDFs with conservative rate limiting (1 req/2 sec)
5. Result: 10 RCA documents saved to `data/raw/uk/Q{n}/` with manifest updated

### Scenario 2: Restricted Well Handling
1. User runs ingestion targeting a quadrant with mixed access
2. System encounters 403 Forbidden on specific wells
3. System logs the restriction, skips the well, and continues
4. Result: Partial success with skip reasons logged in metrics

### Scenario 3: Rate Limiting Response
1. System receives 429 Too Many Requests from NDR
2. System applies exponential backoff (starting at 30 seconds)
3. System resumes after backoff period
4. Result: Download continues without permanent failure

### Scenario 4: Dry Run Mode
1. User runs `python -m src.ingestion ingest uk --limit 5 --dry-run`
2. System discovers wells and documents without downloading
3. System prints discovery results and estimated download size
4. Result: User can preview what would be downloaded

## Requirements

### Discovery & Search
1. Search wells by quadrant with priority ordering (Central North Sea first)
2. Filter for wells with released/public status only
3. Filter for wells with core data indicators
4. Support well ID formats: "9/13a-A1", license blocks, quadrant/block

### Document Handling
1. Per-well document enumeration (granular lookups, no bulk API)
2. RCA document identification via keywords: core analysis, rca, routine core, porosity, permeability, core report, petrophysical, reservoir
3. Download with compression (zstd)
4. SHA256 verification of downloaded content

### Rate Limiting & Resilience
1. Conservative rate limiting: 1 request per 2 seconds minimum
2. Extended timeout (60s) for international requests
3. Graceful 403 handling (log and skip restricted wells)
4. Exponential backoff on 429 responses
5. Retry transient failures (5xx, timeouts)

### Storage & Data Residency
1. Path structure: `data/raw/uk/Q{quadrant}/{sanitized_well_id}.pdf.zst`
2. **Data Residency: Local-Only/No External Transmission** â€” All downloaded data remains on the local development machine or designated internal storage. No data is transmitted to external services, cloud endpoints, or third-party systems.
3. Manifest with full metadata including quadrant, block, operator, spud date
4. Metrics tracking: downloaded, skipped, skip reasons

### Volume Estimate
1. **Estimated corpus size:** ~50-100 GB total for priority quadrants (9, 16, 22, 30, 21, 15)
2. **Per-document average:** 2-5 MB per RCA PDF (compressed: 1.5-3.5 MB with zstd)
3. **Estimated document count:** 10,000-20,000 RCA documents across priority quadrants
4. **Initial MVP target:** 500-1,000 documents (~2-5 GB) with `--limit` parameter

## Technical Approach
- **UKModule class:** Extends `SourceModule` base class with UK-specific discovery logic
- **Quadrant search:** POST to NDR search API with quadrant/status/hasCore filters
- **Document enumeration:** GET per-well document list, filter for RCA keywords
- **Rate limiter:** Async sleep between requests, configurable via `rate_limit` attribute
- **Path sanitization:** Replace `/` and spaces in well IDs for filesystem compatibility
- **Static fixtures:** Saved HTML/JSON responses committed to `tests/fixtures/uk/` for offline development and CI testing

## Security Considerations
- Public data only - filtering for RELEASED status wells
- No authentication credentials stored (public access portal)
- Rate limiting respects server capacity and terms of service
- No personally identifiable information in well metadata

## Files to Create/Modify
- `src/ingestion/modules/uk.py` â€” New UK NDR module implementation
- `src/ingestion/modules/__init__.py` â€” Register UKModule in module registry
- `tests/ingestion/test_uk.py` â€” Unit tests with mocked responses
- `tests/ingestion/test_uk_integration.py` â€” Integration tests with mock server
- `tests/fixtures/uk/quadrant_search_response.json` â€” Static fixture for quadrant search
- `tests/fixtures/uk/well_documents_response.json` â€” Static fixture for document enumeration
- `tests/fixtures/uk/sample_rca.pdf` â€” Sample RCA PDF for download testing
- `docs/ingestion/uk-ndr.md` â€” Documentation of UK data source and API

## Dependencies
- Core ingestion framework must be implemented (SourceModule base class, DownloadJob) â€” See #TBD (verify "Done" status before starting)
- Compression utilities (zstd) available
- httpx async client configured

## Out of Scope (Future)
- **Registration/auth flow** â€” Deferred until we confirm if required for any data
- **Celtic Sea and Atlantic Margin quadrants** â€” Focus on North Sea for MVP
- **LAS file ingestion** â€” PDF RCA reports only for now
- **Real-time well status monitoring** â€” One-time ingestion, not continuous sync

## Acceptance Criteria
- [ ] `UKModule` class implements `discover_documents()` returning `DownloadJob` list
- [ ] Quadrant search filters for released wells with core data
- [ ] Document filtering correctly identifies RCA-related documents
- [ ] Rate limiting enforces minimum 2-second delay between requests
- [ ] 403 responses result in skip (not failure) with reason logged
- [ ] Downloaded files saved to `data/raw/uk/Q{n}/{well}.pdf.zst`
- [ ] Manifest contains all required metadata fields
- [ ] `--dry-run` mode discovers without downloading
- [ ] International timeout (60s) applied to all requests
- [ ] Static fixtures committed to `tests/fixtures/uk/` for offline testing

## Definition of Done

### Implementation
- [ ] `UKModule` class with all methods implemented
- [ ] Priority quadrant ordering (9, 16, 22, 30, 21, 15)
- [ ] Error classification for 403/404/429 responses
- [ ] Unit tests written and passing
- [ ] Static fixtures created and committed

### Tools
- [ ] CLI supports `ingest uk` command with `--limit` and `--dry-run`
- [ ] Metrics output includes UK-specific fields (quadrant, skip reasons)

### Documentation
- [ ] `docs/ingestion/uk-ndr.md` documents API structure and usage
- [ ] README updated with UK as available data source
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Smoke test: `python -m src.ingestion ingest uk --limit 1 --dry-run` succeeds
- [ ] Smoke test: `python -m src.ingestion ingest uk --limit 3` downloads 3 files
- [ ] Manifest validation: `cat data/raw/uk/manifest.json | jq .` shows valid structure

## Testing Notes

### Unit Test Coverage
```python
def test_quadrant_search_returns_wells(self, mock_response): ...
def test_well_id_sanitization(self):  # "9/13a-A1" â†’ "9_13a_A1"
def test_rca_document_filtering(self):  # Keywords match
def test_conservative_rate_limiting(self):  # 2+ sec between calls
def test_graceful_403_handling(self, mock_response):  # Skip, don't fail
def test_timeout_handling(self, slow_mock_response):  # 60s timeout
```

### Static Fixtures
Tests use committed fixtures from `tests/fixtures/uk/`:
- `quadrant_search_response.json` â€” Mock NDR search API response
- `well_documents_response.json` â€” Mock well document list
- `sample_rca.pdf` â€” Binary fixture for download verification

### Integration Test Setup
Mock server should support:
- `/api/wells/search` POST endpoint returning well list
- `/api/wells/{id}/documents` GET endpoint returning document list
- `/api/documents/{id}` GET endpoint returning PDF content
- Configurable 403/429 responses for specific wells

### Manual Verification
```bash
# Dry run - verify discovery works
python -m src.ingestion ingest uk --limit 1 --dry-run

# Small batch download
python -m src.ingestion ingest uk --limit 3

# Verify manifest structure
cat data/raw/uk/manifest.json | jq '.[] | {well_id, quadrant, operator}'

# Verify compression
ls -la data/raw/uk/Q9/
```

---

**Labels:** `ingestion`, `scraper`, `uk-ndr`
**Size:** L (Large)

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-01-31 | **Reviews:** 2</sub>
