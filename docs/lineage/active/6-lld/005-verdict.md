# LLD Review: #6-Feature: Analytics-Ready CSV Output Format

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The design for the analytics-ready CSV format is technically sound, with a strong focus on security (CSV injection prevention) and data integrity (explicit flag columns). The fail-open strategy for transformation errors is appropriate. However, the LLD is **BLOCKED** due to insufficient test coverage for requirements regarding legacy output preservation and error logging details.

## Open Questions Resolved
No open questions found in Section 1 (all marked resolved).

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | Running with `--analytics` produces `core_analysis_analytics.csv` | T180 | ✓ Covered |
| 2 | No empty cells exist in analytics output (all converted to `NA`) | T150 | ✓ Covered |
| 3 | Numeric columns parse as `float64` in pandas with `na_values=['NA']` | T160 | ✓ Covered |
| 4 | Sample numbers contain no parenthetical suffixes | T090, T100, T110 | ✓ Covered |
| 5 | `is_fracture` column correctly identifies fracture samples | T090, T100 | ✓ Covered |
| 6 | `permeability_below_detection` is TRUE if EITHER field is below detection | T120, T130, T135 | ✓ Covered |
| 7 | `saturation_no_data` is TRUE for rows with `**` marker | T140 | ✓ Covered |
| 8 | Original `core_analysis.csv` unchanged (human-readable format preserved) | - | **GAP** |
| 9 | String fields with leading `=`, `+`, `-`, `@` are prefixed with `'` | T010, T020, T030, T040 | ✓ Covered |
| 10 | Transformation failures log error and skip analytics file without aborting | T170 | ✓ Covered |
| 11 | Error message includes row/field context for debugging | - | **GAP** |

**Coverage Calculation:** 9 requirements covered / 11 total = **81%**

**Verdict:** **BLOCK** (Requires ≥95%)

**Missing Test Scenarios:**
1. **For Requirement 8:** Add a test (or expand T180) to verify that `core_analysis.csv` produced with `--analytics` is identical to one produced without it (content fidelity regression test).
2. **For Requirement 11:** Update T170 or add a new test to explicitly assert that the captured log message contains the Row ID or context data, not just that the file generation was skipped.

## Tier 1: BLOCKING Issues
No blocking issues found. LLD is approved for implementation pending Tier 2 fixes.

### Cost
- [ ] No issues found.

### Safety
- [ ] No issues found.

### Security
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] No issues found.

### Observability
- [ ] No issues found.

### Quality
- [ ] **Requirement Coverage:** Coverage is 81%, below the 95% threshold. See "Requirement Coverage Analysis" above for specific gaps regarding regression testing (Req 8) and error log verification (Req 11).
- [ ] **Test T170 Definition:** The pass criteria "Files present" is insufficient for Requirement 11. It must check `assert "Row 5" in caplog.text` (or similar) to ensure debugging context is actually logged.

## Tier 3: SUGGESTIONS
- **Cleanliness:** Section 1 Open Questions are marked resolved `[x]`. Per instructions, these should be removed from the final document to reduce noise.
- **Testing:** For T150 ("No empty cells"), consider checking strictly that *every* cell value is non-empty, rather than just pandas loading without error.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision