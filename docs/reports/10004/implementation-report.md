# Implementation Report: Issue #4 - Improved Footnote Symbol Handling

## Issue Reference
- **Issue:** [#4](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/issues/4)
- **LLD:** `docs/lld/active/safe/LLD-004.md`
- **Branch:** `4-footnote-symbols`

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/core_analysis.py` | Modified | Added merged cell expansion, removed notes column |
| `src/output/csv_sanitizer.py` | Modified | Fixed to not escape standalone indicators like `+`, `**` |
| `tests/test_footnote_symbols.py` | Created | 11 unit tests for symbol handling |
| `tests/fixtures/stub_samples.py` | Created | Stub data for offline testing |
| `tests/fixtures/__init__.py` | Created | Package init |
| `data/output/spec/core_analysis.csv` | Modified | Updated baseline (12 columns, no Notes) |

## Design Decisions

### 1. Module-Level Constants
Added constants at module level per LLD spec:
- `FRACTURE_INDICATOR_RE`: Compiled regex for performance
- `MAX_SAMPLE_LINES = 20`: Safety limit
- `COLUMN_GROUPS`: Defines permeability and saturation column groups
- `MERGED_INDICATORS`: List of indicators that trigger replication
- `ALLOWED_OUTPUT_ROOTS`: Security whitelist for output paths

### 2. Fracture Indicator Preservation
- Used compiled regex `r'\((f|F)\)$'` to match end of sample number
- Preserve exact case in sample_number field: `1-9(f)` stays `1-9(f)`, `1-2(F)` stays `1-2(F)`

### 3. Merged Cell Expansion
- `+`: Replicated to both `permeability_air_md` and `permeability_klink_md`
- `<0.0001`: Replicated to both permeability columns
- `**`: Replicated to all three saturation columns

### 4. CSV Injection Prevention
- Applied `sanitize_csv_value()` to header values
- Standalone indicators (`+`, `**`, `<0.0001`) are NOT escaped (they're not valid formulas)
- Only formula-like patterns (e.g., `+1234`, `=SUM(A1)`) are escaped with leading `'`

### 5. Notes Column Removed
- Original LLD specified a notes column, but it was not part of the assignment requirements
- Removed to keep output focused on extracting table data as specified
- Output now has 12 columns matching the PDF table structure

## Known Limitations

1. **Column group detection is heuristic-based** - Uses indicator values, not PDF bounding box analysis
2. **Only exact matches trigger expansion** - Substring matches (e.g., `<0.001`) won't trigger

## Verification

- Row count: 138 data rows (unchanged from baseline)
- Headers: Original PDF headers preserved (12 columns)
- Diff check: All changes are expected per Issue #4 requirements

## Commits

Single commit: `feat(core-analysis): handle merged cell indicators for permeability and saturation`
