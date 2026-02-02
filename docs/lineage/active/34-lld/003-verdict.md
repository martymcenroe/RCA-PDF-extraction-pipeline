# LLD Review: #134 - Feature: Historical Reference Database for Cross-Report Image Comparison

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD provides a solid foundation for the database schema and SIFT integration. However, it contains a **Critical Logic Flaw** in the ingestion pseudocode that would cause unintended data loss during batch processing. Additionally, the document retains "Open Questions" that must be resolved to be the source of truth, and directory structures need verification.

## Tier 1: BLOCKING Issues

### Cost
No blocking issues found.

### Safety
- [ ] **Unsafe Destructive Logic (CRITICAL):** In Section 2.5 (Ingestion Flow), the logic to "Delete existing entries for this PDF" (Step 5d) is placed **inside** the loop iterating over individual images (Step 5).
    - **Impact:** If `report.pdf` contains 10 images, processing Image 2 will trigger the delete (since the PDF exists), wiping the record just inserted for Image 1. Only the final image of the PDF will remain.
    - **Recommendation:** Refactor logic to group images by Source PDF first. Perform the "Delete existing" operation **once** per PDF before entering the image insertion loop.

### Security
No blocking issues found.

### Legal
No blocking issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Unresolved Open Questions:** Section 1 lists "Open Questions" (SIFT directory organization, DB size) that are marked "Remove when resolved". An LLD must be the source of truth.
    - **Recommendation:** Decide on the approach (e.g., "Organize SIFT files by PDF-derived hash directory") and update Section 2.5/2.3, then remove the questions.
- [ ] **Path Structure Verification:** The LLD specifies paths starting with `src/gfiat/`.
    - **Recommendation:** Verify if the project uses the `src/` layout or a flat layout (`gfiat/`). If the project does not use `src/`, update all file paths in Section 2.1.

### Observability
No high-priority issues found.

### Quality
- [ ] **Missing Schema Tests:** `src/gfiat/db/schema.py` is introduced to handle DB initialization and migrations, but no `tests/test_db_schema.py` is listed in Section 2.1 or 10.
    - **Recommendation:** Add `tests/test_db_schema.py` to verify table creation and **index existence** (Req #2) independently of the ingestion logic.

## Tier 3: SUGGESTIONS
- **Explicit SIFT Structure:** In Section 2.5, step 5e, clarify the directory structure for `.npy` files. Grouping by PDF filename or hash prevents the root SIFT directory from becoming unmanageable (e.g., `data/sift/{pdf_hash}/{image_id}.npy`).
- **Test Coverage:** Add a specific test case in Section 10 (e.g., "Ingest PDF with multiple pages") to regression-test the "Safety" bug identified above, ensuring all pages persist after a `--force` ingest.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision