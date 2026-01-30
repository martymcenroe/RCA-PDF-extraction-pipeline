# Spec vs Extended Output Comparison Quality Gate

## User Story
As a developer maintaining dual extraction pipelines,
I want automated comparison between Spec and Extended outputs,
So that I can catch regressions and ensure the Extended pipeline is a valid replacement for the Spec pipeline.

## Objective
Create a CI quality gate that compares CSV outputs from both extraction pipelines and fails the build if the Extended pipeline output does not contain all data present in the Spec pipeline (subset verification).

## UX Flow

### Scenario 1: Outputs Match (Happy Path)
1. Developer runs `python scripts/compare_outputs.py`
2. Script loads both CSV files using streaming comparison
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
2. Script uses true streaming approach (no `list()` conversion) to avoid OOM
3. Comparison completes successfully within memory constraints
4. Result: Comparison works on standard GitHub Actions runners (~7GB RAM)

### Scenario 6: Extra Columns in Extended
1. Developer runs comparison script
2. Extended output contains additional columns not in Spec
3. Script ignores extra columns and only verifies Spec columns exist
4. Result: Exit code 0 (subset check passes)

## Assumptions

**CRITICAL: Row Ordering Requirement**
- Both Spec and Extended pipelines MUST produce output files with **deterministic, identical row ordering**
- Rows are assumed to be sorted by the same primary key in both outputs
- If row ordering cannot be guaranteed, this approach will fail and a different architecture (hash-based comparison with higher memory usage, or pre-sort step) will be required
- The CI workflow should ensure both pipelines process input in the same order

## Requirements

### Comparison Logic
1. Verify all columns in Spec exist in Extended
2. Verify all rows in Spec have matching rows in Extended (row-by-row streaming)
3. Verify all values match for corresponding cells
4. Treat empty string, 'NA', and 'NaN' as equivalent values for null comparison
5. Support subset verification (Extended may have additional columns/rows)

### Output Format
1. Display clear pass/fail status with emoji indicators
2. Show row and column counts on success
3. Limit diff output to 20 items to avoid log flooding
4. Indicate total difference count when truncated
5. Display exit codes in help text (0 for success, 1 for failure)

### CLI Interface
1. Use `argparse` for argument parsing with help messages
2. Accept optional positional arguments for file paths
3. Default to standard output locations if no args provided
4. Provide `--help` flag with usage examples
5. Document exit codes in help output
6. Support `--verbose` flag to show all differences (disable 20-item limit)

### Memory Efficiency
1. Use Python standard `csv` library (no pandas dependency)
2. Stream files using iterator-based comparison with `zip()` on iterators
3. **No `list()` conversion** on readers - true streaming only
4. Work within GitHub Actions runner memory limits (~7GB)
5. Handle files >500MB without OOM

### Path Security
1. Validate file paths to prevent directory traversal attacks
2. Use `os.path.realpath()` and verify paths are within allowed directories
3. Reject paths containing `..` or absolute paths outside repo root

## Technical Approach
- **Comparison Script:** `scripts/compare_outputs.py` using standard library `csv` module with true streaming (using `zip()` on iterators, absolutely no `list()` conversion)
- **CLI:** `argparse` for argument handling with proper help text, error messages, and exit code documentation
- **Diff Algorithm:** Row-by-row, column-by-column streaming comparison assuming deterministic row order
- **Path Validation:** `os.path.realpath()` with repo root boundary check
- **CI Integration:** GitHub Actions step that runs comparison and fails on mismatch

## Security Considerations
- Script only reads local files within the repository
- **File paths validated to prevent directory traversal** using `os.path.realpath()` and repo root boundary checks
- No network access required
- No sensitive data handling beyond what's already in output files

## Files to Create/Modify
- `scripts/compare_outputs.py` — New comparison script with CSV support and path validation
- `.github/workflows/ci.yml` — Add comparison step after both pipelines run
- `tests/fixtures/` — Test CSV files for unit testing
- `docs/reports/0XXX/implementation-report.md` — Implementation documentation

## Dependencies
- None (uses Python standard library only: `csv`, `argparse`, `sys`, `os`, `pathlib`)

## Out of Scope (Future)
- **JSON comparison** — Removed from MVP scope; standard library `json` cannot stream large files and would violate memory efficiency requirements. Defer to future issue with streaming JSON parser (e.g., `ijson`) if needed.
- HTML diff report generation — deferred to future enhancement
- Tolerance-based numeric comparison — exact match only for MVP
- Performance benchmarking between pipelines — separate concern
- Automatic fix suggestions — manual investigation required
- Hash-based comparison for unordered rows — requires different architecture

## Acceptance Criteria
- [ ] `scripts/compare_outputs.py` exists and is executable
- [ ] Script uses `argparse` with `--help` support including exit code documentation
- [ ] Script uses standard library `csv` (not pandas)
- [ ] Script streams files without loading entirely into memory (no `list()` on readers)
- [ ] Script uses `zip()` directly on csv reader iterators for true streaming
- [ ] Script handles files >500MB without OOM on standard runners
- [ ] Script verifies all Spec columns exist in Extended
- [ ] Script verifies all Spec rows have matching Extended rows
- [ ] Script treats empty string, 'NA', and 'NaN' as equivalent null values
- [ ] Script outputs clear pass/fail with specific differences
- [ ] Script exits 0 on match, 1 on mismatch or error
- [ ] Script validates file paths to prevent directory traversal
- [ ] Script supports `--verbose` flag to show all differences
- [ ] CI workflow includes comparison step
- [ ] Test case for extra columns in Extended (subset verification passes)

## Definition of Done

### Implementation
- [ ] Core comparison script implemented with true streaming
- [ ] Path validation implemented with repo root boundary check
- [ ] Unit tests written and passing
- [ ] Integration test with sample CSV files

### Tools
- [ ] CLI tool created in `scripts/compare_outputs.py`
- [ ] Tool includes `--help` documentation with exit codes
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

# Test with extra columns in Extended (should pass)
python scripts/compare_outputs.py tests/fixtures/spec.csv tests/fixtures/extended_extra_cols.csv
# Expected: Exit 0, subset verification passes

# Test directory traversal prevention
python scripts/compare_outputs.py ../../../etc/passwd tests/fixtures/extended.csv
# Expected: Exit 1, "Invalid path" error

# Test verbose mode
python scripts/compare_outputs.py --verbose tests/fixtures/spec.csv tests/fixtures/extended_mismatch.csv
# Expected: Exit 1, ALL differences shown (no 20-item limit)
```

### Force Error States
- Delete one output file before running
- Manually edit a value in Extended output
- Remove a column from Extended output
- Attempt directory traversal with `../` in path

---

## Implementation Reference

### CSV Comparison (Standard Library - True Streaming)
```python
#!/usr/bin/env python3
"""Compare spec and extended outputs for subset match."""

import csv
import argparse
import sys
import os
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Compare Spec and Extended pipeline outputs.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Exit codes:
  0 - Comparison passed (all Spec data found in Extended)
  1 - Comparison failed or error occurred

Examples:
  %(prog)s
  %(prog)s data/output/spec/core.csv data/output/extended/core.csv
  %(prog)s --verbose spec.csv extended.csv'''
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
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show all differences (disable 20-item limit)'
    )
    return parser.parse_args()


def validate_path(file_path: str, repo_root: Path) -> bool:
    """Validate file path is within repo root to prevent directory traversal.
    
    Args:
        file_path: Path to validate
        repo_root: Repository root directory
        
    Returns:
        True if path is safe, False otherwise
    """
    try:
        real_path = Path(os.path.realpath(file_path))
        real_root = Path(os.path.realpath(repo_root))
        # Check if resolved path is within repo root
        real_path.relative_to(real_root)
        return True
    except ValueError:
        return False


def is_null_equivalent(value: str) -> bool:
    """Check if value represents a null/empty value.
    
    Treats empty string, 'NA', and 'NaN' as equivalent.
    """
    return value in ('', 'NA', 'NaN')


def compare_outputs(spec_path: str, extended_path: str, verbose: bool = False) -> bool:
    """Compare two CSV files - verify Spec is subset of Extended.
    
    Uses true streaming to handle large files without OOM.
    Returns True if all Spec data exists in Extended, False otherwise.
    """
    issues = []
    repo_root = Path(__file__).parent.parent
    
    # Validate paths for directory traversal
    if not validate_path(spec_path, repo_root):
        print(f"❌ Invalid path (outside repo): {spec_path}")
        return False
    if not validate_path(extended_path, repo_root):
        print(f"❌ Invalid path (outside repo): {extended_path}")
        return False
    
    # Validate files exist
    if not Path(spec_path).exists():
        print(f"❌ File not found: {spec_path}")
        return False
    if not Path(extended_path).exists():
        print(f"❌ File not found: {extended_path}")
        return False
    
    # Open both files for streaming comparison
    with open(spec_path, newline='') as spec_file, \
         open(extended_path, newline='') as ext_file:
        
        spec_reader = csv.DictReader(spec_file)
        ext_reader = csv.DictReader(ext_file)
        
        spec_columns = spec_reader.fieldnames or []
        ext_columns = ext_reader.fieldnames or []
        
        # Check that all Spec columns exist in Extended
        spec_cols_set = set(spec_columns)
        ext_cols_set = set(ext_columns)
        missing_cols = spec_cols_set - ext_cols_set
        if missing_cols:
            issues.append(f"Columns missing from Extended: {missing_cols}")
        
        # Stream and compare row by row using zip on iterators (TRUE STREAMING)
        # NOTE: This assumes both files have identical row ordering
        row_count = 0
        for idx, (spec_row, ext_row) in enumerate(zip(spec_reader, ext_reader)):
            row_count = idx + 1
            for col in spec_columns:
                if col in missing_cols:
                    continue
                spec_val = spec_row.get(col, '')
                ext_val = ext_row.get(col, '')
                
                # Handle empty/NaN comparison
                if spec_val == ext_val:
                    continue
                if is_null_equivalent(spec_val) and is_null_equivalent(ext_val):
                    continue
                    
                issues.append(f"Row {idx}, column '{col}': spec='{spec_val}' vs extended='{ext_val}'")
        
        # Check if spec has more rows than extended
        remaining_spec_rows = sum(1 for _ in spec_reader)
        if remaining_spec_rows > 0:
            issues.append(f"Extended has fewer rows: missing {remaining_spec_rows} rows from Spec")
    
    # Report results
    if issues:
        print("❌ COMPARISON FAILED")
        print("=" * 50)
        max_display = len(issues) if verbose else 20
        for issue in issues[:max_display]:
            print(issue)
        if not verbose and len(issues) > 20:
            print(f"... and {len(issues) - 20} more differences (use --verbose to see all)")
        return False
    else:
        print("✓ COMPARISON PASSED")
        print(f"  Spec rows compared: {row_count}")
        print(f"  Spec columns: {len(spec_columns)}")
        print("  All Spec data verified in Extended output")
        return True


if __name__ == '__main__':
    args = parse_args()
    success = compare_outputs(args.spec_path, args.extended_path, args.verbose)
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

## Labels
`ci`, `quality`, `python`