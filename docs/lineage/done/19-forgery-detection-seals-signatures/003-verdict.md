# Issue Review: Forgery Detection: Seals and Signatures

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
**PASSED**

## Review Summary
The issue is technically detailed and includes strong user stories and flows. However, it fails Tier 1 checks regarding Cost (ML inference budget) and Legal (Explicit data residency for biometric/signature data). It also requires tighter definitions for image processing security.

## Tier 1: BLOCKING Issues

### Security
- [ ] **Malicious Payload Mitigation:** The issue involves processing user-uploaded binaries (images/PDFs) using libraries like OpenCV and Pillow. These are common vectors for buffer overflow or "ImageTragick" style exploits.
    *   **Recommendation:** Explicitly add a requirement for input sanitization or sandboxed processing (e.g., "Process images in ephemeral containers" or "sanitize headers before passing to OpenCV").

### Safety
- [ ] No blocking issues found.

### Cost
- [ ] **Missing Compute Budget:** The Technical Approach mentions CNN-based models and Ensembles. This implies significant CPU/GPU usage compared to standard text processing.
    *   **Recommendation:** Provide a rough estimate of the infrastructure cost increase (e.g., "Requires moving to GPU instances" or "Estimated $X/month increase in compute for CPU inference").

### Legal
- [ ] **Biometric Data Residency:** The issue deals with signatures (biometric data). While "Privacy & Data Residency" is touched upon in Security Considerations, it does not explicitly mandate *where* the processing occurs.
    *   **Recommendation:** Explicitly state "Local-Only execution / No external API transmission of signature data" to prevent developers from plugging in 3rd-party vision APIs during implementation.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Vague Acceptance Criteria:** "Verify seal clarity meets minimum threshold" is not binary.
    *   **Recommendation:** Define the threshold or the metric (e.g., "Laplacian variance > 100").
- [ ] **Vague Acceptance Criteria:** "Flags compression inconsistencies with configurable sensitivity."
    *   **Recommendation:** Define the default success state (e.g., "Detects 90% of Error Level Analysis discrepancies on test set 4").

### Architecture
- [ ] **Unlinked Dependency:** The issue references "Existing validation pipeline" multiple times but does not link to the specific issue or ID that defined it, nor does it confirm that pipeline is in a "Done" state.
    *   **Recommendation:** Link the dependency issue ID.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add `machine-learning`, `security`, and `feature` labels.
- **Effort Estimate:** Add T-Shirt size (Likely XL due to model tuning requirements).
- **Performance:** A 500ms latency budget for an ensemble of CNN + OpenCV + ELA might be optimistic on standard hardware. Consider loosening or specifying hardware requirements.

## Questions for Orchestrator
1. Do we have a legal precedent for storing "reference signatures" vs. hashing them? Storing raw reference signatures increases liability significantly.

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision