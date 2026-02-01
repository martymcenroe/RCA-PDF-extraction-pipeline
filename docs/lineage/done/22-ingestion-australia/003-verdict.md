# Issue Review: Australian WAPIMS Data Ingestion Module

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is technically robust, particularly in its definition of the batch/basket logic and fallback strategies. However, it fails Tier 1 blocking checks regarding explicit security requirements for file handling, cost estimates for storage, and mandatory data residency declarations. These must be rectified to meet the "Definition of Ready."

## Tier 1: BLOCKING Issues

### Security
- [ ] **Path Sanitization Requirement Missing:** While `test_target_path_sanitization` is mentioned in Testing Notes, the **Requirements** section does not explicitly mandate sanitizing `well_name` and `basin` strings derived from the API.
    *   *Recommendation:* Add a specific item under "Storage & Compression" requirements: "Sanitize basin and well names to remove characters invalid for filesystems or that could lead to directory traversal before path creation."

### Safety
- [ ] No issues found.

### Cost
- [ ] **Missing Storage/Budget Estimate:** The issue involves downloading PDF documents (potentially in bulk). While API costs are zero, storage impact is non-zero.
    *   *Recommendation:* Add a "Resource Estimation" section. State the expected storage footprint (e.g., "Est. < 500MB for initial MVP runs") or confirm it fits within existing storage quotas.

### Legal
- [ ] **Data Residency & Transmission:** The issue is a scraper/ingestion module but lacks the mandatory "Local-Only" declaration required by Audit 0815.
    *   *Recommendation:* Explicitly state in the "Security Considerations" or "Legal" section: "Data processing is Local-Only; no scraped data is transmitted to external third-party services."

## Tier 2: HIGH PRIORITY Issues
No high-priority issues found. Context is complete.

### Quality
- [ ] No issues found.

### Architecture
- [ ] No issues found.

## Tier 3: SUGGESTIONS
- **Effort Estimate:** Add a T-shirt size (Likely **L** given the complexity of the batch polling + fallback logic).
- **Taxonomy:** Add label `module: ingestion`.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision