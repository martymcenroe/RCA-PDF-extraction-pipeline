# Issue Review: HTML Forensic Report Generator

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The draft is strong regarding user flow and functional requirements. However, it lacks specific technical gating for Stored XSS (Security) and misses explicit links to upstream dependencies (Architecture). These must be addressed to meet the Definition of Ready.

## Tier 1: BLOCKING Issues

### Security
- [ ] **Input Sanitization:** The draft acknowledges XSS risks but does not explicitly mandate sanitization of input data. The report consumes metadata (PDF Author, Keywords, Filenames) which can be malicious vectors for Stored XSS.
    - **Recommendation:** Add to Technical Approach: "Strict context-aware output encoding (autoescaping) must be enforced in Jinja2. All metadata fields derived from source documents must be treated as untrusted input."

### Safety
- [ ] No issues found. Fail-safe scenarios are well-defined.

### Cost
- [ ] No issues found.

### Legal
- [ ] No issues found. Privacy and local-only processing are adequately covered.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Vague Acceptance Criteria:** "Render correctly in Chrome, Firefox..." is subjective.
    - **Recommendation:** Refine to: "Report renders without console errors or horizontal scroll breakage in Chrome, Firefox, Safari, Edge (latest versions)."
- [ ] **Vague Acceptance Criteria:** "Print preview shows readable... output."
    - **Recommendation:** Refine to: "Print preview fits content to page width and does not break images across page boundaries."

### Architecture
- [ ] **Unlinked Dependency:** "Core analysis pipeline must be complete" is referenced but not linked.
    - **Recommendation:** Link the specific GitHub Issue ID for the analysis pipeline and confirm it is in "Done" state.
- [ ] **Missing Test Fixtures:** The test plan mentions testing with empty/large directories but doesn't specify creating a committed fixture.
    - **Recommendation:** Add to "Files to Create": `tests/fixtures/sample_analysis_output/` containing valid JSON and dummy images to ensure the report generator can be developed/tested without running the heavy analysis pipeline.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add labels: `feature`, `reporting`, `mvp`.
- **Effort:** Estimate looks like `Size: L` (approx 5-8 story points) due to the number of visualizations and templates required.
- **CLI:** Consider adding a `--open` flag to the CLI to automatically open the report in the default browser after generation.

## Questions for Orchestrator
1. Does the "Core analysis pipeline" output schema (JSON structure) already exist and is it frozen? If the schema changes, this report generator will break.

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision