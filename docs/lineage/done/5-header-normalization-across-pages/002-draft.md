# Header Normalization Across Pages

## User Story
As a **data analyst** using the RCA pipeline,
I want **table headers normalized consistently across multi-page tables**,
So that **I can work with clean, merged datasets without manual header cleanup**.

## Objective
Implement header normalization that detects, flattens, and standardizes table headers across continuation pages, merging related tables into single logical datasets with canonical column names.

## UX Flow

### Scenario 1: Multi-Page Table with Consistent Headers
1. User extracts tables from W20552.pdf (pages 39-42)
2. System detects pages 40-42 are continuations of page 39 table
3. System merges all rows into single table with headers from page 39
4. Result: Single table with 138 rows and canonical column names

### Scenario 2: Merged Cell Headers (Hierarchical)
1. User extracts table with merged header cells (e.g., "Permeability (md)" spanning "Air" and "Klink" columns)
2. System detects multi-row header structure
3. System flattens to single row: "permeability_air_md", "permeability_klink_md"
4. Result: Flat header row with descriptive column names

### Scenario 3: Continuation Page Without Headers
1. User extracts table where page 41 has no header row (pure data continuation)
2. System detects row count matches previous table schema
3. System applies headers from page 39 source table
4. Result: Data rows correctly attributed to canonical columns

### Scenario 4: Abbreviated Headers on Continuation
1. User extracts table where continuation page uses "Ka" instead of "Permeability Air (md)"
2. System fuzzy-matches abbreviated header to canonical name
3. System normalizes to "permeability_air_md"
4. Result: Consistent column names across all pages

## Requirements

### Header Detection
1. Distinguish header rows from data rows based on content patterns
2. Detect multi-row headers (merged cells spanning columns)
3. Identify header row position (typically first 1-3 rows)

### Header Normalization
1. Flatten hierarchical headers into single row
2. Map raw headers to canonical names via configurable mapping
3. Normalize units (%, md, g/cc) into column names
4. Handle unknown headers gracefully (preserve original name)

### Schema Matching
1. Detect when tables share compatible schemas
2. Support exact match, subset match, and fuzzy match modes
3. Calculate similarity score for abbreviated header matching
4. Threshold of 0.8 similarity for automatic merging

### Table Merging
1. Merge continuation tables into single logical table
2. Skip duplicate header rows on continuation pages
3. Preserve source page metadata for traceability
4. Maintain row order across merged pages

## Technical Approach
- **Header Detection:** Analyze numeric ratio and position to classify rows as header vs data
- **Merged Cell Resolution:** Track spanning headers across rows, combine parent + child names
- **Canonical Mapping:** Dictionary-based lookup with variant aliases per column
- **Schema Matching:** Levenshtein distance for fuzzy header comparison
- **Table Merging:** Sequential scan with schema compatibility check

## Security Considerations
- No external data access; all processing is local to provided PDF
- No user credentials or sensitive data involved
- Output is structured data derived entirely from input document

## Files to Create/Modify
- `src/rca_pipeline/table_extractor.py` — Add `normalize_headers` parameter, implement merging logic
- `src/rca_pipeline/header_normalizer.py` — New module for header detection, flattening, and normalization
- `src/rca_pipeline/schema_matcher.py` — New module for table schema comparison and merging
- `src/rca_pipeline/canonical_headers.py` — Canonical header mapping configuration
- `tests/test_header_normalization.py` — Unit tests for header normalization
- `tests/test_schema_matching.py` — Unit tests for schema matching and merging

## Dependencies
- Table extraction (#0003 or equivalent) must be functional
- Access to W20552.pdf for testing with real-world header variations

## Out of Scope (Future)
- **AI-based header inference** — Use rule-based detection for MVP
- **Cross-document schema matching** — Focus on single document first
- **User-defined canonical mappings** — Hardcode RCA mappings for now
- **Column reordering** — Assume consistent column order within document

## Acceptance Criteria
- [ ] Multi-row merged headers are flattened into single descriptive column names
- [ ] "Permeability (md)" + "Air" becomes "permeability_air_md"
- [ ] Tables from pages 39-42 merge into single table with 138 rows
- [ ] Continuation pages without headers inherit schema from source table
- [ ] Abbreviated headers ("Ka", "Sw") map to canonical names
- [ ] Output includes `header_source_page` and `pages_spanned` metadata
- [ ] Unknown headers are preserved (not dropped or errored)
- [ ] `normalize_headers=False` bypasses all normalization (backward compatible)

## Definition of Done

### Implementation
- [ ] `header_normalizer.py` module with `flatten_headers()` and `normalize_header()` functions
- [ ] `schema_matcher.py` module with `tables_match_schema()` and `merge_continuation_tables()` functions
- [ ] `table_extractor.py` updated to use normalization pipeline
- [ ] Unit tests written and passing (>90% coverage on new modules)

### Tools
- [ ] CLI flag `--normalize-headers` added to extraction tool (if applicable)
- [ ] Document canonical header mapping in tool help

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (if security-relevant)
- [ ] Run 0810 Privacy Audit - PASS (if privacy-relevant)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes

### Manual Testing
1. Run extraction on W20552.pdf with `normalize_headers=True`
2. Verify output contains single core analysis table (not 4 separate)
3. Verify all 138 data rows present
4. Verify column names are canonical (no raw "Permeability (md)")

### Force Error States
- Test with PDF containing only header row (no data) — should return empty table
- Test with completely unrecognized headers — should preserve original names
- Test with mismatched column counts between pages — should not merge, return separate tables

### Test Data
```python
# Mock multi-row header for unit testing
mock_headers = [
    ["", "Permeability (md)", "", "Porosity (%)", ""],
    ["Sample", "Air", "Klink", "Ambient", "NCS"]
]
# Expected flattened output
expected = ["sample_number", "permeability_air_md", "permeability_klink_md", 
            "porosity_ambient_pct", "porosity_ncs_pct"]
```