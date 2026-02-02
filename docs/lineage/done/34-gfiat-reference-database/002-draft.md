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
2. System scans directory for extracted image data
3. System extracts pHash and SIFT descriptors for each image
4. System stores fingerprints with metadata (source PDF, page, well name, depth)
5. Result: Database populated with historical image fingerprints

### Scenario 2: Querying for Similar Images
1. User analyzes a new report and extracts image fingerprints
2. System queries database for images with matching/similar pHash values
3. System performs SIFT matching on candidates
4. Result: List of potential cross-report duplicates with source information

### Scenario 3: Duplicate Source PDF Handling
1. User runs ingest on a PDF that was previously ingested
2. System detects existing entries for this source PDF
3. System prompts user: update, skip, or force re-ingest
4. Result: No duplicate entries; database remains consistent

### Scenario 4: No Matches Found
1. User queries database with a new image fingerprint
2. System searches pHash index and finds no close matches
3. Result: Empty result set returned; image is novel

## Requirements

### Database Storage
1. SQLite database for image metadata and pHash values
2. Indexed pHash column for fast lookup queries
3. SIFT descriptors stored as `.npy` files with paths in database
4. Support for well metadata (name, depth) when available

### Ingestion
1. Recursively scan directories for extracted image data
2. Extract pHash for each image
3. Extract and store SIFT descriptors
4. Handle duplicate source PDFs gracefully
5. Track ingestion date for audit purposes

### Querying
1. Find images with exact pHash match
2. Find images with similar pHash (Hamming distance threshold)
3. Find images with SIFT descriptor matches above threshold
4. Return source PDF, page number, and metadata for matches

### CLI Interface
1. `python -m src.gfiat.db ingest <directory>` — add images to database
2. `python -m src.gfiat.db query --phash <hash>` — find similar by pHash
3. `python -m src.gfiat.db query --image <path>` — find similar by image file
4. `python -m src.gfiat.db stats` — show database statistics

## Technical Approach
- **Storage:** SQLite for metadata and pHash; filesystem for SIFT `.npy` files
- **Indexing:** B-tree index on pHash for fast exact/prefix matching
- **Similarity Search:** Hamming distance calculation for pHash comparison
- **SIFT Matching:** Load candidate `.npy` files and run FLANN matching
- **Scalability Path:** Design schema to allow future FAISS migration for vector search

### Database Schema
```sql
CREATE TABLE images (
    id INTEGER PRIMARY KEY,
    source_pdf TEXT NOT NULL,
    page_num INTEGER,
    image_index INTEGER,
    phash TEXT NOT NULL,
    sift_file TEXT,
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
- [ ] **Legal/PII:** Image fingerprints only, no PII extracted
- [x] **Safety:** Database corruption could lose historical reference data; need backup strategy

## Security Considerations
- Database contains only fingerprints and metadata, not original images
- File paths to SIFT descriptors should be relative to prevent path traversal
- Consider read-only mode for production queries

## Files to Create/Modify
- `src/gfiat/db/__init__.py` — Database module initialization
- `src/gfiat/db/schema.py` — SQLite schema and migrations
- `src/gfiat/db/ingest.py` — Ingestion logic for historical reports
- `src/gfiat/db/query.py` — Query functions for similarity search
- `src/gfiat/db/__main__.py` — CLI entry point
- `tests/test_db_ingest.py` — Ingestion tests
- `tests/test_db_query.py` — Query tests

## Dependencies
- Issue #23 must be completed first (Data Ingestion provides source PDFs and extraction)

## Out of Scope (Future)
- **FAISS integration** — deferred until scale requires it (thousands of images)
- **Automatic re-indexing** — manual ingest only for MVP
- **Web UI for database browsing** — CLI only
- **Distributed/sharded storage** — single SQLite file for now

## Acceptance Criteria
- [ ] SQLite database created with schema for image metadata
- [ ] pHash values stored with B-tree index for fast lookup
- [ ] SIFT descriptors stored as `.npy` files with paths in database
- [ ] Query returns images with exact pHash match
- [ ] Query returns images within Hamming distance threshold of pHash
- [ ] Query returns images with SIFT match ratio above threshold
- [ ] `ingest` command adds all images from directory to database
- [ ] `query --phash` returns matching images with source metadata
- [ ] Duplicate source PDF handling prevents duplicate entries
- [ ] Database stats command shows image count and storage size

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
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- Test with empty database, single image, and batch of images
- Test pHash similarity with known near-duplicate images
- Test SIFT matching with rotated/cropped versions of same image
- Test duplicate PDF handling by ingesting same PDF twice
- Verify index performance with 1000+ images
- Test query with non-existent hash returns empty result