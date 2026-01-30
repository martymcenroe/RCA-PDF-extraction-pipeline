# Improved Footnote Symbol Handling for PDF Table Extraction

## User Story
As a data analyst working with core sample data,
I want footnote symbols extracted with their original meaning preserved and merged cells correctly expanded,
So that I can accurately interpret fracture types and detection limit indicators without data loss.

## Objective
Preserve the semantic distinction between footnote symbols `(f)`/`(F)` and correctly expand merged cell values (`+`, `<0.0001`, `**`) across their spanning columns during PDF table extraction.

## UX Flow

### Scenario 1: Extracting Fracture Indicators (Happy Path)
1. User runs extraction on PDF containing samples with `(f)` and `(F)` annotations
2. System detects case-sensitive fracture indicators
3. Result: CSV output preserves `(f)` and `(F)` as distinct values in the `notes` column

### Scenario 2: Extracting Merged Permeability Cells
1. User extracts table row where `+` spans both Air and Klink permeability columns
2. System detects `+` as a merged cell indicator
3. Result: Both `permeability_air_md` and `permeability_klink_md` contain `+`

### Scenario 3: Extracting Merged Saturation Cells
1. User extracts table row where `**` spans all three saturation columns
2. System detects `**` as a merged cell indicator for saturation group
3. Result: `saturation_water_pct`, `saturation_oil_pct`, and `saturation_total_pct` all contain `**`

### Scenario 4: Mixed Row with Multiple Indicators
1. User extracts row containing `(F)` fracture note AND `<0.0001` merged permeability
2. System processes both indicators independently
3. Result: `notes` contains `(F)`, both permeability columns contain `<0.0001`

## Requirements

### Symbol Preservation
1. Preserve exact case of fracture indicators: `(f)` remains `(f)`, `(F)` remains `(F)`
2. Store original symbol text, not interpreted values (e.g., keep `+` not `below_detection`)
3. Document symbol meanings in extraction metadata or comments

### Merged Cell Expansion
1. Define column groups that can contain merged cells:
   - Permeability: `permeability_air_md`, `permeability_klink_md`
   - Saturation: `saturation_water_pct`, `saturation_oil_pct`, `saturation_total_pct`
2. Detect merged cell indicators: `+`, `<0.0001`, `<`, `**`
3. When indicator detected in any column of a group, replicate to all columns in that group

### Data Integrity
1. Only expand known merged indicators, not arbitrary values
2. Log when expansion occurs for audit trail
3. Preserve ability to distinguish "no data" from "below detection limit"

## Technical Approach

- **Column Groups Configuration:** Define `COLUMN_GROUPS` dict mapping group names to column lists
- **Merged Indicators List:** Define `MERGED_INDICATORS` list of strings that trigger expansion
- **Post-Processing Pass:** Add `expand_merged_values()` function after initial row extraction
- **Case-Sensitive Matching:** Update fracture detection to use separate checks for `(f)` vs `(F)`

## Security Considerations
No security implications - this is a data transformation enhancement with no external API calls, file system changes outside the output CSV, or user input handling changes.

## Files to Create/Modify
- `src/extraction/pdf_parser.py` — Add `COLUMN_GROUPS`, `MERGED_INDICATORS` constants; update fracture detection logic
- `src/extraction/postprocess.py` — Add `expand_merged_values()` function (or add to existing postprocessor)
- `tests/test_footnote_symbols.py` — New test file for symbol handling
- `docs/data-dictionary.md` — Document symbol meanings

## Dependencies
- None - this enhancement can be implemented independently

## Out of Scope (Future)
- Automatic PDF legend parsing to discover symbol meanings — manual documentation for now
- Visual merged cell detection via PDF structure analysis — using indicator-based heuristic instead
- Support for additional footnote symbols beyond the four identified — add as discovered

## Acceptance Criteria
- [ ] Rows with `(f)` have `notes` column containing exactly `(f)`
- [ ] Rows with `(F)` have `notes` column containing exactly `(F)`
- [ ] Rows with `+` in permeability have `+` in BOTH `permeability_air_md` AND `permeability_klink_md`
- [ ] Rows with `<0.0001` in permeability have value in BOTH permeability columns
- [ ] Rows with `**` in saturation have `**` in ALL THREE saturation columns
- [ ] Existing rows without footnote symbols are unchanged
- [ ] At least one sample with `(f)` and one with `(F)` exist in test data to verify differentiation

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing

### Tools
- [ ] Update/create relevant CLI tools in `tools/` (if applicable)
- [ ] Document tool usage

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

### Test Data Requirements
Ensure test PDF or mock data includes:
- At least 2 rows with `(f)` fracture indicator
- At least 2 rows with `(F)` fracture indicator  
- At least 1 row with `+` merged across permeability columns
- At least 1 row with `<0.0001` merged across permeability columns
- At least 1 row with `**` merged across saturation columns
- Control rows with normal numeric values (should be unchanged)

### Manual Verification
1. Compare extraction output against source PDF visually for 5 random rows with footnotes
2. Verify column counts match expected (no shifted data from expansion logic)