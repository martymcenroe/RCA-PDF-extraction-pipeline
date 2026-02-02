# Issue Review: G-FIAT: Lossless PDF Image Extraction

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
**PASSED**

## Review Summary
The issue is technically robust with clear User Stories, UX Flows, and "Definition of Done" criteria. However, it is **BLOCKED** by a critical Legal Tier 1 issue regarding dependency licensing (PyMuPDF). This must be resolved before the issue can enter the backlog.

## Tier 1: BLOCKING Issues

### Security
- [ ] No blocking issues found. "Offline operation" mitigates most risks.

### Safety
- [ ] No blocking issues found.

### Cost
- [ ] No blocking issues found.

### Legal
- [ ] **License Compliance (CRITICAL):** The Technical Approach specifies `PyMuPDF`. This library is licensed under **AGPL v3.0**, which is a "viral" copyleft license. Unless G-FIAT is also open-sourced under AGPL v3.0, using PyMuPDF may legally force the entire project to be open-sourced or require a commercial license. **Action:** Confirm G-FIAT's license compatibility or switch to a permissive alternative (e.g., `pdfminer.six` or `pypdf`).
- [ ] **Privacy & Data Residency:** Issue acknowledges PII and states "No network access required." This is acceptable, but please add an explicit line in "Requirements" mandating: *"Tool must not transmit any data externally; local filesystem operations only."*

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Acceptance Criteria Precision:** "Exit code 0 on success, non-zero on failure with descriptive error" is slightly vague. **Recommendation:** Specify behavior: "On failure, print error message to `stderr` containing the specific exception type and file path, then exit with code `1`."
- [ ] **Robustness:** The "Risk Checklist" mentions Architecture is "No." However, PDF parsing is notoriously fragile. **Recommendation:** Add a requirement for a timeout mechanism or memory limit to prevent the CLI from hanging on "zip bomb" style PDFs.

### Architecture
- [ ] No high-priority issues found. Architecture matches requirements.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add labels `feature`, `core-infrastructure`, `blocked-legal`.
- **Effort Estimate:** Recommended T-Shirt size: **M** (due to edge cases in PDF binary streams).
- **Testing:** Consider adding a test case for a PDF with *no* images to verify the empty manifest generation explicitly.

## Questions for Orchestrator
1. What is the overarching license for the G-FIAT repository? (Determines if PyMuPDF is viable).
2. Is the extraction of "inline images" truly out of scope for MVP? (Some forensic artifacts may hide there).

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision