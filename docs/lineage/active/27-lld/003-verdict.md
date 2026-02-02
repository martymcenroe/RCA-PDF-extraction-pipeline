# LLD Review: 127 - Feature: G-FIAT: Lossless PDF Image Extraction

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD provides a strong foundation for the G-FIAT extraction tool with excellent test coverage plans. However, it contains unresolved "Open Questions" and "TODO" items in critical safety sections that must be defined before implementation. Specifically, the Logic Flow does not strictly implement the "Fail Closed" safety strategy regarding partial output cleanup.

## Tier 1: BLOCKING Issues

### Safety
- [ ] **Fail-Safe Strategy Implementation:** Section 7.2 states a "Fail Closed" strategy ("do not produce partial output"), but the Logic Flow (Section 2.5) does not include steps to clean up/remove the output directory in the `CATCH` blocks. If an error occurs halfway through, partial data is left on disk. **Fix:** Update Logic Flow to explicitly delete `output_dir` in the error handling blocks if the operation was not successful.

### Cost
- [ ] No issues found.

### Security
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] **Path Structure:** The LLD uses the `src/gfiat/` layout. **Verify:** Does the existing repository use a `src/` directory? If the project uses a flat layout (e.g., `gfiat/` at root), this LLD must be updated to match.
- [ ] **Incomplete Design (Open Questions):** Section 1 contains "Open Questions" regarding JBIG2 handling and Metadata fields. These must be resolved in the design, not during coding. **Recommendation:** (1) Define JBIG2 behavior (e.g., "Skip and log warning in manifest"), (2) List the specific required metadata fields in Section 2.3.

### Observability
- [ ] No issues found.

### Quality
- [ ] **Safety "TODO"s:** Section 7.2 lists "Symlink attacks" and "Resource exhaustion" mitigations as "TODO". **Fix:** Move these from TODO to the Logic Flow or explicitly define how they will be handled (e.g., using `Path.resolve()` in Step 1 of Logic Flow). Design documents should not contain TODOs for safety mechanisms.

## Tier 3: SUGGESTIONS
- **JBIG2 Handling:** Suggest logging JBIG2 streams as "skipped" in the manifest with a specific error code, rather than failing the entire PDF.
- **Memory Limit:** Explicitly add the `resource.setrlimit` call to the `main` or `extract_images` logic to enforce the 500MB cap mentioned in Section 8.1.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision