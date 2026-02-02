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
4. Result: Report generated with performance optimization applied

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
4. Render correctly in Chrome, Firefox, Safari, Edge (latest versions)
5. Print-friendly CSS for PDF export via browser

## Technical Approach
- **Templating:** Jinja2 templates for HTML structure and content injection
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
- JavaScript is minimal and doesn't execute user-provided content (no XSS vectors)
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

## Dependencies
- Core analysis pipeline must be complete (produces JSON + images for report consumption)
- Jinja2 library (add to requirements.txt if not present)
- Matplotlib already in use for forensic visualizations

## Out of Scope (Future)
- **Interactive zoom/pan on images** — deferred; basic click-to-expand is MVP
- **Report comparison (diff two reports)** — future enhancement for tracking changes
- **Export to PDF directly** — browser print-to-PDF is sufficient for MVP
- **Multi-language/i18n support** — English only initially
- **Custom branding/logo injection** — future configuration option

## Acceptance Criteria
- [ ] CLI command `python -m src.gfiat.report ./analysis_output/ -o report.html` generates valid HTML
- [ ] Report opens and renders correctly in Chrome, Firefox, Safari, Edge
- [ ] Executive summary displays accurate counts matching analysis JSON
- [ ] Twin pairs render side-by-side with visible keypoint match lines
- [ ] ELA overlays display on manipulation-flagged images
- [ ] Thumbnail grid shows all extracted images with classification labels
- [ ] Clicking thumbnail expands to full image with metadata
- [ ] Generated report is self-contained (works offline, no external requests)
- [ ] Report file size < 50MB for analysis with 50 images
- [ ] Print preview shows readable, properly paginated output

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