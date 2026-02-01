# Issue Review: Norwegian DISKOS Data Ingestion Module

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is technically robust with excellent detail in UX flows, testing strategies, and error handling. However, it fails the "Definition of Ready" due to missing explicit statements regarding Data Residency (Legal) and specific License compliance for the targeted datasets. These must be codified before approval.

## Tier 1: BLOCKING Issues

### Security
- [ ] No blocking issues found. Input sanitization is addressed in Technical Approach.

### Safety
- [ ] No blocking issues found. Fail-safe strategies are defined.

### Cost
- [ ] **Infrastructure Impact Ambiguity:** The issue implies a CLI tool (`python -m ...`) but does not specify if this is intended for local execution only or a cloud-based job.
    - *Recommendation:* Explicitly state the intended runtime environment. If Cloud/CI, provide a budget estimate for storage (Volve is large; even filtered, it can be significant) and compute duration.

### Legal
- [ ] **Privacy & Data Residency (CRITICAL):** While the data is public, the issue is a scraper/ingestion tool. It fails to explicitly mandate where the data is processed or stored.
    - *Recommendation:* Add a "Data Handling" section. Explicitly state "Local-Only processing" OR define the specific cloud region/storage bucket requirements to ensure compliance with potential EU/EEA data export restrictions (if applicable to DISKOS).
- [ ] **License Compliance:** The issue states Volve is "released by Equinor for research" but does not cite the specific license (e.g., CC-BY 4.0, OGL).
    - *Recommendation:* Verify and list the specific license model for both Volve and DISKOS public data to ensure compatibility with the project's license.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] No high-priority quality issues found. Acceptance Criteria are quantifiable.

### Architecture
- [ ] **Offline Development / Fixtures:** The `Testing Notes` mention mocking the server (`test_volve_well_discovery`), but do not explicitly require saving static HTML/JSON fixtures.
    - *Recommendation:* Add a requirement to `Definition of Done` or `Technical Approach` to capture and commit "Golden Master" HTML/JSON responses to `tests/fixtures/norway/` to ensure the test suite runs without any network calls or mock generation logic.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add labels `ingestion`, `norway`, `external-data`.
- **Effort Estimate:** Add a T-shirt size estimate (Likely "Medium" or 3-5 Story Points).
- **Refinement:** Consider adding a `--force` flag to the CLI requirements to overwrite existing files if needed.

## Questions for Orchestrator
1. Does the DISKOS Terms of Service have specific clauses regarding automated scraping rates (robot.txt) that might override our generic "1 request/second" limit?

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision