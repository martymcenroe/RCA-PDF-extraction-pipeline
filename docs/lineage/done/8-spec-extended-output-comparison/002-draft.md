# Spec vs Extended Output Comparison Quality Gate

## User Story
As a **developer maintaining the extraction pipelines**,
I want **automated comparison between spec and extended pipeline outputs**,
So that **I can detect regressions and ensure both pipelines produce identical results**.

## Objective
Create a comparison script that validates spec (minimal) and extended (database) pipeline outputs are identical, failing CI if any differences are detected.

## UX Flow

### Scenario 1: Outputs Match (Happy Path)
1. Developer runs `python scripts/compare_outputs.py`
2. Script loads both CSV files and compares row-by-row
3. Result: `✓ COMPARISON PASSED` with row/column counts
4. Exit code 0 (success)

### Scenario 2: Outputs Differ
1. Developer runs comparison after pipeline change
2. Script detects value differences in row 45
3. Result: `❌ COMPARISON FAILED` with detailed diff (limited to first 20 differences)
4. Exit code 1 (failure)

### Scenario 3: Structural Mismatch
1. One pipeline outputs different columns or row counts
2. Script detects shape/column mismatch before value comparison
3. Result: Clear error message identifying structural differences
4. Exit code 1 (failure)

### Scenario 4: CI Integration
1. PR triggers GitHub Actions workflow
2. Both pipelines run, producing outputs
3. Comparison script runs as quality gate
4. PR blocked if comparison fails

## Requirements

### Comparison Logic
1. Compare CSV row counts (shape check)
2. Compare column names and order
3. Compare values row-by-row, column-by-column
4. Handle NaN/null values correctly (NaN == NaN should pass)
5. Support configurable ignore list for intentional differences (e.g., timestamps)

### JSON Comparison
1. Compare page classifications
2. Compare sample data arrays
3. Report first mismatch with context

### Output Formatting
1. Clear pass/fail indicator (✓/❌)
2. Summary statistics on pass
3. Detailed diff on fail (capped at 20 differences)
4. Machine-readable exit codes

## Technical Approach
- **Pandas:** Load and compare CSV files efficiently
- **JSON module:** Parse and compare structured outputs
- **CLI arguments:** Support custom file paths via `sys.argv`
- **Exit codes:** 0 for pass, 1 for fail (CI-compatible)

## Security Considerations
- Script only reads files, no write operations
- No external network calls
- Safe for CI environments

## Files to Create/Modify
- `scripts/compare_outputs.py` — Main comparison script (new)
- `.github/workflows/ci.yml` — Add comparison step (modify)
- `tests/test_compare_outputs.py` — Unit tests for comparison logic (new)

## Dependencies
- None — this is a standalone quality gate

## Out of Scope (Future)
- **Fuzzy matching** — exact match only for MVP
- **HTML diff report** — text output sufficient initially
- **Historical comparison** — only compares current outputs
- **Performance benchmarking** — separate concern from correctness

## Acceptance Criteria
- [ ] `scripts/compare_outputs.py` exists and is executable
- [ ] Script correctly identifies identical outputs (exit 0)
- [ ] Script correctly identifies differing outputs (exit 1)
- [ ] Script handles NaN values without false positives
- [ ] Script compares JSON outputs (classifications, samples)
- [ ] Output limited to 20 differences to avoid log spam
- [ ] CI workflow includes comparison as quality gate
- [ ] `IGNORE_COLUMNS` configuration documented and working

## Definition of Done

### Implementation
- [ ] Core comparison script implemented
- [ ] JSON comparison function implemented
- [ ] CLI argument parsing for custom paths
- [ ] Unit tests written and passing

### Tools
- [ ] `scripts/compare_outputs.py` created
- [ ] Script documented with `--help` output

### Documentation
- [ ] Usage examples in script docstring
- [ ] CI integration documented in workflow file
- [ ] Known intentional differences documented (if any)

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/compare-outputs/implementation-report.md` created
- [ ] `docs/reports/compare-outputs/test-report.md` created

### Verification
- [ ] Run initial comparison on current outputs
- [ ] Fix any discrepancies found (or document as intentional)
- [ ] CI pipeline passes with comparison step

## Testing Notes

### Manual Testing
```bash
# Run comparison with defaults
python scripts/compare_outputs.py

# Run with custom paths
python scripts/compare_outputs.py data/output/spec/core_analysis.csv data/output/extended/core_analysis.csv

# Verify failure detection (modify one file temporarily)
sed -i 's/+/MODIFIED/' data/output/spec/core_analysis.csv
python scripts/compare_outputs.py  # Should fail
git checkout data/output/spec/core_analysis.csv  # Restore
```

### Unit Test Cases
1. Identical files → pass
2. Different row count → fail with shape message
3. Different columns → fail with column diff
4. Single value difference → fail with location
5. NaN in both → pass (not a difference)
6. NaN vs value → fail
7. Ignored columns differ → pass