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
def to_analytics_format(rows: list[dict]) -> list[dict]:
    """Transform extraction output to analytics-ready format."""

    analytics_rows = []
    for row in rows:
        a = {}

        # Sample number - extract fracture indicator
        sample = row['sample_number']
        if '(F)' in sample:
            a['sample_number'] = sample.replace('(F)', '').strip()
            a['is_fracture'] = True
            a['fracture_type'] = 'F'
        elif '(f)' in sample:
            a['sample_number'] = sample.replace('(f)', '').strip()
            a['is_fracture'] = True
            a['fracture_type'] = 'f'
        else:
            a['sample_number'] = sample
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

1. [ ] Decide on NA representation (NA vs empty vs NaN)
2. [ ] Decide on below-detection handling (NA vs limit value)
3. [ ] Implement `to_analytics_format()` function
4. [ ] Add `--analytics` flag to CLI
5. [ ] Update output documentation
