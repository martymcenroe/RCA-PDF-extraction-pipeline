# Issue #4: Improved Footnote Symbol Handling for PDF Table Extraction

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

### Scenario 5: False Positive Handling (Edge Case)
1. User extracts row where a text note legitimately starts with `+` but is not a merged cell indicator (e.g., `+10% correction`)
2. System checks if value is in a numeric column group AND matches exact merged indicator pattern
3. Result: Text is preserved as-is without triggering expansion; only exact matches (`+`, `**`, `<0.0001`, `<`) in defined column groups trigger expansion

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
4. Only trigger expansion on **exact string matches** of known indicators to avoid false positives

### CSV Output Sanitization
1. Prepend single quote (`'`) to values starting with `+`, `-`, `=`, or `@` to prevent CSV injection/formula execution in spreadsheet applications
2. Apply sanitization during CSV write phase, not during internal data processing
3. Document that raw values are sanitized for Excel/Sheets safety

### Data Integrity
1. Only expand known merged indicators, not arbitrary values
2. Log when expansion occurs for audit trail
3. Preserve ability to distinguish "no data" from "below detection limit"

## Technical Approach

- **Column Groups Configuration:** Define `COLUMN_GROUPS` dict mapping group names to column lists
- **Merged Indicators List:** Define `MERGED_INDICATORS` list of exact strings that trigger expansion
- **Post-Processing Pass:** Add `expand_merged_values()` function after initial row extraction
- **Case-Sensitive Matching:** Update fracture detection to use separate checks for `(f)` vs `(F)`
- **CSV Sanitization:** Add `sanitize_csv_value()` function that prepends `'` to formula-triggering characters
- **Exact Match Validation:** Use `value.strip() in MERGED_INDICATORS` rather than substring matching to prevent false positives

## Security Considerations

### CSV Injection Mitigation
The requirement to preserve leading `+` and potential `=` symbols creates a CSV Injection (Formula Injection) vulnerability when output is opened in Excel or Google Sheets. 

**Mitigation:** All CSV output values beginning with `+`, `-`, `=`, or `@` are prepended with a single quote (`'`) during CSV write. This prevents formula execution while preserving the visual value in spreadsheet applications.

```python
def sanitize_csv_value(value: str) -> str:
    """Prevent CSV injection by escaping formula-triggering characters."""
    if value and value[0] in ('+', '-', '=', '@'):
        return f"'{value}"
    return value
```

### Data Residency
Data processing is **Local-Only**. No external transmission of PDF content occurs. All extraction and transformation happens within the local execution environment with no external API calls.

## Files to Create/Modify
- `src/extraction/pdf_parser.py` â€” Add `COLUMN_GROUPS`, `MERGED_INDICATORS` constants; update fracture detection logic
- `src/extraction/postprocess.py` â€” Add `expand_merged_values()` function (or add to existing postprocessor)
- `src/extraction/csv_writer.py` â€” Add `sanitize_csv_value()` function for CSV injection prevention
- `tests/test_footnote_symbols.py` â€” New test file for symbol handling
- `tests/test_csv_sanitization.py` â€” New test file for CSV injection prevention
- `docs/data-dictionary.md` â€” Document symbol meanings

## Dependencies
- None - this enhancement can be implemented independently

## Out of Scope (Future)
- Automatic PDF legend parsing to discover symbol meanings â€” manual documentation for now
- Visual merged cell detection via PDF structure analysis â€” using indicator-based heuristic instead
- Support for additional footnote symbols beyond the four identified â€” add as discovered

## Acceptance Criteria
- [ ] Rows with `(f)` have `notes` column containing exactly `(f)`
- [ ] Rows with `(F)` have `notes` column containing exactly `(F)`
- [ ] Rows with `+` in permeability have `+` in BOTH `permeability_air_md` AND `permeability_klink_md`
- [ ] Rows with `<0.0001` in permeability have value in BOTH permeability columns
- [ ] Rows with `**` in saturation have `**` in ALL THREE saturation columns
- [ ] Existing rows without footnote symbols are unchanged
- [ ] At least one sample with `(f)` and one with `(F)` exist in test data to verify differentiation
- [ ] CSV output values starting with `+`, `-`, `=`, `@` are prepended with `'` to prevent formula injection
- [ ] Text values like `+10% correction` in non-indicator contexts do NOT trigger merged cell expansion (false positive prevention)

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
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0810 Privacy Audit - PASS
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
- At least 1 row with false positive text (e.g., `+10%` in a text field) to verify no unintended expansion

### CSV Injection Test Cases
- Verify `+` outputs as `'+` in CSV
- Verify `=SUM(A1)` (if present) outputs as `'=SUM(A1)`
- Verify `-1` numeric values are handled appropriately (context-dependent)
- Open output CSV in Excel and verify no formula execution warnings

### Manual Verification
1. Compare extraction output against source PDF visually for 5 random rows with footnotes
2. Verify column counts match expected (no shifted data from expansion logic)
3. Open CSV in Excel/Sheets and confirm no unexpected formula behavior

## Labels
`enhancement`, `data-extraction`, `csv`

## Effort Estimate
**Size: S/M** (4-6 hours)

## Original Brief
# Idea: Improved Footnote Symbol Handling

**Status:** Enhancement
**Effort:** Medium (4-6 hours)
**Value:** High - accuracy improvement

---

## Problem

The PDF table uses four footnote symbols with specific meanings. Current extraction handles them inconsistently:

| Symbol | Meaning | Current Handling | Issue |
|--------|---------|------------------|-------|
| `(f)` | Fracture (lowercase) | Captured | Not differentiated from (F) |
| `(F)` | Fracture (uppercase) | Captured | Not differentiated from (f) |
| `+` | Below detection | Partial | Should span both permeability columns |
| `<0.0001` | Below detection limit | Partial | Should span both permeability columns |
| `**` | No saturation data | Partial | Should span all three saturation columns |

---

## Observed Issues

### 1. (f) vs (F) Not Differentiated

The PDF distinguishes between lowercase `(f)` and uppercase `(F)` - likely indicating different fracture types or severity. Current code treats them identically.

```python
# Current (lossy)
if '(f)' in sample or '(F)' in sample:
    notes = 'fracture'

# Should preserve case
if '(f)' in sample:
    notes = 'fracture_minor'  # or preserve as '(f)'
elif '(F)' in sample:
    notes = 'fracture_major'  # or preserve as '(F)'
```

### 2. Merged Cell Values Not Spanning Columns

When `+` or `<0.0001` appears in permeability, it spans both Air and Klink columns in the PDF (merged cell). Current extraction puts it in one column only.

**PDF shows:**
```
| Permeability (md) |
| Air    | Klink   |
|      +          |  <- merged across both
```

**Current output:**
```csv
permeability_air_md,permeability_klink_md
+,
```

**Should be:**
```csv
permeability_air_md,permeability_klink_md
+,+
```

### 3. Saturation `**` Not Spanning Columns

Similar issue with `**` in saturation columns - should appear in Water, Oil, and Total.

---

## Proposal

1. **Preserve original symbol case** - `(f)` and `(F)` stored as-is
2. **Detect merged cell indicators** - `+`, `<0.0001`, `**`
3. **Replicate to spanned columns** - Apply value to all columns in the merge group

---

## Implementation

### Column Groups (Merge Targets)

```python
COLUMN_GROUPS = {
    'permeability': ['permeability_air_md', 'permeability_klink_md'],
    'saturation': ['saturation_water_pct', 'saturation_oil_pct', 'saturation_total_pct'],
}

MERGED_INDICATORS = ['+', '**', '<0.0001', '<']
```

### Detection Logic

```python
def expand_merged_values(row: dict) -> dict:
    """Expand merged cell values to all columns in group."""

    # Check permeability columns
    perm_vals = [row.get('permeability_air_md'), row.get('permeability_klink_md')]
    for val in perm_vals:
        if val and any(ind in str(val) for ind in MERGED_INDICATORS):
            # This was a merged cell - apply to both
            row['permeability_air_md'] = val
            row['permeability_klink_md'] = val
            break

    # Check saturation columns
    sat_vals = [row.get(c) for c in COLUMN_GROUPS['saturation']]
    for val in sat_vals:
        if val == '**':
            # Apply to all three
            for col in COLUMN_GROUPS['saturation']:
                row[col] = '**'
            break

    return row
```

### Fracture Case Preservation

```python
def extract_fracture_indicator(sample_text: str) -> str | None:
    """Preserve exact fracture indicator."""
    if '(F)' in sample_text:
        return '(F)'
    elif '(f)' in sample_text:
        return '(f)'
    return None
```

---

## Testing

```python
def test_fracture_case_preserved():
    """Verify (f) and (F) are differentiated."""
    # Find samples with each type
    lowercase = [r for r in rows if r.get('notes') == '(f)']
    uppercase = [r for r in rows if r.get('notes') == '(F)']

    # Should have both types
    assert len(lowercase) > 0
    assert len(uppercase) > 0
    assert lowercase != uppercase

def test_merged_permeability():
    """Verify + appears in both permeability columns."""
    plus_rows = [r for r in rows if r.get('permeability_air_md') == '+']
    for row in plus_rows:
        assert row['permeability_klink_md'] == '+'

def test_merged_saturation():
    """Verify ** appears in all three saturation columns."""
    star_rows = [r for r in rows if r.get('saturation_water_pct') == '**']
    for row in star_rows:
        assert row['saturation_oil_pct'] == '**'
        assert row['saturation_total_pct'] == '**'
```

---

## Next Steps

1. [ ] Document exact meaning of (f) vs (F) from PDF legend
2. [ ] Identify all merged cell patterns in source PDF
3. [ ] Update extraction logic to detect merges
4. [ ] Add column group expansion
5. [ ] Update tests