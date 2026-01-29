# Performance & Scalability

## Benchmarks

All measurements on `W20552.pdf` (253 pages, 16.3 MB).

### Minimal Approach

| Operation | Time | Notes |
|-----------|------|-------|
| PDF open | ~10 ms | PyMuPDF document load |
| Page iteration | ~340 ms | 253 pages, text extraction |
| Classification | ~5 ms | Keyword matching |
| Data parsing | ~5 ms | 138 samples |
| **Total** | **359 ms** | Single-pass |

### Database Approach

| Operation | Time | Notes |
|-----------|------|-------|
| PDF extraction | 5,430 ms | All elements to memory |
| Database write | 1,232 ms | 224,706 records |
| **First run total** | **6,662 ms** | One-time cost |
| Query + parse | 56 ms | Subsequent runs |

### Comparison

| Scenario | Minimal | Database | Winner |
|----------|---------|----------|--------|
| Single extraction | 359 ms | 6,662 ms | Minimal |
| 10 extractions (same doc) | 3,590 ms | 6,662 + 560 ms | Database |
| Different query on same doc | 359 ms | 56 ms | Database |

**Break-even point:** ~18 queries on the same document.

## Resource Usage

### Memory

| Approach | Peak Memory | Notes |
|----------|-------------|-------|
| Minimal | ~50 MB | PDF in memory during processing |
| Database (extraction) | ~200 MB | All elements in memory before DB write |
| Database (query) | ~20 MB | Only loads relevant blocks |

### Disk

| File | Size | Records |
|------|------|---------|
| Input PDF | 16.3 MB | - |
| SQLite database | 32.4 MB | 224,706 |
| Output CSV | 15 KB | 138 rows |
| Output JSON | 45 KB | 138 samples + metadata |

## Scalability Projections

### Document Size Scaling

Assuming linear scaling with page count:

| Pages | Minimal Time | Database First Run | Database Query |
|-------|--------------|-------------------|----------------|
| 50 | ~70 ms | ~1.3 s | ~11 ms |
| 253 | 359 ms | 6.7 s | 56 ms |
| 500 | ~710 ms | ~13 s | ~110 ms |
| 1000 | ~1.4 s | ~26 s | ~220 ms |

### Batch Processing

Processing multiple documents (minimal approach):

| Documents | Serial Time | Parallel (4 cores) |
|-----------|-------------|-------------------|
| 1 | 359 ms | 359 ms |
| 10 | 3.6 s | ~1 s |
| 100 | 36 s | ~10 s |
| 1000 | 6 min | ~1.5 min |

### Database Approach for Batch

| Documents | Extraction | All Queries | Total |
|-----------|------------|-------------|-------|
| 10 | 67 s | 0.6 s | 67.6 s |
| 100 | 670 s (~11 min) | 6 s | ~11 min |

Database approach is slower for batch processing of different documents, but faster for repeated queries on the same documents.

## Bottleneck Analysis

### Minimal Approach

| Component | % Time | Optimization Opportunity |
|-----------|--------|-------------------------|
| PDF text extraction | 95% | Limited (PyMuPDF already fast) |
| Classification | 1% | None needed |
| Parsing | 4% | None needed |

### Database Approach

| Component | % Time (First Run) | Optimization |
|-----------|-------------------|--------------|
| PDF extraction | 82% | Skip unused elements |
| Database write | 18% | Batch inserts, disable indexes during load |

## Cost Analysis

### Cloud Processing (AWS Lambda)

Assuming 256 MB memory, 1 second billed duration:

| Documents/Month | Minimal Cost | Database Cost |
|-----------------|--------------|---------------|
| 100 | ~$0.02 | ~$0.14 |
| 1,000 | ~$0.21 | ~$1.40 |
| 10,000 | ~$2.10 | ~$14.00 |

### OCR Alternative (if needed)

| Service | Per Document | 1,000 Documents |
|---------|--------------|-----------------|
| Text extraction (current) | $0 | $0 |
| AWS Textract | ~$1.50 | $1,500 |
| Google Vision | ~$1.50 | $1,500 |
| OpenAI Vision | ~$0.50 | $500 |

## Recommendations

| Use Case | Recommended Approach |
|----------|---------------------|
| Grading/evaluation | Minimal |
| CI/CD pipeline | Minimal |
| Batch processing | Minimal (parallel) |
| Interactive exploration | Database + viewer |
| Development/debugging | Database + viewer |
| API with repeated queries | Database |
