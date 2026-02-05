# LLD Review: 25 - Feature: Texas University Lands Data Ingestion Module

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD provides a solid foundation for the Texas University Lands ingestion module, correctly utilizing the asynchronous patterns established in the core framework. The architecture is sound, with clear separation of concerns between discovery, filtering, and downloading. However, the Test Plan has a critical gap regarding the reliability requirements (retry logic), resulting in a requirement coverage failure that blocks approval.

## Open Questions Resolved
- [x] ~~Does the Texas University Lands portal require registration/authentication for bulk access?~~ **RESOLVED: Proceed assuming public access based on current portal behavior. If 403s are encountered during crawling (beyond `robots.txt` checks), the `SourceModule` should be updated to support auth injection, but for MVP, public access is the working assumption.**
- [x] ~~What is the exact API/web interface structure for querying wells by county?~~ **RESOLVED: Use browser developer tools to inspect the Network tab while performing a manual search on `ulands.utexas.edu`. Map the form data/query parameters to the `httpx` request in `discover_wells`.**
- [x] ~~Are there specific document type codes that indicate RCA content beyond keyword matching?~~ **RESOLVED: Stick to Keyword Matching (Req 3) for the MVP. Log the available `document_type` fields in the manifest during ingestion to analyze and build a mapping for a future optimization iteration.**

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | Module MUST check and respect `robots.txt` | T090, T100 | ✓ Covered |
| 2 | Module MUST query at least 10 priority counties | T150 (Integration) | ✓ Covered |
| 3 | Module MUST filter documents using RCA keywords | T020, T030 | ✓ Covered |
| 4 | Module MUST enforce 1 request/second rate limit | T060 | ✓ Covered |
| 5 | Module MUST retry failed requests with exponential backoff | - | **GAP** |
| 6 | Module MUST store files at `data/raw/texas/{county}/{api_number}.pdf.zst` | T080, T130 | ✓ Covered |
| 7 | Module MUST update manifest after each download | T130 | ✓ Covered |
| 8 | Module MUST handle 403/restricted responses gracefully | T070 | ✓ Covered |
| 9 | Module MUST support `--dry-run` flag | T110 | ✓ Covered |
| 10 | Module MUST support `--limit N` flag | T120 | ✓ Covered |
| 11 | Module MUST checkpoint for resumability | T140 | ✓ Covered |
| 12 | All data MUST remain LOCAL-ONLY | T150 (verifies local file creation) | ✓ Covered |

**Coverage Calculation:** 11 requirements covered / 12 total = **91.6%**

**Verdict:** BLOCK (Coverage < 95%)

**Missing Test Scenarios:**
- **Requirement 5 (Retry Logic):** There is no test verifying that transient errors (e.g., HTTP 500, 502, or ConnectionError) trigger the retry mechanism with backoff. T070 only covers 403 Forbidden (which correctly skips without retry). A new test `test_retry_logic_on_transient_error` is required.

## Tier 1: BLOCKING Issues
No Tier 1 blocking issues found.

### Cost
- No issues found.

### Safety
- No issues found.

### Security
- No issues found.

### Legal
- No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- No issues found.

### Observability
- No issues found.

### Quality
- [ ] **Requirement Coverage:** The Test Plan misses Requirement #5 (Retry logic). 
    - **Recommendation:** Add `T065 | test_retry_on_transient_error | Mock 500 error then success | Retries occur, success returned`.
- [ ] **TDD Test Plan Gap:** The test plan includes T010 for county search, but relies on T150 (End-to-End) to verify the iteration over the *list* of priority counties (Req 2). While acceptable, explicit unit testing of the priority list configuration would be more robust.

## Tier 3: SUGGESTIONS
- **Reliability:** Ensure the `sanitize_county_name` function handles spaces (replace with underscores) and periods (remove) to ensure cross-platform compatibility.
- **Observability:** Consider adding a specific metric for `bytes_downloaded` in addition to `documents_downloaded` to track storage impact.

## Questions for Orchestrator
None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision