# Security Analysis

This page documents security scanning results for the codebase.

## Summary

| Check | Result |
|-------|--------|
| **Dependency Vulnerabilities** | None found |
| **Static Analysis (Bandit)** | 4 medium, 15 low (all acceptable) |
| **Automated Monitoring** | GitHub Dependabot enabled |

## Dependency Scanning

**Tool:** [pip-audit](https://pypi.org/project/pip-audit/)

```
No known vulnerabilities found
```

Dependencies are minimal (PyMuPDF, Flask, Click) which reduces attack surface.

## Static Analysis

**Tool:** [Bandit](https://bandit.readthedocs.io/) - Python security linter

### Medium Severity (4 findings)

| Finding | Location | Verdict |
|---------|----------|---------|
| Hardcoded `/tmp/` directory | `core_analysis.py:47` | **Acceptable** - Part of output path allowlist, not a temp file vulnerability |
| SQL injection warning | `elementizer/database.py` | **False positive** - Table names are hardcoded constants, not user input |
| SQL injection warning | `elementizer/database.py` | **False positive** - Same as above |
| SQL injection warning | `elementizer/viewer.py` | **False positive** - Same as above |

### Low Severity (15 findings)

| Finding | Count | Verdict |
|---------|-------|---------|
| `try/except/pass` patterns | 11 | **Acceptable** - Defensive coding for PDF parsing; malformed PDFs shouldn't crash the pipeline |
| `try/except/continue` patterns | 2 | **Acceptable** - Same rationale |
| `assert` statements | 2 | **Acceptable** - Used for invariant checking; code isn't run with `-O` flag |

## Security Controls

### Input Validation

- **Output path validation:** `_validate_output_path()` restricts writes to allowed directories only
- **PDF parsing:** Malformed input handled gracefully, doesn't crash

### No Network Operations

The pipeline is entirely offline:
- No external API calls
- No data exfiltration possible
- No remote code execution vectors

### CSV Injection Protection

Output CSV files are sanitized against formula injection attacks:
- Cells starting with `=`, `+`, `-`, `@` are escaped
- UTF-8 BOM added for Excel compatibility

## Automated Monitoring

**GitHub Dependabot** is enabled to:
- Monitor dependencies for new CVEs
- Automatically create PRs for security updates

## Running Security Scans

```bash
# Install tools
pip install bandit pip-audit

# Scan code for vulnerabilities
bandit -r src/ -f txt

# Check dependencies for CVEs
pip-audit
```

---

*Analysis performed: 2026-01-30*
