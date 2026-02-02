# Issue #24: Norwegian DISKOS Data Ingestion Module

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

### Scenario 5: Force Overwrite Mode
1. User runs `python -m src.ingestion ingest norway --limit 5 --force`
2. System detects existing files in target directory
3. Files are overwritten with fresh downloads
4. Result: Updated files replace previous versions

## Requirements

### Data Discovery
1. Prioritize Volve dataset wells before DISKOS exploration
2. Support all 10 known Volve wells (15/9-F-1 through 15/9-F-15D)
3. Filter documents using English and Norwegian keywords (kjerne, kjerneanalyse)
4. Handle well ID formats with slashes and hyphens (e.g., "15/9-F-1")

### Download & Storage
1. Compress to zstd format in `data/raw/norway/{dataset}/`
2. Rate limit to 1 request/second (verify against DISKOS robots.txt before implementation)
3. Support extended timeout (120s) for large files
4. Enforce 100 MB max file size limit
5. Handle ZIP archive extraction when needed
6. Support `--force` flag to overwrite existing files

### Resilience
1. Try alternative path patterns when primary path fails
2. Skip wells gracefully when documents unavailable
3. Continue ingestion on individual file failures
4. Log all failures with well ID and reason

### Data Handling
1. **Runtime Environment:** Local execution only (CLI tool runs on developer machine)
2. All data processing and storage occurs locally in project `data/` directory
3. No cloud storage or remote data transmission
4. No EU/EEA data export concerns as data remains local

## Technical Approach
- **Two-Phase Discovery:** Volve wells checked first via `_discover_volve()`, then DISKOS via `_discover_diskos()` if limit not reached
- **Path Fallback:** Multiple Volve URL patterns tried when primary fails
- **Norwegian Keyword Support:** RCA detection includes "kjerne" (core) and "kjerneanalyse" (core analysis)
- **Well ID Sanitization:** Slashes and hyphens converted to underscores for filesystem paths
- **Golden Master Fixtures:** Static HTML/JSON responses captured to `tests/fixtures/norway/` for offline testing

## Security Considerations
- Volve dataset is fully public (released by Equinor for research)
- DISKOS public data requires no authentication
- Some DISKOS data may require registration (handled gracefully with skip)
- No credentials stored; auth-required resources logged and skipped
- All inputs sanitized before filesystem operations

## License Compliance
- **Volve Dataset:** Released under [Equinor Open Data License](https://www.equinor.com/energy/volve-data-sharing) â€” free for research, education, and commercial use with attribution
- **DISKOS Public Data:** Available under Norwegian Petroleum Directorate open data terms â€” verify specific license at implementation time
- Both licenses are compatible with project MIT license

## Files to Create/Modify
- `src/ingestion/modules/norway.py` â€” New `NorwayModule` class implementation
- `src/ingestion/modules/__init__.py` â€” Register Norway module
- `tests/ingestion/test_norway.py` â€” Unit and integration tests
- `tests/fixtures/norway/` â€” Golden master HTML/JSON response fixtures
- `docs/ingestion/norway.md` â€” Module documentation and Volve structure

## Dependencies
- Core ingestion framework must be in place (SourceModule base class, DownloadJob)
- Compression utilities (zstd) available

## Out of Scope (Future)
- DISKOS authenticated access â€” requires registration workflow
- Seismic data (SEGY files) â€” different processing pipeline
- Production data ingestion â€” not RCA-related
- LAS file parsing â€” separate enhancement
- Cloud/CI execution â€” local-only for initial implementation

## Acceptance Criteria
- [ ] `NorwayModule` discovers all 10 Volve wells when available
- [ ] Documents filtered correctly using English and Norwegian keywords
- [ ] Well IDs with special characters (/, -) handled in file paths
- [ ] Volve wells processed before DISKOS exploration
- [ ] Large files (50+ MB) download successfully with extended timeout
- [ ] Files exceeding 100 MB rejected with `FileTooLargeError`
- [ ] Alternative path patterns tried when primary path returns 404
- [ ] Manifest entries include dataset field ("volve" or "diskos")
- [ ] Rate limiting enforced at 1 req/sec (or per robots.txt)
- [ ] `--dry-run` lists discoverable documents without downloading
- [ ] `--force` flag overwrites existing files
- [ ] All tests run offline using committed fixtures (no network calls)

## Definition of Done

### Implementation
- [ ] `NorwayModule` class with Volve priority and DISKOS fallback
- [ ] Norwegian keyword detection in `_is_rca_document()`
- [ ] Alternative path resolution for Volve structure variations
- [ ] `--force` flag implementation for file overwrite
- [ ] Unit tests written and passing
- [ ] Integration tests for priority ordering
- [ ] Golden master fixtures committed to `tests/fixtures/norway/`

### Tools
- [ ] CLI supports `ingest norway --limit N` command
- [ ] CLI supports `--force` flag for overwrite
- [ ] Dry-run mode functional for Norway module

### Documentation
- [ ] Document Volve directory structure in module docstring
- [ ] Update ingestion README with Norway module details
- [ ] Add Norway to supported sources list
- [ ] Document license requirements for Volve and DISKOS data
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/norway-module/implementation-report.md` created
- [ ] `docs/reports/norway-module/test-report.md` created

### Verification
- [ ] Smoke test: `python -m src.ingestion ingest norway --limit 1 --dry-run`
- [ ] Smoke test: `python -m src.ingestion ingest norway --limit 5`
- [ ] Manifest validation: `cat data/raw/norway/manifest.json | jq .`
- [ ] Verify DISKOS robots.txt compliance before production use

## Testing Notes

### Unit Test Coverage
```bash
pytest tests/ingestion/test_norway.py -v
```

Test cases:
- `test_volve_well_discovery` â€” Uses committed fixtures, verify all wells found
- `test_norwegian_keyword_matching` â€” Verify "kjerne", "kjerneanalyse" detected
- `test_well_id_sanitization` â€” "15/9-F-1" â†’ "15_9_F_1"
- `test_alternative_path_fallback` â€” Primary 404, alternative succeeds
- `test_large_file_handling` â€” 60 MB file downloads with extended timeout
- `test_file_size_limit` â€” 150 MB file rejected
- `test_force_overwrite` â€” Existing files replaced when `--force` used

### Fixture Requirements
All tests MUST run offline. Commit golden master responses to:
```
tests/fixtures/norway/
  volve_well_listing.json
  volve_document_response.html
  diskos_search_response.json
```

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

# Force overwrite
python -m src.ingestion ingest norway --limit 5 --force

# Verify manifest
cat data/raw/norway/manifest.json | jq '.[] | {well_id, dataset}'

# Check compression
ls -la data/raw/norway/volve/
```

## Metadata

**Labels:** `ingestion`, `norway`, `external-data`
**Effort:** Medium (3-5 Story Points)

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-01-31 | **Reviews:** 2</sub>
