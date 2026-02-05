# LLD Review: 23-Feature: Data Ingestion Core Framework + USGS CRC Module

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The LLD presents a robust architecture for data ingestion with strong emphasis on safety (path sanitization), resilience (circuit breakers, checkpointing), and data integrity (manifests, hashing). The design uses appropriate modern Python patterns (async/httpx, click). However, the document is **BLOCKED** due to insufficient test coverage (Requirement #8 regarding the status command is untested) and unresolved open questions in Section 1.

## Open Questions Resolved
- [x] ~~What is the expected catalog HTML structure from USGS CRC? Need sample for parser development.~~ **RESOLVED: Use browser Developer Tools (Network Tab) to capture the response body from a search on `https://my.usgs.gov/crc/`. Save this HTML as `tests/fixtures/usgs_catalog.html` to create your parser test fixture.**
- [x] ~~Are there any USGS-specific robots.txt restrictions to honor?~~ **RESOLVED: Yes, you must respect `https://my.usgs.gov/robots.txt`. Ensure your HTTP client sets a descriptive User-Agent string (e.g., `Project-Ingestor/0.1`) and strictly adheres to the 1 request/second limit defined in your design.**

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| 1 | `ingest usgs --limit 5` downloads 5 RCA PDFs | T200, T190 | ✓ Covered |
| 2 | Files zstd-compressed with `.pdf.zst` | T110, T190 | ✓ Covered |
| 3 | Manifest file created with SHA256 | T080, T190 | ✓ Covered |
| 4 | Resume from checkpoint without re-downloading | T170, T130 | ✓ Covered |
| 5 | Rate limiting enforces 1 request/second | **GAP** | **MISSING** |
| 6 | Circuit breaker opens after 5 failures | T090 | ✓ Covered |
| 7 | `--dry-run` discovers without downloading | T160 | ✓ Covered |
| 8 | `status` command shows counts | **GAP** | **MISSING** |
| 9 | 404 errors logged, no crash | T180 | ✓ Covered |
| 10 | Path traversal rejected | T030, T040 | ✓ Covered |
| 11 | Invalid state codes rejected | T020 | ✓ Covered |
| 12 | Filenames contain safe chars only | T050, T060, T120 | ✓ Covered |

**Coverage Calculation:** 10 requirements covered / 12 total = **83.3%**

**Verdict:** **BLOCK** (<95%)

**Missing Test Scenarios:**
1.  **Test for Req #5 (Rate Limiting):** Add a test (e.g., `test_rate_limiter_timing`) that mocks `time.sleep` or uses `freezegun` to verify that subsequent requests are delayed by at least 1.0 second.
2.  **Test for Req #8 (Status Command):** Add a test (e.g., `test_cli_status_output`) that invokes the `status` command with a known checkpoint state and asserts the output contains correct counts.

## Tier 1: BLOCKING Issues
No blocking Cost, Safety, Security, or Legal issues found. The design is conservative and safe.

### Cost
- [ ] No issues found.

### Safety
- [ ] No issues found.

### Security
- [ ] No issues found.

### Legal
- [ ] No issues found.

## Tier 2: HIGH PRIORITY Issues

### Architecture
- [ ] No issues found.

### Observability
- [ ] No issues found.

### Quality
- [ ] **Requirement Coverage:** Coverage is 83.3% (Target: ≥95%). Two requirements (#5 Rate Limiting and #8 Status Command) are not mapped to specific test scenarios in Section 10.1. Please add T210 and T220 to cover these.

## Tier 3: SUGGESTIONS
- **Maintainability:** Consider separating the `USGSModule` logic into `USGSClient` (network) and `USGSParser` (HTML logic) if the file grows beyond 300 lines.
- **Performance:** In `_parse_catalog_page`, ensure you are using a generator or streaming parser if the catalog pages are extremely large, though for standard pagination this is likely fine.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision