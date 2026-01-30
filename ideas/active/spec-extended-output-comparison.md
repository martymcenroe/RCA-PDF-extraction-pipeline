# Idea: Spec vs Extended Output Comparison

**Status:** Required (quality gate)
**Effort:** Low (1-2 hours)
**Value:** Critical - ensures both pipelines produce identical results

---

## Problem

We have two extraction pipelines:

1. **Spec (minimal):** PDF → PyMuPDF → CSV/JSON (359ms)
2. **Extended (database):** PDF → Elementizer → SQLite → Extractor → CSV/JSON (6.7s)

Both should produce **identical** output. If they don't, one (or both) has a bug.

---

## Current State

| Output | Location |
|--------|----------|
| Spec | `data/output/spec/core_analysis.csv` |
| Extended | `data/output/extended/core_analysis.csv` |

These have never been formally compared.

---

## Proposal

Create a comparison script that:

1. Loads both CSV files
2. Compares row-by-row, column-by-column
3. Reports any differences
4. Fails CI if differences found

---

## Implementation

```python
#!/usr/bin/env python3
"""Compare spec and extended outputs for exact match."""

import pandas as pd
import sys

def compare_outputs(spec_path: str, extended_path: str) -> bool:
    """Compare two CSV files for exact match.

    Returns True if identical, False otherwise.
    """
    spec_df = pd.read_csv(spec_path)
    ext_df = pd.read_csv(extended_path)

    issues = []

    # Check shape
    if spec_df.shape != ext_df.shape:
        issues.append(f"Shape mismatch: spec={spec_df.shape}, extended={ext_df.shape}")

    # Check columns
    if list(spec_df.columns) != list(ext_df.columns):
        spec_cols = set(spec_df.columns)
        ext_cols = set(ext_df.columns)
        issues.append(f"Column mismatch:")
        issues.append(f"  Only in spec: {spec_cols - ext_cols}")
        issues.append(f"  Only in extended: {ext_cols - spec_cols}")

    # Check values row by row
    if spec_df.shape == ext_df.shape:
        for idx in range(len(spec_df)):
            spec_row = spec_df.iloc[idx]
            ext_row = ext_df.iloc[idx]

            for col in spec_df.columns:
                spec_val = spec_row[col]
                ext_val = ext_row[col]

                # Handle NaN comparison
                if pd.isna(spec_val) and pd.isna(ext_val):
                    continue

                if spec_val != ext_val:
                    issues.append(
                        f"Row {idx}, column '{col}': "
                        f"spec='{spec_val}' vs extended='{ext_val}'"
                    )

    # Report results
    if issues:
        print("❌ COMPARISON FAILED")
        print("=" * 50)
        for issue in issues[:20]:  # Limit output
            print(issue)
        if len(issues) > 20:
            print(f"... and {len(issues) - 20} more differences")
        return False
    else:
        print("✓ COMPARISON PASSED")
        print(f"  Rows: {len(spec_df)}")
        print(f"  Columns: {len(spec_df.columns)}")
        print("  All values match exactly")
        return True


if __name__ == '__main__':
    spec_path = 'data/output/spec/core_analysis.csv'
    extended_path = 'data/output/extended/core_analysis.csv'

    if len(sys.argv) == 3:
        spec_path = sys.argv[1]
        extended_path = sys.argv[2]

    success = compare_outputs(spec_path, extended_path)
    sys.exit(0 if success else 1)
```

---

## Expected Output

### If Match:
```
✓ COMPARISON PASSED
  Rows: 138
  Columns: 12
  All values match exactly
```

### If Mismatch:
```
❌ COMPARISON FAILED
==================================================
Row 45, column 'permeability_air_md': spec='+' vs extended=''
Row 45, column 'permeability_klink_md': spec='+' vs extended='+'
Row 102, column 'saturation_water_pct': spec='**' vs extended='NA'
... and 12 more differences
```

---

## JSON Comparison

Also compare JSON outputs for structural equality:

```python
import json

def compare_json(spec_path: str, extended_path: str) -> bool:
    """Compare JSON outputs."""
    with open(spec_path) as f:
        spec_data = json.load(f)
    with open(extended_path) as f:
        ext_data = json.load(f)

    # Compare page classifications
    if spec_data.get('classifications') != ext_data.get('classifications'):
        print("Classification mismatch")
        return False

    # Compare sample data
    spec_samples = spec_data.get('samples', [])
    ext_samples = ext_data.get('samples', [])

    if len(spec_samples) != len(ext_samples):
        print(f"Sample count mismatch: {len(spec_samples)} vs {len(ext_samples)}")
        return False

    for i, (spec_s, ext_s) in enumerate(zip(spec_samples, ext_samples)):
        if spec_s != ext_s:
            print(f"Sample {i} mismatch:")
            print(f"  Spec: {spec_s}")
            print(f"  Extended: {ext_s}")
            return False

    return True
```

---

## CI Integration

Add to test suite or GitHub Actions:

```yaml
- name: Compare outputs
  run: |
    python scripts/compare_outputs.py \
      data/output/spec/core_analysis.csv \
      data/output/extended/core_analysis.csv
```

---

## Handling Known Differences

If pipelines intentionally produce different output (e.g., different metadata), document and exclude:

```python
IGNORE_COLUMNS = ['extraction_timestamp', 'pipeline_version']

for col in spec_df.columns:
    if col in IGNORE_COLUMNS:
        continue
    # ... compare
```

---

## Next Steps

1. [ ] Create `scripts/compare_outputs.py`
2. [ ] Run initial comparison
3. [ ] Fix any discrepancies found
4. [ ] Add to CI pipeline
5. [ ] Document any intentional differences
