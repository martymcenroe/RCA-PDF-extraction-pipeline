# Issue Review: Spec vs Extended Output Comparison Quality Gate

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is structurally sound and provides a strong reference implementation for CSVs. However, there is a critical architectural oversight regarding row ordering in the streaming approach, and the JSON requirements are not reflected in the technical approach or reference code. These must be resolved to ensure the tool functions as intended.

## Tier 1: BLOCKING Issues

### Security
- [ ] **Security Control Mismatch:** The "Security Considerations" section claims "File paths validated to prevent directory traversal," but the provided reference implementation (`compare_outputs.py`) performs no such validation (it merely checks `.exists()`).
    *   **Recommendation:** Either remove the claim if deemed unnecessary for a CI tool, or update the AC/Implementation to strictly require `os.path.abspath` / `commonprefix` checks to ensure paths remain within the repo root.

### Safety
- [ ] No blocking issues found.

### Cost
- [ ] No blocking issues found.

### Legal
- [ ] No blocking issues found.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Requirement vs. Implementation Gap (JSON):** The Requirements and Acceptance Criteria explicitly list "JSON Comparison" and "JSON comparison covers classifications," but the Technical Approach and Implementation Reference **only** cover CSVs. Furthermore, standard `json` library (listed in dependencies) cannot "stream" large files; it loads the whole file, which contradicts the "Memory Efficiency" requirement for >500MB files.
    *   **Recommendation:** Remove JSON from scope OR update dependencies to include a streaming JSON parser (like `ijson` if allowed) and update the reference code to handle JSON.

### Architecture
- [ ] **Row Ordering Assumption (Critical):** The "True Streaming" approach using `zip(spec_reader, ext_reader)` assumes that both the Spec and Extended output files are **deterministically sorted** in the exact same order. If the pipelines process data concurrently or use sets, the rows may be out of order, causing `zip` to compare mismatched rows (e.g., Row 1 vs Row 5) and fail erroneously.
    *   **Recommendation:** Explicitly state in "Assumptions" that inputs must be pre-sorted, OR change the architecture to sort files (which breaks streaming/memory limits), OR require a pre-sort step in the CI workflow before this script runs.

## Tier 3: SUGGESTIONS
- **Constraint Clarification:** Clarify if `pandas` is strictly forbidden due to container size/build time, or just to keep dependencies low.
- **CLI UX:** Consider adding a `--verbose` flag to toggle the "limit diff output to 20 items" requirement.

## Questions for Orchestrator
1. **Deterministic Sorting:** Do the Spec and Extended pipelines guarantee identical row sort order by a Primary Key? If not, a streaming comparison approach is technically impossible without an external sort step.

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision