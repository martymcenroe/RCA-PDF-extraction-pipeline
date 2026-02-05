---
repo: martymcenroe/RCA-PDF-extraction-pipeline
issue: 6
url: https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/issues/6
fetched: 2026-02-05T02:17:13.247952Z
---

# Issue #6: Analytics-Ready CSV Output Format for Data Analysis Tools

# Analytics-Ready CSV Output Format for Data Analysis Tools

## User Story
As a **data analyst**,
I want **a CSV output format optimized for pandas, R, and Excel pivot tables**,
So that **I can import core analysis data directly without manual cleanup of symbols and empty cells**.

## Objective
Add a third output format (`core_analysis_analytics.csv`) that transforms human-readable symbols into analysis-ready values with proper NA handling and flag columns.

## UX Flow

### Scenario 1: Generate Analytics CSV
1. User runs extraction with `--analytics` flag
2. System extracts data from PDF as normal
3. System sanitizes string fields to prevent CSV injection
4. System transforms symbols (`+`, `**`, `<0.0001`) to NA with flag columns
5. System extracts fracture indicators from sample numbers to separate columns
6. Result: Three output files including `core_analysis_analytics.csv`

### Scenario 2: Load in Pandas
1. User runs `pd.read_csv('core_analysis_analytics.csv', na_values=['NA'])`
2. Numeric columns automatically parse as `float64`
3. Boolean flag columns indicate data quality issues
4. Result: Ready for analysis without string-to-numeric conversion errors

### Scenario 3: Load in R
1. User runs `read.csv('core_analysis_analytics.csv')`
2. R recognizes `NA` as missing values natively
3. Result: Proper `NA` handling in statistical functions

### Scenario 4: Transformation Failure (Error Case)
1. User runs extraction with `--analytics` flag
2. System extracts data from PDF successfully
3. `to_analytics_format()` encounters unexpected data type or transformation error
4. System logs detailed error message with row/field context
5. System continues with extraction, skips analytics file generation (Fail Open/Partial Success)
6. Result: Original `core_analysis.csv` and `core_analysis.json` are produced; analytics CSV is not generated; user is notified of partial success with actionable error message

## Requirements

### Data Type Integrity
1. Numeric columns contain only numbers or `NA` (no symbols, operators, or mixed content)
2. Boolean flag columns use `TRUE`/`FALSE` values
3. String columns contain clean text without embedded indicators

### Symbol Transformations
1. Empty cells → `NA`
2. `+` (below detection) → `NA` with `permeability_below_detection = TRUE`
3. `<0.0001` → `NA` with `permeability_below_detection = TRUE`
4. `**` (no saturation data) → `NA` across all saturation columns with `saturation_no_data = TRUE`
5. `(F)` or `(f)` suffix → extracted to `is_fracture` and `fracture_type` columns

### Security: CSV Injection Prevention
1. All string fields MUST be sanitized before CSV output
2. Leading characters `=`, `+`, `-`, `@`, `\t`, `\r` MUST be escaped by prepending a single quote (`'`)
3. Sanitization applies to `sample_number`, `fracture_type`, and any other text fields
4. Sanitization function MUST be applied as final step before CSV serialization

### Output Schema
1. `sample_number` — cleaned (no parenthetical suffixes), sanitized for CSV injection
2. `is_fracture` — boolean flag
3. `fracture_type` — `F`, `f`, or `NA`
4. `depth_feet` — numeric or NA
5. `permeability_air_md` — numeric or NA
6. `permeability_klink_md` — numeric or NA
7. `permeability_below_detection` — boolean flag
8. `porosity_ambient_pct` — numeric or NA
9. `porosity_ncs_pct` — numeric or NA
10. `saturation_water_pct` — numeric or NA
11. `saturation_oil_pct` — numeric or NA
12. `saturation_total_pct` — numeric or NA
13. `saturation_no_data` — boolean flag
14. `grain_density_gcc` — numeric or NA

## Technical Approach
- **Transformation Layer:** New `to_analytics_format()` function processes extraction output
- **NA Representation:** Use string `NA` (compatible with both R and pandas via `na_values` parameter)
- **Below Detection Strategy:** Option A — NA with flag column (preserves information without false precision)
- **CLI Integration:** Add `--analytics` flag to include analytics CSV in output
- **CSV Injection Sanitization:** New `sanitize_csv_string()` function prepends `'` to strings starting with `=`, `+`, `-`, `@`, `\t`, `\r`
- **Error Handling Strategy:** Fail Open/Partial Success — if `to_analytics_format()` fails, log error and skip analytics file while still producing standard outputs

## Security Considerations
- **CSV Injection Prevention:** String fields are sanitized to prevent formula injection when opened in Excel. Any string starting with `=`, `+`, `-`, `@`, tab, or carriage return is prefixed with a single quote to prevent execution as a formula.
- **No External Access:** This is a data formatting transformation with no external network access or elevated permissions.
- **Input Validation:** All source data originates from controlled PDF extraction; sanitization provides defense-in-depth.

## Files to Create/Modify
- `src/extractors/core_analysis.py` — Add `to_analytics_format()` function with error handling
- `src/utils/csv_sanitizer.py` — New file for `sanitize_csv_string()` function
- `src/cli/extract.py` — Add `--analytics` flag
- `tests/test_analytics_format.py` — New test file for analytics transformations
- `tests/test_csv_sanitizer.py` — New test file for CSV injection prevention
- `tests/fixtures/test_analytics_edge_cases.pdf` — Static fixture with `+` symbols, `**` markers, and injection payloads
- `docs/output-formats.md` — Document new analytics format

## Dependencies
- None — standalone enhancement

## Out of Scope (Future)
- **Configurable NA representation** — hardcode `NA` for now, make configurable later
- **Detection limit values** — don't substitute `0.0001` for below-detection, use NA
- **Additional flag columns** — start with permeability and saturation flags only

## Acceptance Criteria
- [ ] Running with `--analytics` produces `core_analysis_analytics.csv`
- [ ] No empty cells exist in analytics output (all converted to `NA`)
- [ ] Numeric columns parse as `float64` in pandas with `na_values=['NA']`
- [ ] Sample numbers contain no parenthetical suffixes
- [ ] `is_fracture` column correctly identifies fracture samples
- [ ] `permeability_below_detection` is `TRUE` for rows with `+` or `<0.0001`
- [ ] `saturation_no_data` is `TRUE` for rows with `**` marker
- [ ] Original `core_analysis.csv` unchanged (human-readable format preserved)
- [ ] String fields with leading `=`, `+`, `-`, `@` are prefixed with `'` in CSV output
- [ ] Transformation failures log error and skip analytics file without aborting extraction
- [ ] Error message includes row/field context for debugging

## Definition of Done

### Implementation
- [ ] `to_analytics_format()` function implemented with try/catch error handling
- [ ] `to_numeric_or_na()` helper function implemented
- [ ] `sanitize_csv_string()` function implemented in `src/utils/csv_sanitizer.py`
- [ ] CLI `--analytics` flag added
- [ ] Unit tests written and passing

### Fixtures
- [ ] Create static fixture `tests/fixtures/test_analytics_edge_cases.pdf` with:
  - `+` symbols in permeability columns
  - `**` in saturation columns
  - Sample numbers containing `=SUM(A1)`, `+cmd|`, `-1+1`, `@SUM(A1)` for injection testing

### Tools
- [ ] Update extraction CLI help text

### Documentation
- [ ] Document analytics CSV schema in output-formats.md
- [ ] Document CSV injection sanitization behavior
- [ ] Add usage examples for pandas and R
- [ ] Update README.md with new `--analytics` flag

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] All existing tests pass
- [ ] New analytics format tests pass
- [ ] CSV injection sanitization tests pass
- [ ] Manual verification with pandas and R import
- [ ] Manual verification that sanitized CSV opens safely in Excel

## Testing Notes

**Force below-detection state:**
Use test fixture `test_analytics_edge_cases.pdf` with `+` symbols in permeability columns.

**Force no-saturation state:**
Use test fixture `test_analytics_edge_cases.pdf` with `**` in saturation columns.

**Test CSV injection prevention:**
```python
def test_csv_injection_sanitization():
    """Verify dangerous strings are sanitized."""
    from src.utils.csv_sanitizer import sanitize_csv_string
    
    assert sanitize_csv_string("=SUM(A1)") == "'=SUM(A1)"
    assert sanitize_csv_string("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_string("-1+1") == "'-1+1"
    assert sanitize_csv_string("@SUM(A1)") == "'@SUM(A1)"
    assert sanitize_csv_string("normal_value") == "normal_value"
```

**Test transformation failure handling:**
```python
def test_analytics_transformation_failure_partial_success():
    """Verify extraction continues if analytics transformation fails."""
    # Mock to_analytics_format to raise exception
    # Verify core_analysis.csv still produced
    # Verify analytics CSV not produced
    # Verify error logged with context
```

**Verify pandas compatibility:**
```python
import pandas as pd
df = pd.read_csv('core_analysis_analytics.csv', na_values=['NA'])
assert df['permeability_air_md'].dtype == 'float64'
assert df['is_fracture'].dtype == 'bool' or df['is_fracture'].isin([True, False, 'TRUE', 'FALSE']).all()
```

**Verify R compatibility:**
```r
df <- read.csv('core_analysis_analytics.csv')
stopifnot(is.numeric(df$permeability_air_md) || all(is.na(df$permeability_air_md)))
```

## Original Brief
# Idea: Data Analysis Prep Output Format

**Status:** Enhancement
**Effort:** Low (2-3 hours)
**Value:** High - enables downstream analysis

---

## Problem

Current CSV output is human-readable but not optimized for data analysis tools (pandas, R, Excel pivot tables). Issues:

| Current | Problem | Analytics Expectation |
|---------|---------|----------------------|
| Empty cell | Ambiguous - missing or zero? | `NA` or `NaN` |
| `**` | String in numeric column | `NA` with metadata |
| `+` | String in numeric column | `NA` or `0` with flag |
| `<0.0001` | String with operator | Numeric or `NA` |
| `(f)` suffix | Mixed in sample number | Separate column |

---

## Proposal

Create a third output format: `core_analysis_analytics.csv`

Design principles:
1. **Numeric columns contain only numbers or NA**
2. **Flags/indicators in separate boolean columns**
3. **Standard NA representation** (`NA` for R, empty or `NaN` for pandas)
4. **No ambiguity** - every cell has clear meaning

---

## Schema Transformation

### Current Schema
```
sample_number, depth_feet, permeability_air_md, permeability_klink_md, ...
6-1(f), 9580.5, +, +, ...
```

### Analytics Schema
```
sample_number, is_fracture, fracture_type, depth_feet,
permeability_air_md, permeability_klink_md, permeability_below_detection,
porosity_ambient_pct, porosity_ncs_pct,
saturation_water_pct, saturation_oil_pct, saturation_total_pct, saturation_no_data,
grain_density_gcc
```

---

## Value Transformations

### Empty Cells → NA

```python
def to_analytics_value(val, column_type):
    if val is None or val == '':
        return 'NA'
    return val
```

### Below Detection (`+`, `<0.0001`)

**Option A: NA with flag column**
```csv
permeability_air_md,permeability_below_detection
NA,TRUE
0.042,FALSE
```

**Option B: Use detection limit value**
```csv
permeability_air_md,permeability_below_detection
0.0001,TRUE
0.042,FALSE
```

**Option C: Keep as string (not recommended)**
```csv
permeability_air_md
<0.0001
```

**Recommendation:** Option A (NA with flag). Reasoning:
- Preserves information that value is below detection
- Doesn't introduce false precision
- Analytics tools handle NA gracefully

### No Saturation Data (`**`)

Transform to NA across all three saturation columns:

```python
if any(row[col] == '**' for col in SATURATION_COLS):
    for col in SATURATION_COLS:
        row[col] = 'NA'
    row['saturation_no_data'] = True
```

### Fracture Indicator

Extract from sample number into separate columns:

```python
# Input: "6-1(F)"
# Output:
sample_number = "6-1"
is_fracture = True
fracture_type = "F"  # or "f"
```

---

## Output Files

| File | Purpose | Format |
|------|---------|--------|
| `core_analysis.csv` | Human readable, matches PDF | Original symbols preserved |
| `core_analysis.json` | Structured data | Original symbols preserved |
| `core_analysis_analytics.csv` | Data analysis | NA values, flag columns |

---

## Implementation

```python
def sanitize_csv_string(val: str) -> str:
    """Prevent CSV injection by escaping dangerous leading characters."""
    if val and isinstance(val, str) and len(val) > 0:
        if val[0] in ('=', '+', '-', '@', '\t', '\r'):
            return "'" + val
    return val

def to_analytics_format(rows: list[dict]) -> list[dict]:
    """Transform extraction output to analytics-ready format."""

    analytics_rows = []
    for row in rows:
        try:
            a = {}

            # Sample number - extract fracture indicator
            sample = row['sample_number']
            if '(F)' in sample:
                a['sample_number'] = sanitize_csv_string(sample.replace('(F)', '').strip())
                a['is_fracture'] = True
                a['fracture_type'] = 'F'
            elif '(f)' in sample:
                a['sample_number'] = sanitize_csv_string(sample.replace('(f)', '').strip())
                a['is_fracture'] = True
                a['fracture_type'] = 'f'
            else:
                a['sample_number'] = sanitize_csv_string(sample)
                a['is_fracture'] = False
                a['fracture_type'] = 'NA'

            # Numeric fields - convert empty/symbols to NA
            a['depth_feet'] = to_numeric_or_na(row['depth_feet'])

            # Permeability - handle below detection
            perm_air = row['permeability_air_md']
            perm_klink = row['permeability_klink_md']
            if perm_air in ['+', '<0.0001', ''] or perm_klink in ['+', '<0.0001', '']:
                a['permeability_air_md'] = 'NA'
                a['permeability_klink_md'] = 'NA'
                a['permeability_below_detection'] = True
            else:
                a['permeability_air_md'] = to_numeric_or_na(perm_air)
                a['permeability_klink_md'] = to_numeric_or_na(perm_klink)
                a['permeability_below_detection'] = False

            # Saturation - handle no data
            if row.get('saturation_water_pct') == '**':
                a['saturation_water_pct'] = 'NA'
                a['saturation_oil_pct'] = 'NA'
                a['saturation_total_pct'] = 'NA'
                a['saturation_no_data'] = True
            else:
                a['saturation_water_pct'] = to_numeric_or_na(row['saturation_water_pct'])
                a['saturation_oil_pct'] = to_numeric_or_na(row['saturation_oil_pct'])
                a['saturation_total_pct'] = to_numeric_or_na(row['saturation_total_pct'])
                a['saturation_no_data'] = False

            # Other numeric fields
            a['porosity_ambient_pct'] = to_numeric_or_na(row['porosity_ambient_pct'])
            a['porosity_ncs_pct'] = to_numeric_or_na(row['porosity_ncs_pct'])
            a['grain_density_gcc'] = to_numeric_or_na(row['grain_density_gcc'])

            analytics_rows.append(a)
        except Exception as e:
            # Log error with context and re-raise to trigger partial success handling
            raise TransformationError(f"Failed to transform row {row.get('sample_number', 'unknown')}: {e}")

    return analytics_rows

def to_numeric_or_na(val):
    """Convert to float or NA."""
    if val is None or val == '':
        return 'NA'
    try:
        return float(str(val).replace(',', ''))
    except ValueError:
        return 'NA'
```

---

## Testing

```python
def test_analytics_no_empty_cells():
    """Verify no empty cells in analytics output."""
    df = pd.read_csv('core_analysis_analytics.csv')
    # Empty strings should not exist
    assert not (df == '').any().any()

def test_analytics_numeric_columns():
    """Verify numeric columns are actually numeric."""
    df = pd.read_csv('core_analysis_analytics.csv', na_values=['NA'])
    numeric_cols = ['depth_feet', 'permeability_air_md', 'porosity_ambient_pct']
    for col in numeric_cols:
        assert df[col].dtype in ['float64', 'int64'] or df[col].isna().all()

def test_analytics_fracture_extracted():
    """Verify fracture indicator extracted to separate column."""
    df = pd.read_csv('core_analysis_analytics.csv')
    # No parentheses in sample_number
    assert not df['sample_number'].str.contains(r'\(', regex=True).any()
    # Fracture info in separate columns
    assert 'is_fracture' in df.columns
    assert 'fracture_type' in df.columns
```

---

## Next Steps

1. [x] Decide on NA representation (NA vs empty vs NaN) — **Decision: NA**
2. [x] Decide on below-detection handling (NA vs limit value) — **Decision: NA with flag**
3. [ ] Implement `to_analytics_format()` function
4. [ ] Implement `sanitize_csv_string()` function
5. [ ] Create test fixture `test_analytics_edge_cases.pdf`
6. [ ] Add `--analytics` flag to CLI
7. [ ] Update output documentation

---

**Labels:** `enhancement`, `data-integrity`
**Estimate:** S/M