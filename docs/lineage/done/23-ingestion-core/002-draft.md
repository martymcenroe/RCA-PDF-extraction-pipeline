# Data Ingestion Core Framework + USGS CRC Module

## User Story
As a **data scientist building RCA extraction models**,
I want **an automated pipeline to acquire, compress, and track RCA reports from public geological repositories**,
So that **I can build diverse training datasets with full provenance and data integrity guarantees**.

## Objective
Build a modular data ingestion framework with the USGS Core Research Center as the first source module, enabling automated discovery, download, compression, and manifest tracking of RCA documents.

## UX Flow

### Scenario 1: Fresh Ingestion Run
1. User runs `python -m src.ingestion ingest usgs --limit 50`
2. System discovers 50 RCA documents from USGS catalog
3. System downloads each document with rate limiting (1 req/sec)
4. System compresses with zstd and stores in `data/raw/usgs/{state}/`
5. System updates manifest with checksums and metadata
6. Result: 50 compressed PDFs stored with full provenance

### Scenario 2: Resumed Ingestion After Interruption
1. User runs ingestion, process is interrupted at document 25
2. State is checkpointed to `data/state/usgs.json`
3. User runs `python -m src.ingestion ingest usgs --limit 50 --resume`
4. System loads checkpoint, skips 25 completed documents
5. System downloads remaining 25 documents
6. Result: Full 50 documents acquired without re-downloading

### Scenario 3: Source Temporarily Unavailable
1. User runs ingestion against USGS
2. USGS returns 5 consecutive 503 errors
3. Circuit breaker opens, source marked as unavailable
4. System logs failure and saves checkpoint
5. Result: Graceful failure with state preserved for retry

### Scenario 4: Dry Run Discovery
1. User runs `python -m src.ingestion ingest usgs --limit 10 --dry-run`
2. System discovers 10 documents without downloading
3. System prints document URLs and metadata
4. Result: User can preview what would be downloaded

## Requirements

### Core Framework
1. Base `SourceModule` class with abstract methods for discovery and download
2. `DownloadJob` dataclass representing a single download work unit
3. `ManifestEntry` dataclass for tracking downloaded files
4. `IngestionController` orchestrating downloads across multiple sources
5. `StorageManager` handling zstd compression and file organization

### Resilience
1. Exponential backoff retry (3 attempts, 2-30 second waits)
2. Circuit breaker pattern (5 failures = open, 5 min reset)
3. Checkpoint/resume via JSON state files
4. Graceful handling of 404s and missing documents

### USGS Module
1. Catalog discovery by state (priority: TX, OK, LA, NM, CO, WY, ND, MT, KS)
2. RCA document filtering by keywords
3. Rate limiting at 1 request/second
4. Library number extraction for unique identification
5. ZIP archive handling when documents are bundled

### CLI Interface
1. `ingest` command with source selection and limits
2. `status` command showing progress across sources
3. `--dry-run` flag for discovery without download
4. `--resume/--no-resume` flag for checkpoint behavior

## Technical Approach
- **Base Classes:** Dataclasses for `ManifestEntry`, `DownloadJob`; abstract `SourceModule` class
- **Controller:** Async orchestration with circuit breaker integration per source
- **Storage:** zstd compression (level 3), SHA256 checksums, hierarchical paths
- **HTTP Client:** httpx with async support, tenacity for retries
- **CLI:** Click framework with asyncio integration
- **State:** JSON files in `data/state/` for checkpointing

## Security Considerations
- USGS CRC is public data, no authentication required
- Rate limiting (1 req/sec) ensures polite crawling
- No user credentials stored
- Checksums verify data integrity post-download
- All data stored locally in `data/raw/` (gitignored)

## Files to Create/Modify

### New Files
- `src/ingestion/__init__.py` — Package init with exports
- `src/ingestion/core.py` — Base classes, controller, storage manager
- `src/ingestion/modules/__init__.py` — Modules package init
- `src/ingestion/modules/usgs.py` — USGS CRC source module
- `src/ingestion/cli.py` — Click-based CLI interface
- `tests/ingestion/__init__.py` — Test package init
- `tests/ingestion/test_core.py` — Unit tests for core components
- `tests/ingestion/test_usgs.py` — Unit tests for USGS module
- `tests/ingestion/test_integration.py` — Integration tests

### Modified Files
- `pyproject.toml` — Add dependencies (httpx, zstandard, tenacity, beautifulsoup4, click)
- `.gitignore` — Add `data/raw/`, `data/state/`

## Dependencies
- None (first issue in ingestion epic)

## Out of Scope (Future)
- Additional source modules (Kansas GS, state surveys) — separate issues
- Parallel downloads within a source — optimization for later
- Cloud storage backends (S3, GCS) — local-only for MVP
- Web UI for monitoring — CLI only for now
- Document deduplication across sources — future enhancement

## Acceptance Criteria
- [ ] `python -m src.ingestion ingest usgs --limit 5` downloads 5 RCA PDFs
- [ ] Downloaded files are zstd-compressed with `.pdf.zst` extension
- [ ] Manifest file created at `data/raw/usgs/manifest.json` with SHA256 checksums
- [ ] Interrupted ingestion resumes from checkpoint without re-downloading
- [ ] Rate limiting enforces 1 request/second to USGS
- [ ] Circuit breaker opens after 5 consecutive failures
- [ ] `--dry-run` flag discovers documents without downloading
- [ ] `status` command shows completed/failed/pending counts
- [ ] 404 errors logged but don't crash the pipeline
- [ ] All unit tests pass with mocked HTTP responses

## Definition of Done

### Implementation
- [ ] Core framework implemented (`core.py`)
- [ ] USGS module implemented (`modules/usgs.py`)
- [ ] CLI implemented (`cli.py`)
- [ ] Unit tests written and passing
- [ ] Integration tests with mocked HTTP passing

### Tools
- [ ] CLI documented with `--help` for all commands
- [ ] Example usage in module docstrings

### Documentation
- [ ] README section on data ingestion added
- [ ] Inline docstrings for all public classes/methods
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/0XXX/implementation-report.md` created
- [ ] `docs/reports/0XXX/test-report.md` created

### Verification
- [ ] Smoke test passes against live USGS (limit=1)
- [ ] Compression ratio logged (expect ~25% reduction)
- [ ] Manifest integrity verified

## Testing Notes

### Unit Test Mocking
```python
# Mock USGS catalog response
@pytest.fixture
def mock_usgs_catalog():
    return """<html>..catalog HTML..</html>"""

# Mock PDF download
@pytest.fixture  
def mock_pdf_content():
    return b"%PDF-1.4..."
```

### Force Error States
- **Circuit breaker:** Mock 5 consecutive 503 responses
- **Retry exhaustion:** Mock timeout on all 3 attempts
- **Checksum mismatch:** Corrupt downloaded bytes before verification
- **Resume behavior:** Pre-populate state file with 2 completed wells

### Smoke Test Commands
```bash
# Dry run first
python -m src.ingestion ingest usgs --limit 1 --dry-run

# Actual download
python -m src.ingestion ingest usgs --limit 1

# Verify outputs
ls -la data/raw/usgs/
cat data/raw/usgs/manifest.json
python -m src.ingestion status
```