# Historical Reference Database for Cross-Report Image Comparison

## User Story
As a **fraud analyst**,
I want to **compare images from new reports against a historical database of all previously analyzed images**,
So that I can **detect fraudulent reuse of photos across reports spanning multiple years**.

## Objective
Build a persistent database of image fingerprints from historical reports to enable cross-report duplicate detection that catches fraud spanning multiple documents.

## UX Flow

### Scenario 1: Ingesting Historical Reports
1. User runs `python -m src.gfiat.db ingest ./extracted/`
2. System validates input path (rejects absolute paths and `../` traversal attempts)
3. System scans directory for extracted image data
4. System extracts pHash and SIFT descriptors for each image
5. System stores fingerprints with metadata (source PDF, page, well name, depth)
6. Result: Database populated with historical image fingerprints

### Scenario 2: Querying for Similar Images
1. User analyzes a new report and extracts image fingerprints
2. System queries database for images with matching/similar pHash values
3. System performs SIFT matching on candidates
4. Result: List of potential cross-report duplicates with source information

### Scenario 3: Duplicate Source PDF Handling (Non-Interactive)
1. User runs ingest on a PDF that was previously ingested
2. System detects existing entries for this source PDF
3. System applies behavior based on CLI flag:
   - `--skip-existing` (default): Skip already-ingested PDFs
   - `--update-existing`: Update entries with new fingerprints
   - `--force`: Delete existing entries and re-ingest
4. Result: No duplicate entries; database remains consistent; no interactive prompts

### Scenario 4: No Matches Found
1. User queries database with a new image fingerprint
2. System searches pHash index and finds no close matches
3. Result: Empty result set returned; image is novel

### Scenario 5: Partial Ingestion Failure
1. User runs ingest on directory with 100 images
2. Image 50 is corrupted or unreadable
3. System logs error with file path and reason, skips corrupted image
4. System continues processing remaining images
5. Result: 99 images ingested successfully; 1 error logged to `ingest_errors.log`

## Requirements

### Database Storage
1. SQLite database for image metadata and pHash values
2. **Local-Only Storage:** Database file must reside on local filesystem only; no external transmission of database or contents permitted
3. Indexed pHash column for fast lookup queries
4. SIFT descriptors stored as `.npy` files with relative paths in database
5. Support for well metadata (name, depth) when available

### Ingestion
1. Recursively scan directories for extracted image data
2. Extract pHash for each image
3. Extract and store SIFT descriptors
4. Handle duplicate source PDFs gracefully via CLI flags (non-interactive)
5. Track ingestion date for audit purposes
6. **Partial Failure Handling:** On file read error or corruption, log error and skip file (Fail Open); continue processing remaining files
7. Generate `ingest_errors.log` with timestamp, file path, and error details for any skipped files

### Input Validation
1. Reject absolute paths in CLI file arguments
2. Reject parent directory references (`../`) in all path inputs
3. Sanitize all path inputs before filesystem operations

### Querying
1. Find images with exact pHash match
2. Find images with similar pHash (default Hamming distance threshold = 5, configurable via `--threshold` flag)
3. Find images with SIFT descriptor matches (default match ratio = 0.75, configurable via `--ratio` flag)
4. Return source PDF, page number, and metadata for matches

### CLI Interface
1. `python -m src.gfiat.db ingest <directory> [--skip-existing|--update-existing|--force]` — add images to database
2. `python -m src.gfiat.db query --phash <hash> [--threshold N]` — find similar by pHash
3. `python -m src.gfiat.db query --image <path> [--ratio N]` — find similar by image file
4. `python -m src.gfiat.db stats` — show database statistics

### Duplicate Handling Flags
- `--skip-existing` (default): Skip PDFs already in database; log skipped files
- `--update-existing`: Re-extract fingerprints and update existing entries
- `--force`: Delete all existing entries for PDF and re-ingest from scratch

## Technical Approach
- **Storage:** SQLite for metadata and pHash; filesystem for SIFT `.npy` files
- **Data Residency:** All data stored locally; no network transmission
- **Path Storage:** All SIFT file paths stored as relative paths (not absolute) for database portability
- **Indexing:** B-tree index on pHash for fast exact/prefix matching
- **Similarity Search:** Hamming distance calculation for pHash comparison (default threshold: 5)
- **SIFT Matching:** Load candidate `.npy` files and run FLANN matching (default ratio: 0.75)
- **SIFT Library:** Use OpenCV's SIFT implementation (patent expired 2020, freely usable)
- **Scalability Path:** Design schema to allow future FAISS migration for vector search

### Database Schema
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY,
    source_pdf TEXT NOT NULL,
    page_num INTEGER,
    image_index INTEGER,
    phash TEXT NOT NULL,
    sift_file TEXT,  -- MUST be relative path, not absolute
    extracted_date TEXT,
    well_name TEXT,
    depth TEXT,
    UNIQUE(source_pdf, page_num, image_index)
);

CREATE INDEX idx_phash ON images(phash);
CREATE INDEX idx_source ON images(source_pdf);
```

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [x] **Architecture:** Introduces persistent storage layer; future FAISS migration path needed
- [x] **Cost:** Storage grows with ingested reports (~1MB/100 images pHash, ~50MB/100 images with SIFT)
- [x] **Legal/PII:** Image fingerprints only; well names and PDF paths stored locally only with no external transmission
- [x] **Safety:** Database corruption could lose historical reference data; need backup strategy; partial ingestion failures handled via skip-and-log

## Security Considerations
- Database contains only fingerprints and metadata, not original images
- **Local-Only Storage:** Database must remain on local filesystem; no cloud sync or network transmission
- File paths to SIFT descriptors must be relative (not absolute) to prevent path traversal and ensure database portability
- All CLI path inputs validated to reject absolute paths and `../` references
- Consider read-only mode for production queries
- **SIFT Library License:** OpenCV's SIFT implementation is used (patent expired March 2020); no licensing concerns

## Files to Create/Modify
- `src/gfiat/db/__init__.py` — Database module initialization
- `src/gfiat/db/schema.py` — SQLite schema and migrations
- `src/gfiat/db/ingest.py` — Ingestion logic for historical reports
- `src/gfiat/db/query.py` — Query functions for similarity search
- `src/gfiat/db/validation.py` — Input path sanitization and validation
- `src/gfiat/db/__main__.py` — CLI entry point
- `tests/test_db_ingest.py` — Ingestion tests
- `tests/test_db_query.py` — Query tests
- `tests/test_db_validation.py` — Path validation tests

## Dependencies
- Issue #23 must be completed first (Data Ingestion provides source PDFs and extraction)

## Out of Scope (Future)
- **FAISS integration** — deferred until scale requires it (thousands of images)
- **Automatic re-indexing** — manual ingest only for MVP
- **Web UI for database browsing** — CLI only
- **Distributed/sharded storage** — single SQLite file for now
- **Encryption at rest (SQLCipher)** — evaluate if well names require protection
- **Database migration tooling** — defer until schema changes required

## Acceptance Criteria
- [ ] SQLite database created with schema for image metadata
- [ ] pHash values stored with B-tree index for fast lookup
- [ ] SIFT descriptors stored as `.npy` files with relative paths in database
- [ ] Database stores relative paths (not absolute) to SIFT `.npy` files to ensure database portability
- [ ] Query returns images with exact pHash match
- [ ] Query returns images within Hamming distance threshold of pHash (default: 5)
- [ ] Query returns images with SIFT match ratio above threshold (default: 0.75)
- [ ] Hamming distance and SIFT ratio thresholds are configurable via CLI flags (`--threshold`, `--ratio`)
- [ ] `ingest` command adds all images from directory to database
- [ ] `ingest` command supports `--skip-existing`, `--update-existing`, and `--force` flags for non-interactive duplicate handling
- [ ] `query --phash` returns matching images with source metadata
- [ ] Duplicate source PDF handling prevents duplicate entries (via CLI flags, not interactive prompts)
- [ ] Database stats command shows image count and storage size
- [ ] System rejects absolute paths in CLI file arguments
- [ ] System rejects parent directory references (`../`) in CLI file arguments
- [ ] Corrupted/unreadable files during ingestion are skipped and logged (not crash)
- [ ] Database file stored locally only with no external transmission

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing

### Tools
- [ ] CLI tool `python -m src.gfiat.db` implemented
- [ ] Document tool usage in module docstring

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (file path handling)
- [ ] Run 0810 Privacy Audit - PASS (local-only data storage)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- Test with empty database, single image, and batch of images
- Test pHash similarity with known near-duplicate images
- Test SIFT matching with rotated/cropped versions of same image
- Test duplicate PDF handling by ingesting same PDF twice
- Verify index performance with 1000+ images
- Test query with non-existent hash returns empty result
- **Test path validation:** verify rejection of `/absolute/path`, `../parent/path`, `foo/../bar`
- **Test partial failure:** include corrupted image in batch, verify others process and error is logged
- **Test threshold flags:** verify `--threshold` and `--ratio` override defaults
- **Test duplicate handling flags:** verify `--skip-existing`, `--update-existing`, `--force` work without prompts
- **Test relative paths:** verify all SIFT file paths in database are relative, not absolute

## Labels
`database`, `python`, `feature`, `cli`

## Effort Estimate
**Size: M** (Medium) — New module with schema, ingestion, query logic, and CLI

## Original Brief
# G-FIAT: Historical Reference Database

## Problem

Checking images only within a single report misses fraud that spans multiple documents. A lab might reuse a photo from a well drilled 5 years ago in a new report. We need to compare against a historical database of all previously analyzed images.

## Proposed Solution

Build a persistent database of image fingerprints from historical reports for cross-report duplicate detection.

### Database Schema

**SQLite approach (simple):**
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY,
    source_pdf TEXT,
    page_num INTEGER,
    image_index INTEGER,
    phash TEXT,
    sift_file TEXT,  -- path to .npy descriptor file
    extracted_date TEXT,
    well_name TEXT,
    depth TEXT
);

CREATE INDEX idx_phash ON images(phash);
```

**FAISS approach (scalable):**
- For thousands of images, use Facebook's FAISS library
- Store SIFT descriptors as vectors
- Approximate nearest neighbor search in milliseconds
- Separate metadata in SQLite, vectors in FAISS index

### Workflow
1. Ingest historical reports (from #23 data ingestion)
2. Extract images and fingerprints
3. Add to reference database
4. When analyzing new report, query database for matches
5. Flag cross-report duplicates

## Acceptance Criteria

- [ ] SQLite database for image metadata
- [ ] Store pHash values with index for fast lookup
- [ ] Store SIFT descriptors (file path or embedded)
- [ ] Query: find images with similar pHash
- [ ] Query: find images with SIFT matches
- [ ] Ingest command to add reports to database
- [ ] CLI: `python -m src.gfiat.db ingest ./extracted/`
- [ ] CLI: `python -m src.gfiat.db query --phash <hash>`

## Technical Considerations

- Start with SQLite, migrate to FAISS if scale requires
- FAISS requires numpy arrays of consistent dimension
- Consider sharding by source/date for large datasets
- Need to handle updates when re-analyzing same PDF
- Storage estimate: ~1MB per 100 images (pHash only), ~50MB per 100 images (with SIFT)
- Integration point: Data Ingestion framework (#23) provides source PDFs

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-02-01 | **Reviews:** 3</sub>
