# Issue Review: Alberta AER Data Ingestion Module

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is structurally sound with excellent attention to testing and error handling scenarios. However, it fails Tier 1 checks regarding Cost estimation (storage/bandwidth) and Legal specifications (Data Residency/ToS compliance). These must be addressed before the work can be authorized.

## Tier 1: BLOCKING Issues

### Security
- [ ] No blocking issues found.

### Safety
- [ ] No blocking issues found.

### Cost
- [ ] **Budget Estimate Missing:** The issue implies downloading PDF documents for entire geological formations. There is no estimate of the volume (e.g., 10,000 wells @ 2MB each = 20GB). You must provide a "Worst Case" storage and bandwidth estimate to ensure we do not overrun infrastructure quotas.

### Legal
- [ ] **Data Residency & Transmission:** (CRITICAL) Since this involves Canadian government data, you must explicitly state the Data Residency requirement. Add the standard clause: "Data processing to remain Local-Only; No external transmission of raw documents permitted."
- [ ] **Scraping Compliance:** You state "No authentication required," but have you verified the AER Portal Terms of Service or `robots.txt` regarding automated scraping? Explicitly confirm in the issue that this approach complies with their Acceptable Use Policy.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] No high-priority issues found. Context is complete.

### Architecture
- [ ] **Missing API Contracts/Fixtures:** While you mention "mock AER server," the issue does not attach or link to an example JSON response from the AER portal or a sample UWI format. Please attach a `sample_response.json` so the developer can build the parser offline without hitting the live endpoint.

## Tier 3: SUGGESTIONS
- Add label `ingestion` and `region:canada`.
- Add T-shirt size (Likely `M` given the complexity of UWI parsing and pdf handling).

## Questions for Orchestrator
1. Does the target AER portal have IP banning mechanisms that require proxy rotation, or is the 1 req/sec rate limit officially documented as safe?

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision