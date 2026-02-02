# Issue Review: G-FIAT: Perceptual Hash (pHash) Fingerprinting

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
This is a high-quality draft with excellent attention to edge cases (corruption, missing directories) and specific performance metrics. However, there is a logical gap between the "Corrupted Image" handling and the "Comparison" logic that needs to be addressed in the Requirements/AC to prevent runtime errors.

## Tier 1: BLOCKING Issues
No blocking issues found. Issue is actionable.

### Security
- [ ] No issues found.

### Safety
- [ ] No issues found.

### Cost
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Acceptance Criteria / Logic Gap:** Scenario 3 establishes that corrupted images receive `"phash": null`. However, Scenario 2 (Comparison) and the "Similarity Comparison" requirements do not explicitly state how to handle `null` values. Computing Hamming distance on `null` will likely raise a TypeError.
    - **Recommendation:** Add a requirement/AC to the Comparison section: "Comparison logic must explicitly skip or ignore image entries where `phash` is null/missing."
- [ ] **Vague AC:** The criterion "CLI command ... works" is subjective.
    - **Recommendation:** Refine to "CLI command executes with Exit Code 0 on success and updates manifest.json correctly."

### Architecture
- [ ] **Dependency Weight:** The `imagehash` library often depends on `scipy` and `numpy`.
    - **Recommendation:** Verify if `scipy` is already in the project stack. If not, consider if a lighter-weight pure-implementation of pHash is preferable to adding a heavy dependency for a single feature. This is not a blocker, but an architectural consideration to note.

## Tier 3: SUGGESTIONS
- **Dependency Tracking:** Ensure Issue #103 is strictly verified as "Done" or that specific fixture data from #103 is available for development.
- **Test Coverage:** Consider adding a test case for "Very dark/black images" which sometimes cause issues with DCT-based hashing median calculations.

## Questions for Orchestrator
1. Is the project environment already using `numpy`/`scipy`? (affects dependency decision)

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision