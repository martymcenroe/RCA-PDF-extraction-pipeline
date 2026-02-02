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
