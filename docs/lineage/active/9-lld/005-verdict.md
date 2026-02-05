# LLD Review: 19 - Feature: Data Analysis & Validation for Extracted Core Samples

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD provides a solid foundation for the data analysis feature with a clear modular structure and well-defined validation rules. However, the **Requirement Coverage** falls below the 95% threshold. Several output requirements (file generation, console reporting) are not explicitly verified by the proposed automated tests. These must be addressed before implementation.

## Open Questions Resolved
- [x] ~~Should the script support batch processing of multiple CSV files?~~ **RESOLVED: No.** Keep the MVP simple. The current scope is for a single extracted file. Batch processing can be added later if needed (YAGNI).
- [x] ~~What format should the JSON export use for downstream consumption?~~ **RESOLVED: Simple Dictionary.** Use a flat or nested JSON object reflecting the `SummaryStatistics` TypedDict structure defined in Section 2.3.
- [x] ~~Should fracture samples have a distinct visual marker in plots?~~ **RESOLVED: Yes.** Use a distinct marker shape (e.g., 'x') or color (e.g., red) to clearly differentiate fracture samples from standard core samples in visualizations.

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | Script accepts CSV file path as positional argument | T110, T120 | ✓ Covered |
| 2 | Structural validation checks row count, column count, duplicates, and cores | T010, T020, T030, T040 | ✓ Covered |
| 3 | Range validation flags out-of-bound values with appropriate severity | T050, T060, T070 | ✓ Covered |
| 4 | Consistency validation catches depth ordering and porosity/saturation mismatches | T080, T090 | ✓ Covered |
| 5 | Summary statistics handle special values (+, **, NaN) correctly | T100 | ✓ Covered |
| 6 | Four visualization plots saved to output directory | - | **GAP** |
| 7 | Console report shows PASS/WARN/FAIL with emoji indicators | - | **GAP** |
| 8 | Text report saved to `data/output/analysis/validation_report.txt` | - | **GAP** |
| 9 | Exit code reflects validation status (0=pass, 1=warn, 2=fail) | T110, T120, T130 | ✓ Covered |
| 10 | Missing file produces clear error message with usage | T110 | ✓ Covered |

**Coverage Calculation:** 7 requirements covered / 10 total = **70%**

**Verdict:** **BLOCK**

**Missing Test Scenarios:**
The following tests must be added to Section 10 to meet coverage requirements:
1.  **test_visualizations_created:** Run valid analysis and assert that the 4 specific PNG files exist in the output directory and have non-zero size.
2.  **test_report_generation:** Run analysis and assert `validation_report.txt` exists and contains expected content sections.
3.  **test_console_output_formatting:** Use `capsys` fixture to verify stdout contains specific emoji indicators and status strings.

## Tier 1: BLOCKING Issues
No blocking issues found in Cost, Safety, Security, or Legal categories. LLD is approved for these aspects.

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
- [ ] **Requirement Coverage:** 70% coverage is below the 95% threshold. Requirement #6, #7, and #8 regarding output artifacts (plots, text reports, console text) are essential deliverables but have no automated verification.
    *   **Recommendation:** Add the missing test scenarios listed in the Requirement Coverage section above to `tests/test_analyze_output.py`. Do not rely on "Manual Tests" for file existence checks; these can and must be automated.

## Tier 3: SUGGESTIONS
- **Logging:** While `print` is sufficient for a CLI tool, consider writing a `analysis.log` alongside the report for debugging execution traces if the script grows in complexity.
- **Visuals:** For Requirement 6, ensure the `create_*` functions return the path to the created file, making the test assertions cleaner.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision