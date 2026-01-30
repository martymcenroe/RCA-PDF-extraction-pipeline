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
3. System transforms symbols (`+`, `**`, `<0.0001`) to NA with flag columns
4. System extracts fracture indicators from sample numbers to separate columns
5. Result: Three output files including `core_analysis_analytics.csv`

### Scenario 2: Load in Pandas
1. User runs `pd.read_csv('core_analysis_analytics.csv', na_values=['NA'])`
2. Numeric columns automatically parse as `float64`
3. Boolean flag columns indicate data quality issues
4. Result: Ready for analysis without string-to-numeric conversion errors

### Scenario 3: Load in R
1. User runs `read.csv('core_analysis_analytics.csv')`
2. R recognizes `NA` as missing values natively
3. Result: Proper `NA` handling in statistical functions

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

### Output Schema
1. `sample_number` — cleaned (no parenthetical suffixes)
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

## Security Considerations
No security implications — this is a data formatting transformation with no external access or elevated permissions.

## Files to Create/Modify
- `src/extractors/core_analysis.py` — Add `to_analytics_format()` function
- `src/cli/extract.py` — Add `--analytics` flag
- `tests/test_analytics_format.py` — New test file for analytics transformations
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

## Definition of Done

### Implementation
- [ ] `to_analytics_format()` function implemented
- [ ] `to_numeric_or_na()` helper function implemented
- [ ] CLI `--analytics` flag added
- [ ] Unit tests written and passing

### Tools
- [ ] Update extraction CLI help text

### Documentation
- [ ] Document analytics CSV schema in output-formats.md
- [ ] Add usage examples for pandas and R
- [ ] Update README.md with new `--analytics` flag

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] All existing tests pass
- [ ] New analytics format tests pass
- [ ] Manual verification with pandas and R import

## Testing Notes

**Force below-detection state:**
Use test PDF with `+` symbols in permeability columns.

**Force no-saturation state:**
Use test PDF with `**` in saturation columns.

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