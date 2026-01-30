# Idea: Fix Pylint Audit Integration

**Status:** Bug Fix
**Effort:** Low (1 hour)
**Value:** Medium - enables automated code quality scoring

---

## Problem

The audit script (Q2 check) skips pylint verification:

```
| Q2 | Code is clean | SKIP | Could not parse pylint output |
```

This means we have no automated code quality score, which is a grading criterion:
> "Engineering Quality: Is the code modular and clean?"

---

## Root Cause

The `check_q2_code_clean()` function in `scripts/audit.py` fails to parse pylint output. Likely causes:

1. **Pylint not installed** - Missing from dev dependencies
2. **Output format changed** - Regex doesn't match current pylint version
3. **Windows encoding issues** - Subprocess output encoding mismatch
4. **Non-zero exit code** - Pylint returns non-zero for any warnings

---

## Current Implementation

```python
def check_q2_code_clean() -> CheckResult:
    """Q2: Code is clean (pylint score)."""
    src_path = PROJECT_ROOT / "src/core_analysis_minimal.py"

    try:
        result = subprocess.run(
            ["python", "-m", "pylint", str(src_path), "--score=y", "--output-format=text"],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Extract score from output
        score_match = re.search(r'Your code has been rated at ([\d.]+)/10', result.stdout)
        # ...
```

---

## Diagnosis Steps

1. **Check if pylint is installed:**
   ```bash
   python -m pylint --version
   ```

2. **Run pylint manually:**
   ```bash
   python -m pylint src/core_analysis_minimal.py --score=y
   ```

3. **Check output format:**
   - Verify the score line format
   - Check if output goes to stdout or stderr

4. **Check exit code handling:**
   - Pylint returns non-zero for warnings/errors
   - Need to check output regardless of exit code

---

## Proposed Fix

```python
def check_q2_code_clean() -> CheckResult:
    """Q2: Code is clean (pylint score)."""
    src_path = PROJECT_ROOT / "src/core_analysis_minimal.py"

    # Check if pylint is available
    try:
        subprocess.run(
            ["python", "-m", "pylint", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return CheckResult("Q2", "Code is clean", "SKIP",
                           "pylint not installed - run: pip install pylint")

    try:
        result = subprocess.run(
            ["python", "-m", "pylint", str(src_path), "--score=y", "--output-format=text"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace"  # Handle encoding issues
        )

        # Pylint outputs to stdout, score is at the end
        # Check both stdout and stderr
        output = result.stdout + result.stderr

        # Score line format: "Your code has been rated at X.XX/10"
        score_match = re.search(r'Your code has been rated at (-?[\d.]+)/10', output)

        if score_match:
            score = float(score_match.group(1))
            if score >= 8.0:
                return CheckResult("Q2", "Code is clean", "PASS",
                                   f"Pylint score: {score}/10")
            elif score >= 6.0:
                return CheckResult("Q2", "Code is clean", "WARN",
                                   f"Pylint score: {score}/10 (target: 8.0)")
            else:
                return CheckResult("Q2", "Code is clean", "FAIL",
                                   f"Pylint score: {score}/10 (target: 8.0)")
        else:
            # Debug: show what we got
            return CheckResult("Q2", "Code is clean", "SKIP",
                               f"Could not parse pylint output",
                               evidence=f"stdout: {result.stdout[:200]}...")
    except subprocess.TimeoutExpired:
        return CheckResult("Q2", "Code is clean", "SKIP",
                           "pylint timed out after 120 seconds")
    except Exception as e:
        return CheckResult("Q2", "Code is clean", "SKIP",
                           f"pylint error: {type(e).__name__}: {e}")
```

---

## Dependencies

Add pylint to dev dependencies in `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pylint>=3.0.0",  # Add this
]
```

---

## Testing

After fix:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run audit
python scripts/audit.py --verbose

# Expected output:
# [OK] Q2: Code is clean - PASS
#     Pylint score: 7.5/10
```

---

## Alternative: Use Ruff

If pylint continues to be problematic, consider switching to `ruff`:

- Much faster (10-100x)
- Single binary, fewer dependencies
- Compatible scoring

```python
result = subprocess.run(
    ["ruff", "check", str(src_path), "--statistics"],
    capture_output=True,
    text=True
)
# Parse ruff output instead
```

---

## Next Steps

1. [ ] Install pylint: `pip install pylint`
2. [ ] Run pylint manually to verify output format
3. [ ] Update `check_q2_code_clean()` with improved parsing
4. [ ] Add pylint to dev dependencies
5. [ ] Re-run audit to verify Q2 passes
