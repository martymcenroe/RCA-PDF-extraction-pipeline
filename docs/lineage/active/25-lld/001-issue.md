---
repo: martymcenroe/RCA-PDF-extraction-pipeline
issue: 25
url: https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/issues/25
fetched: 2026-02-05T15:31:33.904792Z
---

# Issue #25: Texas University Lands Data Ingestion Module

# Texas University Lands Data Ingestion Module

## User Story
As a **data engineer**,
I want **an ingestion module that acquires well data from Texas University Lands**,
So that **I can systematically collect RCA documents from the Permian Basin, one of the richest sources of routine core analysis data in West Texas**.

## Objective
Implement a `TexasModule` that queries the Texas University Lands portal for well documents, filters for RCA-related content, and downloads with appropriate rate limiting following the core ingestion framework pattern.

## UX Flow

### Scenario 1: Standard Ingestion Run
1. User runs `python -m src.ingestion ingest texas --limit 50`
2. Module queries priority counties (Andrews, Ector, Winkler, etc.) for wells with core data
3. System filters documents for RCA-related keywords
4. Downloads proceed at 1 req/sec rate limit
5. Result: Documents stored in `data/raw/texas/{county}/` with manifest updated

### Scenario 2: Dry Run Discovery
1. User runs `python -m src.ingestion ingest texas --limit 10 --dry-run`
2. Module discovers documents without downloading
3. System outputs list of documents that would be downloaded
4. Result: User can preview ingestion scope before committing

### Scenario 3: Document Access Restricted
1. User initiates ingestion
2. Portal returns 403 for specific document
3. System logs warning, skips document, continues processing
4. Result: Partial success with clear audit trail of skipped items

### Scenario 4: Portal Session Timeout
1. Ingestion running for extended period
2. Portal session expires mid-run
3. System detects auth failure, re-authenticates gracefully
4. Result: Ingestion continues without user intervention

## Requirements

### Data Discovery
1. Query wells by county from priority list (Andrews, Ector, Winkler, Ward, Crane, Upton, Reagan, Irion, Crockett, Pecos)
2. Filter wells that have core data available
3. Retrieve document listings for each well
4. Identify RCA-related documents via keyword matching (core analysis, rca, porosity, permeability, routine)

### Rate Limiting & Resilience
1. Enforce 1 request/second rate limit (polite crawling)
2. Retry failed requests with exponential backoff (max 3 attempts)
3. Implement circuit breaker for source-level failures
4. Checkpoint after each successful download for resumability

### Storage & Compression
1. Store files at `data/raw/texas/{county}/{api_number}.pdf.zst`
2. Compress with zstd following framework conventions
3. Update `manifest.json` with full metadata after each download
4. Track metrics in `metrics.json`
5. **Data Residency:** All downloaded data stored LOCAL-ONLY in the project's `data/raw/texas/` directory. No cloud transmission or external storage.

### Metadata Capture
1. Capture state, county, API number, well name, formation
2. Record document type and original filename
3. Store download timestamp and checksums
4. Preserve source URL for provenance

### ToS & Crawling Compliance
1. Module MUST check and respect `robots.txt` at `https://ulands.utexas.edu/robots.txt` before crawling
2. If `robots.txt` disallows crawling target paths, module MUST abort with clear error message
3. User-Agent header MUST identify the crawler appropriately (e.g., `RCAIngestion/1.0`)

## Storage Budget Estimate

Based on preliminary portal analysis:
- **Estimated Document Count:** 500-2,000 RCA PDFs across priority counties
- **Average PDF Size:** 1-5 MB (pre-compression)
- **Compressed Size:** ~60-75% of original (zstd)
- **Total Storage Estimate:** 500 MB - 5 GB (compressed)
- **Manifest/Metrics Overhead:** < 10 MB

**Capacity Confirmation:** Local development machines require minimum 10 GB free disk space before running full ingestion.

## Technical Approach
- **Module Class:** Extend `SourceModule` base class with Texas-specific discovery logic
- **HTTP Client:** Use `httpx.AsyncClient` for async requests with connection pooling
- **Document Filtering:** Keyword-based filtering on document name and type fields
- **Path Generation:** County-based directory structure with sanitized API numbers
- **Robots.txt Compliance:** Parse and respect `robots.txt` using `urllib.robotparser`

## Security Considerations
- Public data source; no sensitive credentials required for basic access
- If registration required for bulk access, store credentials in environment variables (not code)
- Rate limiting protects against accidental DoS of public resource
- No PII collected; well data is public record

## Files to Create/Modify
- `src/ingestion/modules/texas.py` — New module implementing `TexasModule` class
- `src/ingestion/modules/__init__.py` — Register Texas module in module registry
- `tests/ingestion/test_texas.py` — Unit tests for module functionality
- `tests/ingestion/test_texas_integration.py` — Integration tests with mocked server
- `tests/ingestion/fixtures/texas/` — Static HTML/JSON fixtures from portal for offline development

## Static Test Fixtures

To enable offline development and deterministic testing:
- `tests/ingestion/fixtures/texas/county_search_andrews.json` — Sample county search response
- `tests/ingestion/fixtures/texas/well_documents_42_003_12345.json` — Sample well document listing
- `tests/ingestion/fixtures/texas/sample_rca.pdf` — Small sample PDF for download tests
- `tests/ingestion/fixtures/texas/robots.txt` — Cached robots.txt for compliance testing

**Fixture Collection:** Run `python -m src.ingestion collect-fixtures texas` to capture fresh responses from portal (requires network access, one-time operation).

## Dependencies
- Core ingestion framework (`SourceModule`, `DownloadJob`) must be implemented
- `httpx` async HTTP client available
- `zstandard` compression library available

## Out of Scope (Future)
- **LAS file parsing** — Focus on PDF acquisition first; structured data extraction deferred
- **Production data ingestion** — RCA documents only for initial implementation
- **Historical backfill optimization** — Standard discovery sufficient for MVP
- **Multi-state expansion** — Texas-only; other state modules are separate issues
- **Proxy rotation** — Not implementing unless IP bans encountered in production

## Acceptance Criteria
- [ ] `TexasModule` class inherits from `SourceModule` and implements required interface
- [ ] Module checks `robots.txt` before crawling and aborts if disallowed
- [ ] Module discovers documents from at least 3 different priority counties
- [ ] RCA document filtering correctly identifies relevant documents (>80% precision on sample)
- [ ] Rate limiting enforced at 1 req/sec (measurable in logs)
- [ ] Downloaded files stored in correct directory structure with zstd compression
- [ ] Manifest updated with complete metadata for each downloaded document
- [ ] 403/restricted document responses logged and skipped gracefully
- [ ] `--dry-run` flag outputs discovery results without downloading
- [ ] `--limit N` flag correctly caps total downloads
- [ ] Static test fixtures committed to `tests/ingestion/fixtures/texas/`

## Definition of Done

### Implementation
- [ ] `TexasModule` class implemented with all required methods
- [ ] County search functionality working against portal
- [ ] Document filtering logic tested and tuned
- [ ] `robots.txt` compliance check implemented
- [ ] Unit tests written and passing (>90% coverage of module)

### Tools
- [ ] CLI supports `ingest texas` command with standard flags
- [ ] `--dry-run` and `--limit` flags functional
- [ ] `collect-fixtures texas` command for fixture generation

### Documentation
- [ ] Module docstrings complete with usage examples
- [ ] Update ingestion README with Texas module details
- [ ] Document any discovered auth requirements or portal quirks
- [ ] Add `src/ingestion/modules/texas.py` to file inventory

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Smoke test passes: `python -m src.ingestion ingest texas --limit 3`
- [ ] Manifest validates against schema
- [ ] Downloaded PDFs are valid (not corrupted/truncated)
- [ ] Storage usage within budget estimate (< 5 GB for full run)

## Testing Notes

### Unit Test Scenarios
```python
def test_county_search_returns_wells(self, mock_response): ...
def test_rca_document_filtering_positive(self): ...
def test_rca_document_filtering_negative(self): ...
def test_api_number_validation(self): ...
def test_rate_limiting_applied(self): ...
def test_graceful_403_handling(self, mock_response): ...
def test_path_generation_sanitizes_county_names(self): ...
def test_robots_txt_respected(self, mock_robots): ...
def test_robots_txt_disallowed_aborts(self, mock_robots): ...
```

### Integration Test Scenarios
```python
def test_end_to_end_download(self, mock_texas_server):
    """Full flow: discover → filter → download → manifest."""

def test_county_rotation(self, mock_texas_server):
    """Verify multiple counties are queried when limit allows."""

def test_checkpoint_recovery(self, mock_texas_server):
    """Interrupt mid-run, resume, verify no duplicates."""

def test_offline_with_fixtures(self):
    """Run full discovery using committed static fixtures."""
```

### Manual Smoke Test
```bash
# Verify discovery without download
python -m src.ingestion ingest texas --limit 5 --dry-run

# Small live test
python -m src.ingestion ingest texas --limit 3

# Verify output
cat data/raw/texas/manifest.json | jq '.[] | {well_id, county}'
ls -la data/raw/texas/*/

# Check storage usage
du -sh data/raw/texas/
```

### Forcing Error States
- Block `ulands.utexas.edu` in `/etc/hosts` to test connection failures
- Mock 403 responses in unit tests for access denied scenarios
- Set `--limit 1000` with low timeout to test circuit breaker
- Use restrictive mock `robots.txt` to test compliance abort

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-01-31 | **Reviews:** 2</sub>
