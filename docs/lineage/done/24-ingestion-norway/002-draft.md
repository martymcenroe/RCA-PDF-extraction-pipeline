# Norwegian DISKOS Data Ingestion Module

## User Story
As a data engineer,
I want to ingest RCA documents from Norway's DISKOS repository and Volve dataset,
So that the system can access high-quality North Sea petroleum data with exceptional documentation standards.

## Objective
Implement a `NorwayModule` that prioritizes the publicly available Volve dataset before falling back to DISKOS exploration for additional Norwegian Continental Shelf well data.

## UX Flow

### Scenario 1: Volve Dataset Ingestion (Happy Path)
1. User runs `python -m src.ingestion ingest norway --limit 10`
2. System discovers Volve wells first (15/9-F-1, 15/9-F-1A, etc.)
3. System downloads RCA/SCAL PDFs from known Volve paths
4. Files compressed and stored in `data/raw/norway/volve/`
5. Result: Manifest updated with 10 Volve documents

### Scenario 2: DISKOS Fallback
1. User runs `python -m src.ingestion ingest norway --limit 20`
2. System exhausts Volve wells (10 documents)
3. System falls back to DISKOS exploration for major fields
4. Result: Mixed manifest with Volve and DISKOS entries

### Scenario 3: Large File Handling
1. System encounters SCAL report > 50 MB
2. Extended timeout (120s) allows complete download
3. File size checked against 100 MB limit
4. Result: Large file successfully ingested with compression

### Scenario 4: Path Resolution Failure
1. Primary Volve path returns 404
2. System tries alternative path patterns
3. If all patterns fail, well is skipped with warning
4. Result: Partial ingestion continues, failure logged

## Requirements

### Data Discovery
1. Prioritize Volve dataset wells before DISKOS exploration
2. Support all 10 known Volve wells (15/9-F-1 through 15/9-F-15D)
3. Filter documents using English and Norwegian keywords (kjerne, kjerneanalyse)
4. Handle well ID formats with slashes and hyphens (e.g., "15/9-F-1")

### Download & Storage
1. Compress to zstd format in `data/raw/norway/{dataset}/`
2. Rate limit to 1 request/second
3. Support extended timeout (120s) for large files
4. Enforce 100 MB max file size limit
5. Handle ZIP archive extraction when needed

### Resilience
1. Try alternative path patterns when primary path fails
2. Skip wells gracefully when documents unavailable
3. Continue ingestion on individual file failures
4. Log all failures with well ID and reason

## Technical Approach
- **Two-Phase Discovery:** Volve wells checked first via `_discover_volve()`, then DISKOS via `_discover_diskos()` if limit not reached
- **Path Fallback:** Multiple Volve URL patterns tried when primary fails
- **Norwegian Keyword Support:** RCA detection includes "kjerne" (core) and "kjerneanalyse" (core analysis)
- **Well ID Sanitization:** Slashes and hyphens converted to underscores for filesystem paths

## Security Considerations
- Volve dataset is fully public (released by Equinor for research)
- DISKOS public data requires no authentication
- Some DISKOS data may require registration (handled gracefully with skip)
- No credentials stored; auth-required resources logged and skipped

## Files to Create/Modify
- `src/ingestion/modules/norway.py` — New `NorwayModule` class implementation
- `src/ingestion/modules/__init__.py` — Register Norway module
- `tests/ingestion/test_norway.py` — Unit and integration tests
- `docs/ingestion/norway.md` — Module documentation and Volve structure

## Dependencies
- Core ingestion framework must be in place (SourceModule base class, DownloadJob)
- Compression utilities (zstd) available

## Out of Scope (Future)
- DISKOS authenticated access — requires registration workflow
- Seismic data (SEGY files) — different processing pipeline
- Production data ingestion — not RCA-related
- LAS file parsing — separate enhancement

## Acceptance Criteria
- [ ] `NorwayModule` discovers all 10 Volve wells when available
- [ ] Documents filtered correctly using English and Norwegian keywords
- [ ] Well IDs with special characters (/, -) handled in file paths
- [ ] Volve wells processed before DISKOS exploration
- [ ] Large files (50+ MB) download successfully with extended timeout
- [ ] Files exceeding 100 MB rejected with `FileTooLargeError`
- [ ] Alternative path patterns tried when primary path returns 404
- [ ] Manifest entries include dataset field ("volve" or "diskos")
- [ ] Rate limiting enforced at 1 req/sec
- [ ] `--dry-run` lists discoverable documents without downloading

## Definition of Done

### Implementation
- [ ] `NorwayModule` class with Volve priority and DISKOS fallback
- [ ] Norwegian keyword detection in `_is_rca_document()`
- [ ] Alternative path resolution for Volve structure variations
- [ ] Unit tests written and passing
- [ ] Integration tests for priority ordering

### Tools
- [ ] CLI supports `ingest norway --limit N` command
- [ ] Dry-run mode functional for Norway module

### Documentation
- [ ] Document Volve directory structure in module docstring
- [ ] Update ingestion README with Norway module details
- [ ] Add Norway to supported sources list
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/norway-module/implementation-report.md` created
- [ ] `docs/reports/norway-module/test-report.md` created

### Verification
- [ ] Smoke test: `python -m src.ingestion ingest norway --limit 1 --dry-run`
- [ ] Smoke test: `python -m src.ingestion ingest norway --limit 5`
- [ ] Manifest validation: `cat data/raw/norway/manifest.json | jq .`

## Testing Notes

### Unit Test Coverage
```bash
pytest tests/ingestion/test_norway.py -v
```

Test cases:
- `test_volve_well_discovery` — Mock Volve server, verify all wells found
- `test_norwegian_keyword_matching` — Verify "kjerne", "kjerneanalyse" detected
- `test_well_id_sanitization` — "15/9-F-1" → "15_9_F_1"
- `test_alternative_path_fallback` — Primary 404, alternative succeeds
- `test_large_file_handling` — 60 MB file downloads with extended timeout
- `test_file_size_limit` — 150 MB file rejected

### Integration Test
```bash
pytest tests/ingestion/test_norway.py::TestNorwayIntegration -v
```

### Manual Smoke Test
```bash
# Dry run - verify discovery
python -m src.ingestion ingest norway --limit 1 --dry-run

# Actual download
python -m src.ingestion ingest norway --limit 5

# Verify manifest
cat data/raw/norway/manifest.json | jq '.[] | {well_id, dataset}'

# Check compression
ls -la data/raw/norway/volve/
```