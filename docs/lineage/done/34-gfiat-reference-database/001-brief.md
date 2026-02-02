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
