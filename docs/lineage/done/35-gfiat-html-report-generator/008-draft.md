# HTML Forensic Report Generator

## User Story
As a **non-technical reviewer** (auditor, legal counsel, compliance officer),
I want **forensic analysis results presented in a clear, visual HTML report**,
So that **I can understand and act on findings without interpreting raw technical data**.

## Objective
Generate standalone HTML reports that transform technical forensic outputs (match scores, ELA maps, FFT spectra) into accessible visualizations supporting human decision-making.

## UX Flow

### Scenario 1: Generate Report from Analysis Output
1. User runs forensic analysis on a PDF, producing output in `./analysis_output/`
2. User executes `python -m src.gfiat.report ./analysis_output/ -o report.html`
3. System reads all analysis artifacts (JSON results, images, metadata)
4. System generates self-contained HTML with embedded visualizations
5. Result: Single `report.html` file ready to open in any modern browser

### Scenario 2: Analysis Directory Missing or Invalid
1. User runs `python -m src.gfiat.report ./nonexistent/ -o report.html`
2. System checks for required analysis artifacts
3. System displays error: "Analysis directory missing required files: [list]"
4. Result: No report generated, clear guidance on what's missing

### Scenario 3: Large Analysis with Many Images
1. User runs report generation on analysis with 200+ images
2. System generates report with lazy-loaded thumbnails
3. System warns if report exceeds 50MB: "Report size: 67MB. Consider using --split-sections"
4. System exits with warning (non-zero exit code) but still generates the report
5. Result: Report generated with performance optimization applied

### Scenario 4: Opening Report in Browser
1. User double-clicks `report.html` or opens in browser
2. Report loads with executive summary visible
3. User scrolls through sections: Summary → Twin Detection → Manipulation → Inventory
4. User clicks thumbnail to expand full image with details
5. Result: Interactive exploration of forensic findings

## Requirements

### Report Structure
1. Executive Summary section at top with key metrics
2. Twin/Clone Detection section with paired image comparisons
3. Manipulation Detection section with ELA overlays and FFT spectra
4. Image Inventory section with filterable thumbnail grid
5. Navigation sidebar or header for section jumping

### Executive Summary
1. Display total images analyzed count
2. Show flagged issues grouped by category (twins, manipulation, metadata anomalies)
3. Present overall risk assessment (Low/Medium/High/Critical)
4. Include timestamp of analysis and source document metadata

### Twin/Clone Detection Display
1. Render image pairs side-by-side
2. Draw keypoint matches as connecting lines between images
3. Display match percentage and confidence score
4. Sort by confidence (highest first)

### Manipulation Detection Display
1. Show original image alongside ELA overlay
2. Highlight suspicious regions with bounding boxes or heat overlay
3. Include FFT spectrum visualization
4. Display manipulation confidence and detection method used

### Image Inventory
1. Render thumbnail grid of all extracted images
2. Show classification label on each thumbnail
3. Support click-to-expand for full image and metadata
4. Include basic filtering by classification

### Technical Requirements
1. Self-contained single HTML file (no external dependencies)
2. Base64-encode all images inline
3. Report file size under 50MB for typical analysis (< 100 images)
4. Report renders without console errors or horizontal scroll breakage in Chrome, Firefox, Safari, Edge (last 2 major versions)
5. Print preview fits content to page width and does not break images across page boundaries

## Technical Approach
- **Templating:** Jinja2 templates for HTML structure and content injection. Strict context-aware output encoding (autoescaping) must be enforced in Jinja2. All metadata fields derived from source documents must be treated as untrusted input.
- **Visualizations:** Matplotlib generates comparison images, ELA overlays, FFT plots; saved as base64 PNG
- **Keypoint Matching Lines:** OpenCV `drawMatches` or custom SVG overlay on paired images
- **Styling:** Embedded CSS with professional report aesthetic; print media queries
- **Interactivity:** Vanilla JavaScript for thumbnail expansion, section navigation, lazy loading
- **CLI:** Click-based command accepting input directory and output path

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No significant system structure changes; adds new report module
- [x] **Cost:** Base64 encoding increases file size ~33%; mitigated with lazy loading for large reports
- [ ] **Legal/PII:** Report contains images from source documents; same sensitivity as source material
- [ ] **Safety:** No data modification; read-only report generation

## Security Considerations
- Reports contain forensic evidence and should inherit classification of source documents
- No external network requests from generated HTML (fully offline-capable)
- **Input Sanitization:** All metadata fields (PDF Author, Keywords, Filenames) derived from source documents are treated as untrusted input. Jinja2 autoescaping is mandatory and must not be disabled for any user-derived content. This mitigates Stored XSS attack vectors.
- JavaScript is minimal and doesn't execute user-provided content
- Consider adding report integrity hash for evidence chain purposes

## Files to Create/Modify
- `src/gfiat/report/__init__.py` — Report module initialization
- `src/gfiat/report/generator.py` — Main report generation logic
- `src/gfiat/report/templates/report.html.j2` — Jinja2 base template
- `src/gfiat/report/templates/sections/` — Partial templates for each section
- `src/gfiat/report/visualizations.py` — Matplotlib rendering for overlays and comparisons
- `src/gfiat/report/assets.py` — Base64 encoding utilities and CSS/JS bundling
- `src/gfiat/__main__.py` — Add `report` subcommand to CLI
- `tests/test_report_generator.py` — Unit tests for report generation
- `tests/fixtures/sample_analysis_output/` — Test fixtures containing valid JSON and dummy images to enable development/testing without running heavy analysis pipeline

## Dependencies
- **Blocked by:** Issue #4 (Core analysis pipeline) must be complete and in "Done" state — produces JSON + images for report consumption
- Jinja2 library (add to requirements.txt if not present)
- Matplotlib already in use for forensic visualizations

## Out of Scope (Future)
- **Interactive zoom/pan on images** — deferred; basic click-to-expand is MVP
- **Report comparison (diff two reports)** — future enhancement for tracking changes
- **Export to PDF directly** — browser print-to-PDF is sufficient for MVP
- **Multi-language/i18n support** — English only initially
- **Custom branding/logo injection** — future configuration option
- **`--open` flag to auto-open report in browser** — future CLI enhancement

## Acceptance Criteria
- [ ] CLI command `python -m src.gfiat.report ./analysis_output/ -o report.html` generates valid HTML
- [ ] Report renders without console errors or horizontal scroll breakage in Chrome, Firefox, Safari, Edge (last 2 major versions)
- [ ] Executive summary displays accurate counts matching analysis JSON
- [ ] Twin pairs render side-by-side with visible keypoint match lines
- [ ] ELA overlays display on manipulation-flagged images
- [ ] Thumbnail grid shows all extracted images with classification labels
- [ ] Clicking thumbnail expands to full image with metadata
- [ ] Generated report is self-contained (works offline, no external requests)
- [ ] Report file size < 50MB for analysis with 50 images; system warns (non-zero exit) if exceeded but still generates report
- [ ] Print preview fits content to page width and does not break images across page boundaries

## Definition of Done

### Implementation
- [ ] Core feature implemented
- [ ] Unit tests written and passing

### Tools
- [ ] Update/create relevant CLI tools in `tools/` (if applicable)
- [ ] Document tool usage

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
- [ ] Run 0810 Privacy Audit - PASS (if privacy-relevant)
- [ ] Run 0817 Wiki Alignment Audit - PASS (if wiki updated)

## Testing Notes
- Test with empty analysis directory (should error gracefully)
- Test with analysis containing 0 flagged items (report should still generate with "no issues found")
- Test with 100+ images to verify lazy loading activates and file size warning appears
- Test print preview in each browser for layout issues
- Verify report works when opened from `file://` protocol (no CORS issues)
- Check that all images render (no broken base64)
- Test fixtures in `tests/fixtures/sample_analysis_output/` must be used for unit tests

## Labels
`feature`, `reporting`, `mvp`, `frontend`

## Effort Estimate
**Size: L** (approx 5-8 story points) — Multiple visualization types and templates required

## Original Brief
# G-FIAT: HTML Forensic Report Generator

## Problem

Forensic analysis produces technical outputs (match scores, ELA maps, FFT spectra) that are meaningless to non-technical users like auditors or legal reviewers. We need to present evidence in a clear, visual format that supports human decision-making.

## Proposed Solution

Generate standalone HTML reports with interactive visualizations of forensic findings.

### Report Sections

1. **Executive Summary**
   - Total images analyzed
   - Flagged issues count by category
   - Overall risk assessment

2. **Twin/Clone Detection Results**
   - Side-by-side image pairs
   - Keypoint matches drawn as connecting lines
   - Match percentage and confidence

3. **Manipulation Detection Results**
   - Original image with ELA overlay
   - Highlighted suspicious regions
   - FFT spectrum visualization

4. **Image Inventory**
   - Thumbnail grid of all extracted images
   - Classification labels
   - Click to expand details

### Technical Approach
- Jinja2 templates for HTML generation
- Matplotlib for visualizations (saved as embedded base64)
- Self-contained single HTML file (no external dependencies)
- Optional: interactive zoom with JavaScript

## Acceptance Criteria

- [ ] Generate self-contained HTML report
- [ ] Display twin pairs with visual matching lines
- [ ] Display ELA overlays on flagged images
- [ ] Include executive summary with counts
- [ ] Render correctly in modern browsers
- [ ] Report size < 50MB for typical analysis
- [ ] CLI: `python -m src.gfiat.report ./analysis_output/ -o report.html`

## Technical Considerations

- Base64 encoding images increases file size ~33%
- Consider lazy loading for reports with many images
- Add print-friendly CSS for PDF export
- Include timestamp and source PDF metadata
- Version the report format for reproducibility