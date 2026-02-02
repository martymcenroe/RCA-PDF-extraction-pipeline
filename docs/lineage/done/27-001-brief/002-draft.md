# G-FIAT: Lossless PDF Image Extraction

## User Story
As a forensic analyst,
I want to extract images from PDFs without any re-encoding,
So that I can analyze original compression artifacts and detect image manipulation.

## Objective
Build a lossless image extraction module that bypasses PDF rendering to access raw XObject binary streams, preserving original forensic evidence.

## UX Flow

### Scenario 1: Extract Images from PDF (Happy Path)
1. User runs `python -m src.gfiat.extract docs/context/init/W20552.pdf --output-dir ./output`
2. System extracts all embedded images as raw binary streams
3. System writes images to `./output/` preserving original format (JPEG→.jpg, PNG→.png)
4. System generates `./output/manifest.json` with metadata for each image
5. Result: User has forensically-intact images ready for analysis

### Scenario 2: PDF with No Images
1. User runs extraction on a text-only PDF
2. System detects no embedded XObject images
3. System creates empty manifest with `"images": []`
4. Result: User receives clear feedback that no images were found

### Scenario 3: Corrupted or Password-Protected PDF
1. User runs extraction on inaccessible PDF
2. System fails to open document
3. System exits with descriptive error message and non-zero exit code
4. Result: User understands why extraction failed

### Scenario 4: Mixed Image Formats
1. User extracts from PDF containing JPEG, PNG, and JBIG2 images
2. System extracts each in its native format
3. System flags JBIG2 images in manifest if external decoder needed
4. Result: User gets all extractable images with format-specific notes

## Requirements

### Extraction Requirements
1. Extract images using PyMuPDF's `extract_image(xref)` to get raw bytes
2. Preserve original compression (no transcoding JPEG→PNG or vice versa)
3. Handle all standard PDF image formats: JPEG, PNG, TIFF, JPEG2000
4. Flag JBIG2 images that may require external decoding

### Manifest Requirements
1. Generate `manifest.json` in output directory
2. Include source PDF path, extraction timestamp (ISO8601)
3. For each image: ID, page number, bounding box, format, filename, XRef number
4. Include extraction statistics (total images, by-format counts)

### CLI Requirements
1. Accept PDF path as positional argument
2. Accept `--output-dir` flag (default: `./extracted_images`)
3. Accept `--verify` flag to validate byte-identity with source streams
4. Return exit code 0 on success, non-zero on failure

## Technical Approach
- **PyMuPDF XObject Access:** Use `page.get_images()` to enumerate XRefs, then `doc.extract_image(xref)` for raw bytes
- **Format Detection:** Read format from PyMuPDF's extraction metadata, not file extension guessing
- **Bounding Box Mapping:** Use `page.get_image_rects(xref)` to get page coordinates
- **Verification Mode:** Compare extracted bytes against `doc.xref_stream(xref)` for integrity check

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No—self-contained extraction module
- [ ] **Cost:** No—local processing only, no API calls
- [ ] **Legal/PII:** Yes—extracted images may contain PII from source documents; output directory should be treated as sensitive
- [ ] **Safety:** No—read-only operation on source PDFs

## Security Considerations
- Source PDFs are read-only; no modification risk
- Output directory permissions inherit from parent; user responsible for securing extracted content
- No network access required; fully offline operation
- Malformed PDFs may cause PyMuPDF exceptions; wrapped with try/catch for graceful failure

## Files to Create/Modify
- `src/gfiat/__init__.py` — Package init
- `src/gfiat/extract.py` — Core extraction logic and CLI entry point
- `src/gfiat/manifest.py` — Manifest generation and schema
- `tests/test_extract.py` — Unit tests for extraction
- `tests/test_manifest.py` — Unit tests for manifest generation
- `pyproject.toml` — Add new dependencies to Poetry

## Dependencies
- None—this is foundational infrastructure for G-FIAT

## Out of Scope (Future)
- **Inline image extraction** — PDF inline images require different parsing; deferred
- **Image analysis/forensics** — This issue is extraction only; analysis is separate
- **Batch processing** — Single PDF per invocation for MVP
- **GUI interface** — CLI only for now

## Acceptance Criteria
- [ ] Extract all images from `docs/context/init/W20552.pdf` without re-encoding
- [ ] Preserve original image format (JPEG stays JPEG, not converted to PNG)
- [ ] Generate `manifest.json` with page/bbox metadata for each image
- [ ] Verify extracted images are byte-identical to PDF XObject streams (via `--verify`)
- [ ] CLI runs successfully: `python -m src.gfiat.extract path/to/pdf.pdf --output-dir ./output`
- [ ] Exit code 0 on success, non-zero on failure with descriptive error

## Definition of Done

### Implementation
- [ ] Core extraction module implemented in `src/gfiat/extract.py`
- [ ] Manifest generation in `src/gfiat/manifest.py`
- [ ] Unit tests written and passing

### Tools
- [ ] CLI entry point functional via `python -m src.gfiat.extract`
- [ ] Help text documents all flags (`--help`)

### Documentation
- [ ] Update README.md with G-FIAT extraction usage
- [ ] Document manifest.json schema
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0810 Privacy Audit - PASS (extracted images may contain PII)

## Testing Notes
- Use `docs/context/init/W20552.pdf` as primary test fixture
- To test error handling: pass non-existent path, password-protected PDF, or non-PDF file
- Verify byte-identity by comparing SHA256 of extracted file vs `doc.xref_stream(xref)`
- Test with PDFs containing multiple image formats if available