# LLD Review: #23 - Feature: Data Ingestion Core Framework + USGS CRC Module

## Identity Confirmation
I am Gemini 3 Pro, acting as Senior Software Architect & AI Governance Lead.

## Pre-Flight Gate
PASSED

## Review Summary
The Low-Level Design is well-structured, architecturally sound, and demonstrates a strong "Safety First" approach with path sanitization and circuit breakers. However, strict Gatekeeper protocols require 95% test coverage of requirements defined in Section 3. The current test plan misses specific scenarios for the `status` command (R8), dropping coverage below the threshold. This must be remediated before approval.

## Open Questions Resolved
- [x] ~~Should we support proxy configuration for institutional network access?~~ **RESOLVED: No code changes required. Rely on standard `HTTP_PROXY` and `HTTPS_PROXY` environment variables, which `httpx` supports natively. This is the industry standard for CLI tools.**

## Requirement Coverage Analysis (MANDATORY)

**Section 3 Requirements:**
| # | Requirement | Test(s) | Status |
|---|-------------|---------|--------|
| R1 | `ingest` command downloads N items | T080, T110 (Integration test in 10.2) | ✓ Covered |
| R2 | zstd compression & .pdf.zst ext | T060 | ✓ Covered |
| R3 | Manifest tracking with SHA256 | T070 | ✓ Covered |
| R4 | Resume from checkpoint | T100 | ✓ Covered |
| R5 | Rate limiting (1s gap) | T080 | ✓ Covered |
| R6 | Circuit breaker (5 failures) | T090 | ✓ Covered |
| R7 | `--dry-run` flag | T120 | ✓ Covered |
| R8 | `status` command shows stats | - | **GAP** |
| R9 | 404 errors logged/safe | T130 | ✓ Covered |
| R10 | Path traversal rejected | T030, T140 | ✓ Covered |
| R11 | Invalid state codes rejected | T020 | ✓ Covered |
| R12 | Safe filenames only | T010, T040, T050, T150 | ✓ Covered |

**Coverage Calculation:** 11 requirements covered / 12 total = **91.6%**

**Verdict:** **BLOCK** (<95%)

**Missing Test Scenarios:**
- **R8:** Add a test scenario (e.g., `T160`) to verify the `status` command reads the checkpoint/manifest and outputs correct statistics.

## Tier 1: BLOCKING Issues
No blocking issues found in Cost, Safety, Security, or Legal categories.

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
- [ ] **Requirement Coverage:** Coverage is 91.6%, which is below the 95% threshold. You must add a test scenario for the `status` command to Section 10.1.
    *   *Recommendation:* Add `T160 | test_status_command_output | Auto | Checkpoint file exists | Displays stats to stdout | stdout contains correct counts`

## Tier 3: SUGGESTIONS
- **Maintainability:** Consider explicitly defining the `User-Agent` header in the `httpx.AsyncClient` initialization to identify the bot politely (e.g., "USGS-Ingestion-Bot/1.0").
- **Performance:** While `zstd` level 3 is good, level 1 might be sufficient for PDFs which are often already compressed, potentially saving CPU cycles if throughput becomes an issue later.

## Questions for Orchestrator
1. None.

## Verdict
[ ] **APPROVED** - Ready for implementation
[x] **REVISE** - Fix Tier 1/2 issues first
[ ] **DISCUSS** - Needs Orchestrator decision