---
repo: martymcenroe/RCA-PDF-extraction-pipeline
issue: 9
url: https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/issues/9
fetched: 2026-02-05T03:13:18.466919Z
---

# Issue #9: Data Analysis & Validation for Extracted Core Samples

# Data Analysis & Validation for Extracted Core Samples

## User Story
As a **data engineer/geologist**,
I want **automated validation and analysis of extracted RCA data**,
So that **I can verify extraction accuracy, catch errors early, and gain insights into data quality**.

## Objective
Create a comprehensive data analysis script that validates the 138 extracted core samples, generates summary statistics, identifies anomalies, and produces visualizations for manual review.

## UX Flow

### Scenario 1: Successful Validation
1. User runs `python scripts/analyze_output.py data/output/spec/core_analysis.csv`
2. System performs structural, range, and consistency validation
3. System generates summary statistics and visualizations
4. Result: Console report shows all checks passed, plots saved to `data/output/analysis/`

### Scenario 2: Validation Warnings
1. User runs analysis script on extracted data
2. System detects values outside expected ranges (e.g., permeability > 100 md)
3. System flags warnings but continues analysis
4. Result: Report shows "PASSED (N warnings)" with specific issues listed

### Scenario 3: Validation Failures
1. User runs analysis script on corrupted/incomplete data
2. System detects structural issues (wrong row count, duplicate samples)
3. System halts with clear error message
4. Result: Report shows "FAILED" with actionable diagnostics

### Scenario 4: Missing Input File
1. User runs script with incorrect file path
2. System cannot locate CSV file
3. Result: Clear error message with usage instructions

## Requirements

### Structural Validation
1. Verify row count matches expected 138 samples
2. Verify all required columns present (≥11 columns)
3. Check for duplicate sample numbers
4. Confirm both cores (4 and 5) are represented

### Range Validation
1. Depth values within 9,500 - 10,000 ft range
2. Permeability values 0 - 1,000 md (flag > 100 as warning)
3. Porosity values 0 - 30% (ambient and NCS)
4. Grain density values 2.0 - 3.0 g/cc
5. Saturation percentages 0 - 100%

### Consistency Validation
1. Depth monotonically increasing within each core
2. NCS porosity ≤ ambient porosity for all samples
3. Saturation total ≈ water + oil (within 1% tolerance)
4. Core number matches expected sample ranges

### Summary Statistics
1. Total sample count and per-core breakdown
2. Depth range (min, max) overall and per core
3. Fracture sample count and percentage
4. Below-detection and missing-data counts
5. Mean, std, min, max for key numeric properties

### Visualizations
1. Depth vs property profiles (porosity, permeability, density, saturation)
2. Correlation matrix heatmap for numeric properties
3. Distribution histograms for key properties
4. Per-core comparison plots

## Technical Approach
- **Validation Engine:** Pandas-based checks with categorized pass/warn/fail results
- **Statistics:** NumPy/Pandas for descriptive statistics with handling for special values (+, **, etc.)
- **Visualization:** Matplotlib for publication-quality plots with consistent styling
- **Reporting:** Structured text output with emoji indicators (✓, ⚠, ✗) and optional JSON export

## Security Considerations
- Script operates on local files only, no network access
- Read-only access to input CSV, write access only to designated output directory
- No execution of external commands or user-provided code

## Files to Create/Modify
- `scripts/analyze_output.py` — Main analysis script with CLI interface
- `scripts/validators/structural.py` — Structural validation functions
- `scripts/validators/range.py` — Range validation functions
- `scripts/validators/consistency.py` — Consistency validation functions
- `scripts/analysis/statistics.py` — Summary statistics generation
- `scripts/analysis/visualizations.py` — Matplotlib plotting functions
- `data/output/analysis/.gitkeep` — Ensure output directory exists
- `tests/test_analyze_output.py` — Unit tests for validation logic
- `README.md` — Update with analysis script usage

## Dependencies
- None (can be implemented independently)

## Out of Scope (Future)
- **Interactive dashboards** — Jupyter notebooks or web UI deferred
- **Machine learning anomaly detection** — Simple statistical checks only for MVP
- **Comparison with original PDF** — Visual diff against source document
- **Export to domain-specific formats** — LAS, WITSML, etc.

## Acceptance Criteria
- [ ] Script runs successfully on extracted CSV: `python scripts/analyze_output.py data/output/spec/core_analysis.csv`
- [ ] Structural validation correctly identifies row count, column count, duplicates, and cores present
- [ ] Range validation flags values outside expected bounds with appropriate severity
- [ ] Consistency validation catches depth ordering issues and porosity/saturation mismatches
- [ ] Summary statistics generated with handling for special values (+, **, NaN)
- [ ] Four visualization plots generated and saved to `data/output/analysis/`
- [ ] Console report clearly shows pass/warn/fail status with actionable details
- [ ] Text report saved to `data/output/analysis/validation_report.txt`
- [ ] Script exits with code 0 for pass, 1 for warnings, 2 for failures
- [ ] Handles missing file gracefully with clear error message

## Definition of Done

### Implementation
- [ ] Core validation logic implemented in modular structure
- [ ] Visualization functions create readable, well-labeled plots
- [ ] CLI accepts file path argument with sensible defaults
- [ ] Unit tests written and passing for all validation functions

### Tools
- [ ] `scripts/analyze_output.py` is executable and documented
- [ ] Add to Makefile: `make analyze` target

### Documentation
- [ ] Update README.md with analysis script usage
- [ ] Docstrings for all public functions
- [ ] Example output included in documentation
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)
- [ ] Manual review of generated plots confirms extraction accuracy

## Testing Notes

### Validation Testing
```bash
# Run on valid extracted data
python scripts/analyze_output.py data/output/spec/core_analysis.csv

# Test with intentionally corrupted data
python scripts/analyze_output.py tests/fixtures/corrupted_core_data.csv

# Test missing file handling
python scripts/analyze_output.py nonexistent.csv
```

### Creating Test Fixtures
1. Copy valid CSV and introduce known errors (duplicate rows, out-of-range values)
2. Verify script correctly identifies each error type
3. Test edge cases: empty file, single row, all warnings

### Visual Verification
1. Compare depth profile plots against original PDF figures
2. Verify porosity values cluster in expected 0-10% range
3. Check that fracture samples are visually distinguishable if marked