# Test Report: Issue #4 - Improved Footnote Symbol Handling

## Test Command Executed

```bash
poetry run --directory /c/Users/mcwiz/Projects/RCA-PDF-extraction-pipeline-4 pytest tests/test_footnote_symbols.py -v
```

## Test Output

```
============================= test session starts =============================
platform win32 -- Python 3.14.0, pytest-9.0.2, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: C:\Users\mcwiz\Projects\RCA-PDF-extraction-pipeline-4
configfile: pyproject.toml
plugins: anyio-4.12.1, langsmith-0.6.4, cov-4.1.0
collecting ... collected 11 items

tests/test_footnote_symbols.py::TestFractureIndicatorExtraction::test_t01_fracture_f_lowercase_preserved PASSED [  9%]
tests/test_footnote_symbols.py::TestFractureIndicatorExtraction::test_t02_fracture_f_uppercase_preserved PASSED [ 18%]
tests/test_footnote_symbols.py::TestFractureIndicatorExtraction::test_fracture_indicator_regex PASSED [ 27%]
tests/test_footnote_symbols.py::TestMergedCellExpansion::test_t03_plus_replicated_to_both_perm PASSED [ 36%]
tests/test_footnote_symbols.py::TestMergedCellExpansion::test_t04_detection_limit_replicated PASSED [ 45%]
tests/test_footnote_symbols.py::TestMergedCellExpansion::test_t05_star_replicated_to_all_sat PASSED [ 54%]
tests/test_footnote_symbols.py::TestNormalRows::test_t06_normal_rows_unchanged PASSED [ 63%]
tests/test_footnote_symbols.py::TestSafetyChecks::test_t10_max_sample_lines_exceeded PASSED [ 72%]
tests/test_footnote_symbols.py::TestSafetyChecks::test_t11_output_path_validation_rejects_outside PASSED [ 81%]
tests/test_footnote_symbols.py::TestSafetyChecks::test_output_path_validation_accepts_tmp PASSED [ 90%]
tests/test_footnote_symbols.py::TestSafetyChecks::test_output_path_validation_accepts_project PASSED [100%]

============================= 11 passed in 0.05s ==============================
```

## Test Summary

| Category | Tests | Passed | Failed | Skipped |
|----------|-------|--------|--------|---------|
| Fracture Indicator | 3 | 3 | 0 | 0 |
| Merged Cell Expansion | 3 | 3 | 0 | 0 |
| Normal Rows | 1 | 1 | 0 | 0 |
| Safety Checks | 4 | 4 | 0 | 0 |
| **Total** | **11** | **11** | **0** | **0** |

## Skipped Tests

None.

## Integration Test Results

### Row Count Verification
```bash
wc -l /tmp/issue4/core_analysis.csv
# Output: 139 /tmp/issue4/core_analysis.csv
# Expected: 139 (138 data + 1 header) - PASS
```

### Baseline Diff Check
```bash
diff /c/Users/mcwiz/Projects/RCA-PDF-extraction-pipeline-4/data/output/spec/core_analysis.csv /tmp/issue4/core_analysis.csv
# Output: (no output - files identical)
# Exit code: 0 - PASS
```

### Header Verification
```bash
head -1 /tmp/issue4/core_analysis.csv
# Output: Core Number,Sample Number,Depth (ft),Permeability (md) | Air,Permeability (md) | Klink,Porosity (%) | Ambient,Porosity (%) | NCS,Grain Density (g/cc),Fluid Saturations (%) | Water,Fluid Saturations (%) | Oil,Fluid Saturations (%) | Total,Page Number
# Expected: Original PDF headers (12 columns, no Notes) - PASS
```

## Acceptance Criteria

- [x] `1-9(f)` sample_number preserves `(f)` suffix
- [x] `1-2(F)` sample_number preserves `(F)` suffix
- [x] Rows with `+` permeability have `+` in BOTH air AND klink columns
- [x] Rows with `<0.0001` have value in BOTH permeability columns
- [x] Rows with `**` saturation have `**` in ALL THREE saturation columns
- [x] Total row count: 138 data rows (unchanged)
- [x] Headers match original PDF (12 columns, no Notes column)
- [x] `diff` returns exit code 0 against updated baseline

## Coverage Metrics

Not measured for this issue (unit tests use stub fixtures).
