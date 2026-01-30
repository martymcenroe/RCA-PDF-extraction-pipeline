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
