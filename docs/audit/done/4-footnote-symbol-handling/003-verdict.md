# Issue Review: Improved Footnote Symbol Handling for PDF Table Extraction

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is well-defined regarding the business logic and happy paths for data extraction. However, it fails the Tier 1 Security check because it claims "No security implications" while introducing a specific vector for CSV Injection (Formula Injection) by enforcing the preservation of leading `+` symbols in CSV output.

## Tier 1: BLOCKING Issues

### Security
- [ ] **Output Sanitization (CSV Injection):** The requirement to preserve leading `+` and potential `=` symbols in the CSV output creates a CSV Injection vulnerability if the data is viewed in Excel/Sheets (formulas will execute). The draft explicitly states "No security implications," which is incorrect.
    *   **Recommendation:** Update "Security Considerations" to either mandate escaping strategies (e.g., prepending a single quote `'`) or explicitly document the risk acceptance if the CSV is strictly for machine consumption.

### Safety
- [ ] No issues found.

### Cost
- [ ] No issues found.

### Legal
- [ ] **Privacy & Data Residency:** While "No external API calls" is mentioned in Security, strict governance requires an explicit **Data Residency** statement in the Legal/Compliance context.
    *   **Recommendation:** Explicitly state: "Data processing is Local-Only. No external transmission of PDF content."

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Edge Case Handling (False Positives):** The requirements define indicators (`+`, `**`), but do not define behavior for "False Positives" (e.g., a text note that legitimately starts with a `+` but isn't a merged cell).
    *   **Recommendation:** Add an Acceptance Criterion for handling or explicitly ignoring false positives (e.g., "Text starting with `+` in non-numeric columns should/should not trigger expansion").

### Architecture
- [ ] No issues found.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add labels: `enhancement`, `data-extraction`, `csv`.
- **Effort Estimate:** Add T-shirt size (appears to be Size S/M).

## Questions for Orchestrator
1. Is the output CSV intended for direct human analysis in Excel, or is it purely for downstream machine ingestion? (This determines the severity of the CSV Injection blocker).

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision