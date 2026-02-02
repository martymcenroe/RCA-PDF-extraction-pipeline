# Issue #27: G-FIAT: Lossless PDF Image Extraction

# G-FIAT: Lossless PDF Image Extraction

## User Story
As a forensic analyst,
I want to extract images from PDFs without any re-encoding,
So that I can analyze original compression artifacts and detect image manipulation.

## Objective
Build a CLI tool that extracts raw image bytes from PDF XObject streams, preserving original formats and generating a structured manifest for forensic analysis.

## UX Flow

### Scenario 1: Successful Extraction (Happy Path)
1. User runs `python -m src.gfiat.extract path/to/document.pdf --output-dir ./output`
2. System parses PDF and identifies all embedded XObject images
3. System extracts raw binary streams without re-encoding
4. System writes images to output directory with original formats preserved
5. System generates `manifest.json` with metadata for each image
6. Result: Exit code 0, user sees summary of extracted images

### Scenario 2: PDF Contains No Images
1. User runs extraction on a text-only PDF
2. System parses PDF and finds zero XObject images
3. System creates empty output directory with `manifest.json` containing empty `images` array
4. Result: Exit code 0, manifest indicates zero images extracted

### Scenario 3: Invalid/Corrupted PDF
1. User runs extraction on malformed PDF file
2. System attempts to parse PDF and encounters error
3. System prints error message to `stderr` containing the specific exception type and file path
4. Result: Exit code 1, no partial output written

### Scenario 4: Output Directory Conflict
1. User runs extraction with existing output directory
2. System detects existing directory
3. If running in interactive terminal (TTY): System prompts user for confirmation
4. If running in non-interactive pipeline without `--force`: System fails immediately with descriptive error to `stderr`
5. If `--force` flag provided: System overwrites existing directory
6. Result: Clear handling of directory conflicts without hanging in automated pipelines

## Requirements

### Extraction Requirements
1. Extract all XObject images from PDF without re-encoding
2. Preserve original image format (JPEG stays JPEG, PNG stays PNG)
3. Access raw binary streams directly via XRef numbers
4. Support common formats: JPEG, PNG, TIFF, JBIG2

### Output Requirements
1. Write extracted images to specified output directory
2. Generate `manifest.json` with complete metadata
3. Use consistent naming scheme: `img_{NNN}.{ext}`
4. Include source PDF path, extraction timestamp, and per-image metadata

### CLI Requirements
1. Accept PDF path as positional argument
2. Accept `--output-dir` for destination (default: `./output`)
3. Accept `--force` flag to overwrite existing output
4. Exit code 0 on success, exit code 1 on failure with descriptive error to `stderr`

### Data Handling Requirements
1. Tool must not transmit any data externally; local filesystem operations only
2. All processing occurs in-memory or on local disk
3. No network access required or permitted

## Technical Approach
- **PDF Parsing:** `pypdf` (BSD-3-Clause) for PDF structure parsing and XObject enumeration
- **Image Extraction:** Direct XObject stream access via `pypdf`'s low-level API to get raw bytes
- **Manifest Generation:** Standard library `json` module for structured output
- **CLI Interface:** `argparse` for argument parsing with clear help text
- **Safety Limits:** 60-second timeout per PDF, 500MB memory limit to prevent resource exhaustion from malformed PDFs

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No - self-contained extraction module
- [ ] **Cost:** No - offline local processing only
- [x] **Legal/PII:** Yes - PDFs may contain PII; all processing is local-only with no data transmission
- [ ] **Safety:** No - read-only operations on input files

## Security Considerations
- **Offline Operation:** No network access required or permitted, mitigating data exfiltration risks
- **Input Validation:** PDF path validated before processing; malformed PDFs handled gracefully
- **No Elevation:** Tool runs with user-level permissions only
- **Memory Safety:** Timeout and memory limits prevent resource exhaustion attacks from crafted PDFs

## Files to Create/Modify
- `src/gfiat/extract.py` â€” Main extraction module with CLI entry point
- `src/gfiat/manifest.py` â€” Manifest generation and JSON schema
- `tests/test_extract.py` â€” Unit tests for extraction functionality
- `tests/fixtures/` â€” Test PDFs (with images, without images, corrupted)

## Dependencies
- `pypdf` (BSD-3-Clause) â€” PDF parsing and XObject access
- `numpy` (BSD-3-Clause) â€” Array operations for image data

### Dev/Test Dependencies
- `opencv-python-headless` (Apache-2.0) â€” Image validation for test verification only

## Out of Scope (Future)
- **Inline image extraction** â€” Deferred to follow-up issue; MVP focuses on XObject images only
- **JBIG2 external decoding** â€” Complex decoder integration deferred
- **Batch processing** â€” Single PDF per invocation for MVP
- **GUI interface** â€” CLI only for MVP

## Acceptance Criteria
- [ ] Extract all XObject images from `docs/context/init/W20552.pdf` without re-encoding
- [ ] Preserve original image format (JPEG stays JPEG, not converted to PNG)
- [ ] Generate `manifest.json` with page/bbox metadata for each image
- [ ] Verify extracted images are byte-identical to PDF XObject streams
- [ ] CLI: `python -m src.gfiat.extract path/to/pdf.pdf --output-dir ./output`
- [ ] On failure, print error message to `stderr` containing specific exception type and file path, then exit with code 1
- [ ] Handle PDF with no images gracefully (empty manifest, exit code 0)
- [ ] Complete extraction within 60-second timeout per PDF
- [ ] Non-interactive mode fails immediately on directory conflict without `--force` (no hanging)

## Definition of Done

### Implementation
- [ ] Core extraction module implemented using `pypdf`
- [ ] Unit tests written and passing
- [ ] Timeout and memory limit protections implemented

### Tools
- [ ] CLI tool functional via `python -m src.gfiat.extract`
- [ ] Help text documents all options (`--help`)

### Documentation
- [ ] Update wiki pages affected by this change
- [ ] Update README.md if user-facing
- [ ] Update relevant ADRs or create new ones
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS (if security-relevant)
- [ ] Run 0810 Privacy Audit - PASS (local-only data handling verified)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- Test with `docs/context/init/W20552.pdf` as primary test case
- Test with PDF containing no images to verify empty manifest generation
- Test with corrupted/malformed PDF to verify error handling
- Test with PDF exceeding timeout to verify resource protection
- Force error states by providing non-existent paths, permission-denied directories
- Test non-interactive mode by piping input or running in CI environment to verify no hanging on directory conflicts

---

**Labels:** `feature`, `core-infrastructure`

**Effort Estimate:** M (Medium) â€” PDF parsing edge cases require careful handling

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-02-01 | **Reviews:** 4</sub>
