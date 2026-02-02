# Issue Review: G-FIAT: Rock Photo Classifier

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Technical Product Manager & Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The issue is structurally sound with clear intent and technical bounds. The heuristic approach is well-scoped for an MVP. However, the Acceptance Criteria rely on specific accuracy metrics (>80%) without an explicit requirement or task to generate the "Ground Truth" labeled dataset required to verify those metrics.

## Tier 1: BLOCKING Issues
No blocking issues found. Issue is actionable.

### Security
- [ ] No issues found.

### Safety
- [ ] **Resilience to Resource Exhaustion:** The issue uses `PIL/Pillow` to process external files. It must explicitly state handling for "Decompression Bombs" (extremely large images compressed into small files) to prevent the script from crashing the host machine.
    *   *Recommendation:* Add requirement to set `Image.MAX_IMAGE_PIXELS` or strictly validate file size/dimensions before loading into memory.

### Cost
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Quality
- [ ] **Unverifiable Accuracy Metrics:** The Acceptance Criteria specify ">80% accuracy" and ">90% accuracy." However, the Requirements do not include a task to "Create/Label Ground Truth Dataset." Without a pre-labeled dataset of known classifications, these percentages cannot be mathematically verified.
    *   *Recommendation:* Add a Requirement or DoD item: "Curate and label a test dataset of at least N images (covering all classes) to serve as the Ground Truth for accuracy calculations."

### Architecture
- [ ] **Unlinked Dependency:** The Dependencies section mentions "Image extraction module must be complete" but does not link to the specific issue or the defined Manifest Schema.
    *   *Recommendation:* Link the antecedent issue ID or attach the expected JSON schema for the manifest input to ensure the reader knows strictly what `src.gfiat.classify` is consuming.

## Tier 3: SUGGESTIONS
- **Taxonomy:** Add label `feature` and `mvp`.
- **Testing:** Consider adding a "Confusion Matrix" to the output of the test run to visualize which categories are overlapping (e.g., distinguishing "chart" from "diagram").

## Questions for Orchestrator
1. Does a labeled library of rock photos vs. generic document images already exist, or does the developer need to spend time creating this dataset as part of this ticket?

## Verdict
[ ] **APPROVED** - Ready to enter backlog
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision