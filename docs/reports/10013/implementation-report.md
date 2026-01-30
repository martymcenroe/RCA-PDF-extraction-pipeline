# Implementation Report: Issue #13 - Extract Headers from PDF

## Issue Reference
- **Issue:** [#13](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/issues/13)
- **LLD:** `docs/lld/active/LLD-013.md`
- **Branch:** `13-extract-pdf-headers`

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/core_analysis.py` | Modified | Added `_extract_headers_from_db()` method and supporting constants |
| `tests/test_header_extraction.py` | Created | 10 unit tests for header extraction |
| `data/output/spec/core_analysis.csv` | Modified | Updated baseline with correct headers |

## Technical Approach

### Header Extraction Algorithm

1. Query `text_spans` table for header region (y=170-230 on page 39)
2. Define column boundaries based on data column positions
3. Handle spanning headers (parent categories that span multiple columns)
4. Exclude misaligned headers (e.g., "Sample" at y=193 that falls in Depth column)
5. Concatenate text vertically within each column

### Key Constants Added

```python
COLUMN_BOUNDARIES = [
    (40, 85),    # Core Number
    (85, 135),   # Sample Number
    ...
]

SPANNING_HEADERS = {
    (193, 259): [3, 4],  # "Permeability," spans columns 3-4
    ...
}

EXCLUDED_HEADERS = [
    (193, 159),  # "Sample" misaligned
]
```

## Header Comparison

| Before (Hardcoded) | After (Extracted from PDF) |
|--------------------|---------------------------|
| Depth (ft) | Sample Depth, feet |
| Permeability (md) \| Air | Permeability, millidarcys to Air |
| Permeability (md) \| Klink | Permeability, millidarcys Klinkenberg |
| Porosity (%) \| Ambient | Porosity, percent Ambient |
| Grain Density (g/cc) | Grain Density, gm/cc |
| Fluid Saturations (%) \| Water | Fluid Saturations, percent Water |

## Verification

- Row count: 138 data rows (unchanged)
- Headers: Now match actual PDF text
- All 10 tests pass
