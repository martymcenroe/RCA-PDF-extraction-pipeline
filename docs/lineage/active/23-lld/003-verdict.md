# LLD Review: 1023 - Feature: Data Ingestion Core Framework + USGS CRC Module

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate: PASSED
All required elements (Issue Link, Context, Proposed Changes) are present.

## Review Summary
The LLD provides a solid foundation for the ingestion framework with clear separation of concerns and robust error handling. However, there is a **critical data consistency flaw** in the logic flow regarding checkpoints vs. manifests that effectively breaks the "resume" functionality. This requires revision before implementation to prevent data orphaning.

## Tier 1: BLOCKING Issues
No blocking issues found. LLD is approved for implementation subject to Tier 2 fixes.

### Cost
- No issues found.

### Safety
- No issues found. Fail-safe strategies are defined, though they need the architectural fix below to be effective.

### Security
- No issues found. Path traversal and sanitization are well-addressed.

### Legal
- No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Data Integrity / Race Condition (Logic Flow 2.5):** The design specifies saving the checkpoint *after each job* (Step 4e) but saving the manifest only *at the very end* (Step 5).
    - **Risk:** If the process crashes or is interrupted (Ctrl+C) after downloading 50 files (and updating the checkpoint 50 times) but before the final manifest save, the checkpoint will mark those IDs as "done", but they will **not** exist in `manifest.json`.
    - **Consequence:** Resuming the job will skip these files (because they are in the checkpoint), but the system has no record of where they are stored or their metadata (because the manifest wasn't saved). The data becomes orphaned.
    - **Recommendation:** Either save the manifest incrementally (after each job, similar to the checkpoint) or use an append-only format (like JSON Lines) for the manifest to ensure atomic durability of metadata alongside the checkpoint.

### Observability
- No issues found.

### Quality
- [ ] **Test vs. Design Contradiction (Test 120):** Test scenario 120 ("Manifest integrity after crash simulation") expects a valid manifest after a mid-ingestion kill. As noted in the Architecture issue above, the current design (saving manifest only at step 5) guarantees this test will **fail**. The design must be updated to match the test expectation.

## Tier 3: SUGGESTIONS
- **Path Structure:** The LLD uses the `src/` layout (`src/ingestion/...`). Ensure this matches the existing project structure. If the project root does not have a `src/` directory, remove this prefix.
- **Tenacity Usage:** The dependencies include `tenacity`, but the logic flow describes a manual try/catch block with exponential backoff. Consider using `tenacity` decorators (`@retry`) on the `download` method to simplify the controller logic.
- **Manifest Format:** Consider using JSON Lines (`.jsonl`) for the manifest. It allows for atomic appends (O(1)) without rewriting the entire file (O(N)) for every save, which scales better as the dataset grows to 10,000+ documents.

## Questions for Orchestrator
1. Does the existing repository use a `src/` directory layout? (The LLD assumes yes).

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision