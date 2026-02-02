# LLD Review: 134-Feature: Historical Reference Database for Cross-Report Image Comparison

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD is well-structured and has successfully addressed the critical safety concerns (partial deletion) and structure issues from the previous review. However, a significant design gap remains regarding the cleanup of physical files during re-ingestion, which creates a resource leak. This needs to be addressed in the logic and test plan before implementation.

## Tier 1: BLOCKING Issues
No blocking issues found. LLD is approved for implementation regarding Tier 1.

### Cost
- [ ] No issues found.

### Safety
- [ ] No issues found. The "delete before insert" logic refactor in Section 2.5 correctly addresses the previous data loss risk. The use of `--force` is accepted as the explicit confirmation mechanism for automation purposes.

### Security
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Ambiguous Storage Root:** The LLD specifies storing files in `data/sift/` but does not define how this path is resolved (e.g., relative to CWD vs. Project Root). If the tool is run from different directories, it may create fragmented data silos or write to unexpected locations.
    - **Recommendation:** Explicitly define the `data_dir` resolution logic in Section 2.5 (e.g., "Resolve `data/` relative to the project root detected via `pyproject.toml` location" or "Use `GFHAT_DATA_DIR` env var with a default").

### Observability
- [ ] No issues found.

### Quality
- [ ] **Orphaned File Leak (Resource Management):** In Section 2.5 (Ingestion Flow, Step 6c), the logic states: "Delete ALL existing entries for this PDF". This deletes the database metadata but fails to delete the corresponding physical `.npy` files stored on disk. Using `--force` repeatedly will cause `data/sift/` to accumulate orphaned, unreferenced SIFT files, leading to disk exhaustion over time.
    - **Recommendation:** Update Section 2.5 Logic Flow to: "Query and retrieve list of `sift_file` paths for the PDF, then delete physical files, THEN delete DB entries."
- [ ] **Missing Test for File Cleanup:** While Test 025 checks that *new* data persists, no test verifies that *old* files are physically removed.
    - **Recommendation:** Add a test scenario (e.g., "Verify physical file cleanup on force") where a PDF is ingested, then re-ingested with `--force`, asserting that the old `.npy` file paths no longer exist on disk.

## Tier 3: SUGGESTIONS
- **Performance:** Consider adding a `vacuum` command or logic to future-proof against database fragmentation, though SQLite handles this reasonably well.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision