# Spec vs Extended Output Comparison Quality Gate

## User Story
As a developer maintaining dual extraction pipelines,
I want automated comparison between Spec and Extended outputs,
So that I can catch regressions and ensure the Extended pipeline is a valid replacement for the Spec pipeline.

## Objective
Create a CI quality gate that compares CSV/JSON outputs from both extraction pipelines and fails the build if the Extended pipeline output does not contain all data present in the Spec pipeline.

## UX Flow

### Scenario 1: Outputs Match (Happy Path)
1. Developer runs `python scripts/compare_outputs.py`
2. Script loads both CSV files and compares them
3. All Spec data exists in Extended with matching values
4. Result: Exit code 0, success message displayed

### Scenario 2: Data Mismatch Found
1. Developer runs comparison script
2. Script detects value differences between files
3. Script outputs detailed diff report (limited to 20 items)
4. Result: Exit code 1, CI fails with actionable error messages

### Scenario 3: Schema Mismatch
1. Developer runs comparison script
2. Extended output is missing columns present in Spec
3. Script reports missing columns clearly
4. Result: Exit code 1, developer knows exactly which columns are missing

### Scenario 4: File Not Found
1. Developer runs comparison script
2. One or both output files don't exist
3. Script outputs clear error message indicating which file is missing
4. Result: Exit code 1 with helpful error message

### Scenario 5: Large File Handling
1. Developer runs comparison on files >500MB
2. Script uses streaming/chunked approach to avoid OOM
3. Comparison completes successfully within memory constraints
4. Result: Comparison works on standard GitHub Actions runners

## Requirements

### Comparison Logic
1. Verify all columns in Spec exist in Extended
2. Verify all rows in Spec have matching rows in Extended
3. Verify all values match for corresponding cells
4. Handle NaN/null values correctly in comparisons
5. Support subset verification (Extended may have additional columns/rows)

### Output Format
1. Display clear pass/fail status with emoji indicators
2. Show row and column counts on success
3. Limit diff output to 20 items to avoid log flooding
4. Indicate total difference count when truncated

### CLI Interface
1. Use `argparse` for argument parsing with help messages
2. Accept optional positional arguments for file paths
3. Default to standard output locations if no args provided
4. Provide `--help` flag with usage examples

### Memory Efficiency
1. Use Python standard `csv` library (no pandas dependency)
2. Stream large files in chunks if needed
3. Work within GitHub Actions runner memory limits (~7GB)

## Technical Approach
- **Comparison Script:** `scripts/compare_outputs.py` using standard library `csv` module for memory-efficient parsing
- **CLI:** `argparse` for argument handling with proper help text and error messages
- **Diff Algorithm:** Row-by-row, column-by-column comparison with early termination option
- **JSON Comparison:** Structural equality check for classification and sample data
- **CI Integration:** GitHub Actions step that runs comparison and fails on mismatch

## Security Considerations
- Script only reads local files within the repository
- No network access required
- No sensitive data handling beyond what's already in output files
- File paths validated to prevent directory traversal

## Files to Create/Modify
- `scripts/compare_outputs.py` — New comparison script with CSV and JSON support
- `.github/workflows/ci.yml` — Add comparison step after both pipelines run
- `docs/reports/0XXX/implementation-report.md` — Implementation documentation

## Dependencies
- None (uses Python standard library only: `csv`, `json`, `argparse`, `sys`)

## Out of Scope (Future)
- HTML diff report generation — deferred to future enhancement
- Tolerance-based numeric comparison — exact match only for MVP
- Performance benchmarking between pipelines — separate concern
- Automatic fix suggestions — manual investigation required

## Acceptance Criteria
- [ ] `scripts/compare_outputs.py` exists and is executable
- [ ] Script uses `argparse` with `--help` support
- [ ] Script uses standard library `csv` (not pandas)
- [ ] Script handles files >500MB without OOM on standard runners
- [ ] Script verifies all Spec columns exist in Extended
- [ ] Script verifies all Spec rows have matching Extended rows
- [ ] Script correctly compares NaN/null values
- [ ] Script outputs clear pass/fail with specific differences
- [ ] Script exits 0 on match, 1 on mismatch or error
- [ ] CI workflow includes comparison step
- [ ] JSON comparison covers classifications and samples

## Definition of Done

### Implementation
- [ ] Core comparison script implemented
- [ ] Unit tests written and passing
- [ ] Integration test with sample CSV/JSON files

### Tools
- [ ] CLI tool created in `scripts/compare_outputs.py`
- [ ] Tool includes `--help` documentation
- [ ] Tool follows project CLI conventions

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (if security-relevant)
- [ ] Run 0810 Privacy Audit - PASS (if privacy-relevant)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes

### Unit Tests
```bash
# Test with matching files
python scripts/compare_outputs.py tests/fixtures/spec.csv tests/fixtures/extended_match.csv
# Expected: Exit 0, "COMPARISON PASSED"

# Test with mismatched files
python scripts/compare_outputs.py tests/fixtures/spec.csv tests/fixtures/extended_mismatch.csv
# Expected: Exit 1, diff report shown

# Test with missing file
python scripts/compare_outputs.py tests/fixtures/nonexistent.csv tests/fixtures/extended.csv
# Expected: Exit 1, "File not found" error
```

### Force Error States
- Delete one output file before running
- Manually edit a value in Extended output
- Remove a column from Extended output

---

## Implementation Reference

### CSV Comparison (Standard Library)
```python
#!/usr/bin/env python3
"""Compare spec and extended outputs for subset match."""

import csv
import json
import argparse
import sys
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Compare Spec and Extended pipeline outputs.',
        epilog='Example: %(prog)s data/output/spec/core.csv data/output/extended/core.csv'
    )
    parser.add_argument(
        'spec_path',
        nargs='?',
        default='data/output/spec/core_analysis.csv',
        help='Path to Spec output CSV (default: data/output/spec/core_analysis.csv)'
    )
    parser.add_argument(
        'extended_path',
        nargs='?',
        default='data/output/extended/core_analysis.csv',
        help='Path to Extended output CSV (default: data/output/extended/core_analysis.csv)'
    )
    return parser.parse_args()


def compare_outputs(spec_path: str, extended_path: str) -> bool:
    """Compare two CSV files - verify Spec is subset of Extended.
    
    Returns True if all Spec data exists in Extended, False otherwise.
    """
    issues = []
    
    # Validate files exist
    if not Path(spec_path).exists():
        print(f"❌ File not found: {spec_path}")
        return False
    if not Path(extended_path).exists():
        print(f"❌ File not found: {extended_path}")
        return False
    
    # Read files using standard csv library (memory efficient)
    with open(spec_path, newline='') as f:
        spec_reader = csv.DictReader(f)
        spec_rows = list(spec_reader)
        spec_columns = spec_reader.fieldnames or []
    
    with open(extended_path, newline='') as f:
        ext_reader = csv.DictReader(f)
        ext_rows = list(ext_reader)
        ext_columns = ext_reader.fieldnames or []
    
    # Check that all Spec columns exist in Extended
    spec_cols_set = set(spec_columns)
    ext_cols_set = set(ext_columns)
    missing_cols = spec_cols_set - ext_cols_set
    if missing_cols:
        issues.append(f"Columns missing from Extended: {missing_cols}")
    
    # Check row count
    if len(spec_rows) > len(ext_rows):
        issues.append(f"Extended has fewer rows: spec={len(spec_rows)}, extended={len(ext_rows)}")
    
    # Compare values for Spec columns only
    for idx, spec_row in enumerate(spec_rows):
        if idx >= len(ext_rows):
            issues.append(f"Row {idx}: missing from Extended")
            continue
            
        ext_row = ext_rows[idx]
        for col in spec_columns:
            if col in missing_cols:
                continue
            spec_val = spec_row.get(col, '')
            ext_val = ext_row.get(col, '')
            
            # Handle empty/NaN comparison
            if spec_val == ext_val:
                continue
            if spec_val in ('', 'NA', 'NaN') and ext_val in ('', 'NA', 'NaN'):
                continue
                
            issues.append(f"Row {idx}, column '{col}': spec='{spec_val}' vs extended='{ext_val}'")
    
    # Report results
    if issues:
        print("❌ COMPARISON FAILED")
        print("=" * 50)
        for issue in issues[:20]:
            print(issue)
        if len(issues) > 20:
            print(f"... and {len(issues) - 20} more differences")
        return False
    else:
        print("✓ COMPARISON PASSED")
        print(f"  Spec rows: {len(spec_rows)}")
        print(f"  Spec columns: {len(spec_columns)}")
        print("  All Spec data verified in Extended output")
        return True


if __name__ == '__main__':
    args = parse_args()
    success = compare_outputs(args.spec_path, args.extended_path)
    sys.exit(0 if success else 1)
```

### CI Integration
```yaml
- name: Compare pipeline outputs
  run: |
    python scripts/compare_outputs.py \
      data/output/spec/core_analysis.csv \
      data/output/extended/core_analysis.csv
```