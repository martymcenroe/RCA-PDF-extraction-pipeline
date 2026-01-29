# Idea: Automated Data Validation & Analysis

**Status:** Brief / Proposal
**Effort:** Low (2-4 hours)
**Value:** High - catches parsing errors automatically

---

## Problem

Manual verification of 138 rows is tedious and error-prone. A grader might spot-check 5 rows and miss systematic errors (e.g., all fracture samples have shifted columns).

---

## Proposal

Build a data validation script that:

1. **Type checking** - Verify each column has expected data types
2. **Range validation** - Flag values outside expected ranges
3. **Outlier detection** - Identify statistical anomalies
4. **Consistency checks** - Cross-validate related fields
5. **Summary statistics** - Quick sanity check of distributions

---

## Implementation

### Column Validation Rules

| Column | Type | Valid Range | Notes |
|--------|------|-------------|-------|
| core_number | int | 1-10 | Single digit in this dataset |
| sample_number | string | pattern `\d+-\d+` | May have (F) or (f) suffix |
| depth_feet | float | 9500-10000 | This well's depth range |
| permeability_air_md | float | 0-100 | Can be blank for fractures |
| permeability_klink_md | float | 0-100 | Can be blank |
| porosity_ambient_pct | float | 0-15 | Typical range for this formation |
| porosity_ncs_pct | float | 0-15 | Should be ≤ ambient |
| grain_density_gcc | float | 2.0-3.0 | Rock density |
| saturation_water_pct | float | 0-100 | |
| saturation_oil_pct | float | 0-100 | |
| saturation_total_pct | float | 0-100 | Should ≈ water + oil |
| page_number | int | 39-42 | Only table pages |

### Outlier Detection

```python
# Flag values > 3 standard deviations from mean
for col in numeric_columns:
    mean = df[col].mean()
    std = df[col].std()
    outliers = df[abs(df[col] - mean) > 3 * std]
    if len(outliers) > 0:
        print(f"Outliers in {col}: {outliers}")
```

### Consistency Checks

```python
# Saturation total should equal water + oil (within tolerance)
df['sat_calc'] = df['saturation_water_pct'] + df['saturation_oil_pct']
mismatches = df[abs(df['saturation_total_pct'] - df['sat_calc']) > 0.5]

# Depth should increase monotonically within each core
for core in df['core_number'].unique():
    core_df = df[df['core_number'] == core]
    if not core_df['depth_feet'].is_monotonic_increasing:
        print(f"Non-monotonic depth in core {core}")

# Fracture samples should have blank permeability
fractures = df[df['notes'].str.contains('fracture', na=False)]
if fractures['permeability_air_md'].notna().any():
    print("Warning: Fracture sample has permeability value")
```

### Summary Statistics Output

```
=== Data Validation Report ===

Samples: 138
Pages: 4 (39, 40, 41, 42)
Cores: 2

Depth Range: 9580.5 - 9727.5 ft
Porosity Range: 0.3 - 8.5 %
Grain Density Range: 2.13 - 2.76 g/cc

Fracture Samples: 42 (30%)
Below Detection: 8 (6%)
No Saturation Data: 45 (33%)

Outliers Detected: 0
Consistency Errors: 0

VALIDATION: PASSED
```

---

## Deliverable

A script `scripts/validate_output.py` that:

```bash
python scripts/validate_output.py data/output/core_analysis_minimal.csv

# Output:
# ✓ 138 samples loaded
# ✓ All columns have valid types
# ✓ All values in expected ranges
# ✓ No outliers detected
# ✓ Saturation totals consistent
# ✓ Depths monotonically increasing
#
# VALIDATION PASSED
```

---

## Benefits

1. **Catches parsing bugs** - Shifted columns would fail range checks
2. **Reproducible** - Same validation every time
3. **Fast** - Runs in <1 second
4. **Documentable** - Output can be included in reports
5. **CI/CD ready** - Can be added to test suite

---

## Next Steps

1. [ ] Implement `validate_output.py`
2. [ ] Add to test suite as integration test
3. [ ] Generate validation report for grader
4. [ ] Consider adding to pipeline as post-processing step
