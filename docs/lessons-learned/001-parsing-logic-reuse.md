# Lessons Learned: Parsing Logic Reuse

**Date:** 2026-01-29
**Issue:** Minimal pipeline had incorrect field alignment for fracture samples
**Root Cause:** Code duplication with oversimplification

---

## What Happened

Two extraction pipelines were built:

1. **Database approach** (`core_analysis.py`) - Built first, correct parsing logic
2. **Minimal approach** (`core_analysis_minimal.py`) - Built second, simplified (buggy) parsing logic

The minimal version was created to demonstrate a "small pipeline" for grading. When writing it, I oversimplified the `_parse_sample_lines()` function instead of porting the tested logic from the database version.

**Result:** Fracture samples had values shifted into wrong columns.

| Field | Minimal (buggy) | Database (correct) |
|-------|-----------------|-------------------|
| porosity_ambient | (blank) | 1.2 |
| grain_density | 0.8 | 2.7 |
| sat_water | 77.2 | 76.4 |

---

## Why It Happened

1. **False assumption:** "Simpler code = fewer bugs"
   - Reality: The parsing logic has edge cases (fractures, below-detection) that require specific handling

2. **Speed vs accuracy conflation:**
   - The database approach is slow because of extraction + database I/O
   - The parsing logic is NOT what makes it slow
   - I incorrectly assumed I needed "simpler" parsing for the "faster" approach

3. **No output comparison:**
   - I claimed both approaches produced "138 samples" without comparing the actual field values
   - Row count equality ≠ data equality

---

## The Fix

Ported the correct `_parse_sample_lines()` logic from `core_analysis.py` to `core_analysis_minimal.py`.

**Time impact:** None. Parsing time is ~5ms out of 370ms total. The complexity is in the PDF extraction, not the parsing.

---

## Lessons

### 1. Don't rewrite working code - copy it

When creating a "minimal" or "simplified" version:
- Copy the working logic first
- Then simplify the scaffolding around it
- The core algorithm should be identical

### 2. Separate concerns: Extraction vs Parsing

| Component | Database Approach | Minimal Approach |
|-----------|------------------|------------------|
| PDF extraction | Extract ALL elements (slow) | Extract only text (fast) |
| Storage | SQLite database (slow) | None (fast) |
| **Parsing logic** | **Same** | **Same** |

The parsing logic should be identical. The speed difference comes from what you extract and where you store it.

### 3. Compare outputs, not just counts

```bash
# Wrong: only checks count
wc -l minimal.csv database.csv

# Right: compares actual content
diff minimal.csv database.csv
head -5 minimal.csv database.csv
```

### 4. Test edge cases explicitly

The unit tests I wrote tested:
- Normal samples ✓
- Fracture samples ✓ (but didn't verify all fields)
- Below-detection samples ✓

Missing: Field-level assertions for fracture samples that would have caught the bug.

---

## Prevention

1. **Single source of truth:** Core parsing logic should exist in ONE place, imported by both pipelines
2. **Diff-based testing:** Add tests that compare minimal vs database output
3. **Field-level assertions:** Test each field value, not just "sample exists"

---

## Code Change

```python
# Before (buggy - oversimplified)
if val == '+':
    sample.notes = "fracture"
    idx += 1
    if idx < len(values):
        sample.porosity_ambient_pct = values[idx]  # Wrong: skipped fields
        idx += 1

# After (correct - ported from database version)
if val == '+':
    notes = "fracture"
    idx += 1
    if idx < len(values):
        porosity_amb = self._parse_float(values[idx])
        idx += 1
    if idx < len(values):
        grain_density = self._parse_float(values[idx])
        idx += 1
    # Then continue to saturations...
```

---

## Metrics

| Metric | Before Fix | After Fix |
|--------|------------|-----------|
| Processing time | 359 ms | 371 ms |
| Samples extracted | 138 | 138 |
| Fracture samples correct | 0% | 100% |
| Field alignment errors | ~40 samples | 0 samples |
