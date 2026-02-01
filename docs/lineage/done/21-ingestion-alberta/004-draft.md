# Alberta AER Data Ingestion Module

## User Story
As a petroleum data scientist,
I want to ingest routine core analysis (RCA) documents from the Alberta Energy Regulator,
So that I can access Canadian well data from the Western Canadian Sedimentary Basin with unique formations not represented in US datasets.

## Objective
Implement an Alberta ingestion module that queries non-confidential wells from the AER data portal, filters by priority formations (Montney, Duvernay, Cardium), and downloads RCA documents with proper rate limiting and Canadian data format handling.

## UX Flow

### Scenario 1: Successful Formation-Based Discovery
1. User runs `python -m src.ingestion ingest alberta --limit 50`
2. System queries AER for wells in priority formations (Montney, Duvernay, Cardium, etc.)
3. System filters to non-confidential wells with core data
4. System downloads RCA documents with 1 req/sec rate limiting
5. Result: Documents saved to `data/raw/alberta/{formation}/` with manifest updated

### Scenario 2: Confidential Well Encountered
1. User runs ingestion against Alberta wells
2. System encounters a well still in confidentiality period
3. System logs skip and continues to next well
4. Result: No confidential data downloaded, clear audit trail

### Scenario 3: UWI Format Variations
1. User ingests wells with different UWI representations
2. System normalizes UWI formats (e.g., `100/06-12-034-05W4/0` → `100_06_12_034_05W4_0`)
3. Result: Consistent filesystem paths regardless of source format

### Scenario 4: Rate Limit Exceeded
1. System makes requests faster than AER allows
2. AER returns 429 response
3. System applies exponential backoff and retries
4. Result: Download eventually succeeds, no data loss

## Requirements

### Data Discovery
1. Query AER API for wells by formation with core data available
2. Filter to non-confidential wells only (confidentiality period typically 1 year)
3. Rotate through priority formations: Montney, Duvernay, Cardium, Viking, Mannville, Leduc, Nisku, Wabamun
4. Identify RCA-related documents by keywords (core analysis, porosity, permeability, etc.)

### UWI Handling
1. Parse Canadian UWI format: `LE-LSd-Sec-Twp-Rge-Mer` (e.g., `100/06-12-034-05W4/0`)
2. Extract components: location exception, legal subdivision, section, township, range, meridian
3. Sanitize UWI for filesystem-safe paths
4. Preserve original UWI in metadata for traceability

### Download & Storage
1. Rate limit to 1 request/second
2. Compress with zstd before storage
3. Store in `data/raw/alberta/{formation}/{sanitized_uwi}.pdf.zst`
4. Update manifest with full metadata including formation and operator

### Resilience
1. Pre-flight confidentiality check before download attempt
2. Classify errors: confidential (skip), not_found (log), rate_limited (backoff), transient (retry)
3. Exponential backoff for 429 responses
4. Resume capability via manifest tracking

### Data Residency & Compliance
1. **Data processing to remain Local-Only; No external transmission of raw documents permitted**
2. All downloaded AER data must be stored on local infrastructure only
3. No raw document content may be sent to external APIs or cloud services

## Cost Estimate

### Storage & Bandwidth (Worst Case)
| Metric | Estimate | Notes |
|--------|----------|-------|
| Wells with RCA data | ~15,000 | Across all priority formations |
| Avg document size | 2 MB | Typical RCA PDF size |
| Max raw storage | 30 GB | 15,000 × 2 MB |
| Post-compression | ~22.5 GB | ~75% with zstd |
| Bandwidth per run | Variable | Depends on `--limit` flag |
| Typical batch (limit=50) | 100 MB | 50 × 2 MB |

### Rate Limit Impact
- At 1 req/sec: 50 documents ≈ 2 minutes discovery + 50 seconds download
- Full corpus (15,000 docs): ~8.5 hours wall time

## Legal & Compliance

### Scraping Compliance Verification
- **AER Acceptable Use Policy:** Verified — AER provides public API access for non-confidential well data
- **robots.txt:** Checked at https://www.aer.ca/robots.txt — API endpoints not disallowed
- **Rate Limiting:** 1 req/sec is conservative; AER does not publish official rate limits but community practice suggests this is safe
- **Terms of Service:** AER data is Crown copyright with open access for non-commercial research use

### Data Residency
- **Requirement:** Canadian government data — Local-Only processing
- **Implementation:** All storage paths are local filesystem (`data/raw/alberta/`)
- **Prohibition:** Raw PDFs must NOT be transmitted to external services

## Technical Approach
- **AlbertaModule class:** Extends `SourceModule` base class with AER-specific discovery and download logic
- **Formation search:** Iterate priority formations, query for wells with `hasCore=True` and `confidential=False`
- **UWI utilities:** Static methods for parsing and sanitizing Canadian well identifiers
- **Confidentiality guard:** Pre-download status check to ensure well data is public
- **Rate limiting:** Async sleep between requests to respect AER limits

## Security Considerations
- Only access non-confidential, publicly available data
- No authentication required for public data access
- Confidentiality checking prevents inadvertent access to restricted data
- Rate limiting respects AER's infrastructure
- Local-only storage ensures compliance with data residency requirements

## API Contract & Fixtures

### Sample AER API Response
See attached fixture: [`tests/fixtures/aer_sample_response.json`](tests/fixtures/aer_sample_response.json)

```json
{
  "wells": [
    {
      "uwi": "100/06-12-034-05W4/0",
      "name": "CNRL HZ MONTNEY 06-12",
      "license": "0501234",
      "operator": "Canadian Natural Resources",
      "formation": "Montney",
      "has_core": true,
      "confidential": false,
      "completion_date": "2018-03-15",
      "documents": [
        {
          "id": "doc-abc123",
          "name": "Routine Core Analysis Report",
          "document_type": "core analysis",
          "download_url": "https://www.aer.ca/data/api/documents/doc-abc123"
        }
      ]
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 100
}
```

### Sample UWI Formats
```
100/06-12-034-05W4/0    # Standard format
1AA/06-12-034-05W4/02   # With location exception and event sequence
00/06-12-034-05W4/0     # Simplified
```

## Files to Create/Modify
- `src/ingestion/modules/alberta.py` — New module implementing AER data ingestion
- `src/ingestion/modules/__init__.py` — Register AlbertaModule
- `tests/ingestion/test_alberta.py` — Unit tests for UWI parsing, filtering, confidentiality checks
- `tests/ingestion/test_alberta_integration.py` — Integration tests with mock AER server
- `tests/fixtures/aer_sample_response.json` — Sample API response fixture for offline development
- `docs/ingestion/alberta.md` — Documentation for AER data source and module usage

## Dependencies
- Core ingestion framework must be in place (SourceModule base class, DownloadJob, manifest handling)
- zstd compression utilities available

## Out of Scope (Future)
- Historical data quality assessment — separate data quality initiative
- Multi-province support (BC, Saskatchewan) — separate issues per province
- LAS file ingestion — focus on RCA PDFs first
- Core photo retrieval — document-focused for MVP
- Proxy rotation — not required given conservative rate limiting (see Questions section)

## Acceptance Criteria
- [ ] `AlbertaModule` discovers wells from at least 3 different formations in a single run
- [ ] UWI parsing correctly extracts section, township, range, meridian components
- [ ] UWI sanitization produces valid filesystem paths with no special characters
- [ ] Confidential wells are detected and skipped with clear log message
- [ ] Downloaded documents stored in correct formation subdirectories
- [ ] Manifest entries include formation, UWI, operator, and well name metadata
- [ ] Rate limiting maintains ≤1 request/second to AER
- [ ] Dry-run mode works: `--dry-run` shows what would be downloaded without fetching
- [ ] Smoke test passes: `python -m src.ingestion ingest alberta --limit 3`
- [ ] No raw documents transmitted externally (data residency compliance)

## Definition of Done

### Implementation
- [ ] `AlbertaModule` class implemented with all required methods
- [ ] UWI parsing and sanitization utilities complete
- [ ] Confidentiality pre-check implemented
- [ ] Unit tests written and passing
- [ ] Integration tests with mock server passing
- [ ] `tests/fixtures/aer_sample_response.json` created

### Tools
- [ ] CLI supports `alberta` as valid source argument
- [ ] Formation filter flag available: `--formation Montney`

### Documentation
- [ ] `docs/ingestion/alberta.md` documents AER data source
- [ ] README updated with Alberta as available source
- [ ] Add files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Unit Test Commands
```bash
pytest tests/ingestion/test_alberta.py -v
```

### Integration Test Commands
```bash
pytest tests/ingestion/test_alberta_integration.py -v
```

### Manual Smoke Test
```bash
# Dry run - verify discovery without download
python -m src.ingestion ingest alberta --limit 1 --dry-run

# Small batch download
python -m src.ingestion ingest alberta --limit 3

# Verify manifest
cat data/raw/alberta/manifest.json | jq '.entries | length'

# Verify formation distribution
cat data/raw/alberta/manifest.json | jq '[.entries[].metadata.formation] | group_by(.) | map({(.[0]): length}) | add'
```

### Force Error States
- **Confidential well:** Mock a well with `confidential: true` in status response
- **Rate limit:** Set rate_limit to 100 and verify 429 handling
- **Invalid UWI:** Pass malformed UWI to parser and verify graceful handling

---

**Labels:** `ingestion`, `region:canada`

**Size:** M

---

## Questions for Orchestrator
1. Does the target AER portal have IP banning mechanisms that require proxy rotation, or is the 1 req/sec rate limit safe as implemented? (Current assumption: 1 req/sec is sufficient without proxy rotation)

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-01-31 | **Reviews:** 2</sub>
