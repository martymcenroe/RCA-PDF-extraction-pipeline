# Fix Pylint Audit Integration for Code Quality Scoring

## User Story
As a **developer maintaining code quality**,
I want **the audit script's Q2 check to correctly parse pylint output**,
So that **I have automated code quality scoring for grading criteria**.

## Objective
Fix the `check_q2_code_clean()` function in `scripts/audit.py` to reliably parse pylint output and provide meaningful code quality scores.

## UX Flow

### Scenario 1: Happy Path - Pylint Installed and Working
1. User runs `python scripts/audit.py`
2. Q2 check invokes pylint on source files
3. Pylint score is extracted and displayed
4. Result: `| Q2 | Code is clean | PASS | Pylint score: 8.5/10 |`

### Scenario 2: Pylint Not Installed
1. User runs `python scripts/audit.py`
2. Q2 check detects pylint is not available
3. Result: `| Q2 | Code is clean | SKIP | pylint not installed - run: pip install pylint |`

### Scenario 3: Low Score Warning
1. User runs audit with code scoring 6.0-7.9
2. Q2 check extracts score successfully
3. Result: `| Q2 | Code is clean | WARN | Pylint score: 7.2/10 (target: 8.0) |`

### Scenario 4: Parse Failure with Debug Info
1. User runs audit with unexpected pylint output format
2. Q2 check cannot find score pattern
3. Result: `| Q2 | Code is clean | SKIP | Could not parse pylint output | evidence: stdout: ... |`

## Requirements

### Parsing Robustness
1. Handle pylint non-zero exit codes (returns non-zero for any warnings)
2. Check both stdout and stderr for score output
3. Handle negative scores (pylint can return negative values)
4. Support Windows encoding with `errors="replace"`

### Error Handling
1. Detect and report when pylint is not installed
2. Handle subprocess timeout gracefully (increase to 120s)
3. Provide debug evidence when parsing fails
4. Catch and report unexpected exceptions with type and message

### Dependency Management
1. Add pylint>=3.0.0 to dev dependencies in `pyproject.toml`
2. Document installation requirement in error messages

## Technical Approach
- **Pylint Detection:** Pre-check with `pylint --version` before main execution
- **Output Capture:** Concatenate stdout + stderr for comprehensive parsing
- **Regex Pattern:** Update to handle negative scores: `r'Your code has been rated at (-?[\d.]+)/10'`
- **Encoding:** Add `encoding="utf-8"` and `errors="replace"` for Windows compatibility
- **Timeout:** Increase from 60s to 120s for larger codebases

## Security Considerations
No security implications - this is a development-only tooling fix that runs locally.

## Files to Create/Modify
- `scripts/audit.py` — Update `check_q2_code_clean()` function with improved parsing logic
- `pyproject.toml` — Add `pylint>=3.0.0` to `[project.optional-dependencies.dev]`

## Dependencies
- None - this is a standalone bug fix

## Out of Scope (Future)
- **Switch to Ruff** — Consider as alternative if pylint continues to be problematic
- **Multi-file scanning** — Currently only checks `src/core_analysis_minimal.py`
- **Configurable score thresholds** — Hardcoded 8.0/6.0 thresholds are sufficient for now

## Acceptance Criteria
- [ ] Running `python -m pylint --version` succeeds after `pip install -e ".[dev]"`
- [ ] Q2 check returns PASS/WARN/FAIL with score when pylint works
- [ ] Q2 check returns SKIP with actionable message when pylint not installed
- [ ] Q2 check handles pylint non-zero exit codes without failing
- [ ] Parse failure includes evidence snippet for debugging
- [ ] Windows users can run audit without encoding errors

## Definition of Done

### Implementation
- [ ] `check_q2_code_clean()` rewritten with improved error handling
- [ ] Pylint version check added before main execution
- [ ] Both stdout and stderr checked for score output
- [ ] Encoding parameters added for Windows compatibility

### Tools
- [ ] N/A - modifying existing audit tool

### Documentation
- [ ] Update audit script docstrings if needed
- [ ] Add comment explaining pylint exit code behavior

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run full audit suite - Q2 no longer shows "Could not parse pylint output"
- [ ] Test on fresh environment without pylint installed - shows helpful skip message

## Testing Notes

**Manual verification steps:**

```bash
# 1. Verify current failure
python scripts/audit.py --verbose
# Should show: Q2 | Code is clean | SKIP | Could not parse pylint output

# 2. Check pylint installation
python -m pylint --version

# 3. If not installed, install dev dependencies
pip install -e ".[dev]"

# 4. Run pylint manually to see output format
python -m pylint src/core_analysis_minimal.py --score=y

# 5. After fix, re-run audit
python scripts/audit.py --verbose
# Should show: Q2 | Code is clean | PASS/WARN/FAIL | Pylint score: X.X/10
```

**To test error handling:**
```bash
# Uninstall pylint temporarily
pip uninstall pylint -y

# Run audit - should show helpful skip message
python scripts/audit.py --verbose
# Expected: Q2 | Code is clean | SKIP | pylint not installed - run: pip install pylint
```