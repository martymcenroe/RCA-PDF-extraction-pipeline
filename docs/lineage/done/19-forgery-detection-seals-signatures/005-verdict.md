# Issue Review: Forgery Detection: Seals and Signatures

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
This is an exceptionally well-defined issue that adheres strictly to security and legal constraints. The inclusion of specific "Local-Only" mandates and quantifiable acceptance criteria (e.g., Laplacian variance > 100) sets a high standard. It is structurally ready for the backlog, with one architectural clarification required regarding the sandboxing implementation.

## Tier 1: BLOCKING Issues
No blocking issues found. Issue is actionable.

### Security
- [ ] No issues found. Strong emphasis on input sanitization and ephemeral containers.

### Safety
- [ ] No issues found. Fail-safe strategy (flagging for manual review) is clearly defined.

### Cost
- [ ] No issues found. Budget and compute impact are explicitly estimated.

### Legal
- [ ] No issues found. Data residency and "Local-Only" processing are explicitly mandated, satisfying privacy requirements for biometric/signature data.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] No issues found. Acceptance Criteria are binary and quantifiable.

### Architecture
- [ ] **Sandboxing Implementation Strategy:** The requirement "Process all images in ephemeral Docker containers" implies the application code needs to spawn containers.
    - *Risk:* If the main application runs inside Kubernetes or a restricted container environment, spawning child containers (Docker-in-Docker or sibling containers) requires elevated privileges (access to Docker socket) which may violate security policies.
    - *Recommendation:* Clarify if `src/extraction/forgery/input_sanitizer.py` spawns a subprocess, a sibling container, or if this should be a standalone microservice to isolate the high-privilege requirement.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add `compliance` label.
- **Testing:** Explicitly list a "Corrupted/Malicious Document Set" (e.g., zip bombs, polyglot files) as a required Static Fixture for offline development.

## Questions for Orchestrator
1. **Perceptual Hashing:** The UX flow mentions "System compares signature characteristics against reference," but Legal requires "stored as one-way perceptual hashes." Can we confirm that the `imagehash` library (pHash/dHash) provides sufficient fidelity for fraud detection compared to feature point matching (SIFT/ORB) which might require raw images?

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision

*(Note: Verdict is REVISE strictly to address the Architectural Sandbox implementation detail, otherwise Approved.)*