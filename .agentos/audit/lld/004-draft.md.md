# 135 - Feature: HTML Forensic Report Generator

<!-- Template Metadata
Last Updated: 2026-02-02
Updated By: Issue #35 LLD Creation
Update Reason: Revision addressing Gemini Review #1 feedback - removed manual tests, added missing test coverage
-->

## 1. Context & Goal
* **Issue:** #35
* **Objective:** Generate standalone, self-contained HTML reports that transform technical forensic analysis outputs into accessible visualizations for non-technical reviewers.
* **Status:** Draft
* **Related Issues:** #4 (Core analysis pipeline - BLOCKING), #117

### Open Questions

- [ ] Should the report include a table of contents with anchor links for longer reports?
- [ ] What is the exact JSON schema version expected from Issue #4's output?
- [ ] Should we support custom CSS injection for organizational branding in a future iteration?

## 2. Proposed Changes

*This section is the **source of truth** for implementation. Describes exactly what will be built.*

### 2.1 Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `gfiat/report/__init__.py` | Add | Report module initialization and public exports |
| `gfiat/report/generator.py` | Add | Main report generation orchestration logic |
| `gfiat/report/schema.py` | Add | JSON schema validation for input analysis data |
| `gfiat/report/templates/report.html.j2` | Add | Jinja2 base template for complete HTML report |
| `gfiat/report/templates/sections/executive_summary.html.j2` | Add | Partial template for executive summary section |
| `gfiat/report/templates/sections/twin_detection.html.j2` | Add | Partial template for twin/clone detection section |
| `gfiat/report/templates/sections/manipulation_detection.html.j2` | Add | Partial template for manipulation detection section |
| `gfiat/report/templates/sections/image_inventory.html.j2` | Add | Partial template for image inventory grid section |
| `gfiat/report/visualizations.py` | Add | Matplotlib rendering for ELA overlays, FFT plots, keypoint matches |
| `gfiat/report/assets.py` | Add | Base64 encoding utilities and CSS/JS bundling |
| `gfiat/__main__.py` | Modify | Add `report` subcommand to CLI |
| `tests/test_report_generator.py` | Add | Unit tests for report generation |
| `tests/test_report_schema.py` | Add | Unit tests for JSON schema validation |
| `tests/test_report_visualizations.py` | Add | Unit tests for visualization generation |
| `tests/test_report_html_validation.py` | Add | HTML structure and standards validation tests |
| `tests/fixtures/sample_analysis_output/` | Add | Test fixtures with valid JSON and dummy images |

### 2.2 Dependencies

*New packages, APIs, or services required.*

```toml
# pyproject.toml additions
jinja2 = "^3.1.2"
jsonschema = "^4.20.0"
html5-parser = "^0.4.12"  # For automated HTML validation
beautifulsoup4 = "^4.12.0"  # For HTML structure assertions
# matplotlib already present for forensic visualizations
# opencv-python already present for image processing
```

### 2.3 Data Structures

```python
# Pseudocode - NOT implementation

class AnalysisInput(TypedDict):
    """Schema for input JSON from Issue #4 analysis pipeline."""
    schema_version: str  # e.g., "1.0.0"
    source_document: DocumentMetadata
    analysis_timestamp: str  # ISO 8601 format
    risk_assessment: RiskLevel  # "Low" | "Medium" | "High" | "Critical"
    images: list[ImageRecord]
    twin_pairs: list[TwinPair]
    manipulation_flags: list[ManipulationFlag]

class DocumentMetadata(TypedDict):
    """Metadata about the analyzed source document."""
    filename: str
    path: str
    page_count: int
    file_size_bytes: int
    author: Optional[str]  # Untrusted - requires sanitization
    keywords: Optional[str]  # Untrusted - requires sanitization

class ImageRecord(TypedDict):
    """Individual extracted image record."""
    id: str
    filename: str
    path: str  # Relative path within analysis output
    page_number: int
    dimensions: tuple[int, int]  # (width, height)
    file_size_bytes: int
    classification: str  # "Photo" | "Chart" | "Diagram" | "Logo" | "Other"
    extraction_timestamp: str

class TwinPair(TypedDict):
    """Detected twin/clone image pair."""
    image_a_id: str
    image_b_id: str
    match_percentage: float  # 0.0 - 100.0
    confidence_score: float  # 0.0 - 1.0
    keypoint_count: int
    keypoint_matches_path: Optional[str]  # Path to pre-rendered match visualization

class ManipulationFlag(TypedDict):
    """Flagged manipulation detection result."""
    image_id: str
    detection_method: str  # "ELA" | "FFT" | "Metadata" | "Combined"
    confidence: float  # 0.0 - 1.0
    ela_overlay_path: Optional[str]
    fft_spectrum_path: Optional[str]
    suspicious_regions: list[BoundingBox]

class BoundingBox(TypedDict):
    """Bounding box for suspicious region."""
    x: int
    y: int
    width: int
    height: int

class ReportConfig(TypedDict):
    """Configuration for report generation."""
    input_dir: Path
    output_path: Path
    lazy_load_threshold: int  # Number of images before enabling lazy load
    max_report_size_mb: int  # Warn if exceeded
    split_sections: bool  # Future: split into multiple files

class RiskLevel(str, Enum):
    """Risk assessment levels from upstream analysis."""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
```

### 2.4 Function Signatures

```python
# gfiat/report/generator.py
def generate_report(
    input_dir: Path,
    output_path: Path,
    config: Optional[ReportConfig] = None
) -> ReportResult:
    """Generate HTML forensic report from analysis output directory."""
    ...

def load_analysis_data(input_dir: Path) -> AnalysisInput:
    """Load and validate analysis JSON from input directory."""
    ...

def validate_analysis_directory(input_dir: Path) -> list[str]:
    """Validate input directory contains required artifacts. Returns list of missing files."""
    ...

# gfiat/report/schema.py
def validate_analysis_json(data: dict) -> ValidationResult:
    """Validate analysis JSON against expected schema version."""
    ...

def get_schema_version(data: dict) -> str:
    """Extract schema version from analysis data."""
    ...

# gfiat/report/visualizations.py
def render_keypoint_matches(
    image_a: np.ndarray,
    image_b: np.ndarray,
    keypoints_a: list[cv2.KeyPoint],
    keypoints_b: list[cv2.KeyPoint],
    matches: list[cv2.DMatch]
) -> bytes:
    """Render side-by-side images with keypoint match lines. Returns PNG bytes."""
    ...

def render_ela_overlay(
    original: np.ndarray,
    ela_map: np.ndarray,
    suspicious_regions: list[BoundingBox]
) -> bytes:
    """Render ELA overlay with highlighted suspicious regions. Returns PNG bytes."""
    ...

def render_fft_spectrum(spectrum_data: np.ndarray) -> bytes:
    """Render FFT spectrum visualization. Returns PNG bytes."""
    ...

# gfiat/report/assets.py
def encode_image_base64(image_path: Path) -> str:
    """Read image file and return base64-encoded data URI."""
    ...

def encode_bytes_base64(data: bytes, mime_type: str) -> str:
    """Encode raw bytes to base64 data URI with specified MIME type."""
    ...

def get_embedded_css() -> str:
    """Return embedded CSS for report styling."""
    ...

def get_embedded_js() -> str:
    """Return embedded JavaScript for report interactivity."""
    ...

def calculate_report_size(html_content: str) -> int:
    """Calculate report size in bytes."""
    ...
```

### 2.5 Logic Flow (Pseudocode)

```
REPORT GENERATION FLOW:
1. Parse CLI arguments (input_dir, output_path)
2. Validate input directory exists
3. Check for required files: analysis.json, images/
4. IF missing files THEN
   - Print error: "Analysis directory missing required files: [list]"
   - Exit with error code 1
5. Load analysis.json
6. Validate JSON against schema
7. IF schema validation fails THEN
   - Print error: "Invalid analysis JSON: [validation error details]"
   - Exit with error code 1
8. Load all referenced images into memory
9. Generate visualizations:
   - FOR each twin pair: render keypoint matches
   - FOR each manipulation flag: render ELA overlay, FFT spectrum
10. Encode all images as base64 data URIs
11. Prepare template context with:
    - Executive summary metrics
    - Twin pairs with visualizations
    - Manipulation flags with visualizations
    - Image inventory with thumbnails
12. Render Jinja2 template with context (autoescaping enabled)
13. Calculate report size
14. IF size > 50MB THEN
    - Print warning: "Report size: {size}MB. Consider using --split-sections"
    - Set exit code to 2 (warning)
15. Write HTML to output_path
16. Print success: "Report generated: {output_path}"
17. Exit with appropriate code (0=success, 2=warning)

TEMPLATE RENDERING FLOW:
1. Initialize Jinja2 environment with autoescape=True
2. Load base template (report.html.j2)
3. Include section partials:
   - executive_summary.html.j2
   - twin_detection.html.j2
   - manipulation_detection.html.j2
   - image_inventory.html.j2
4. Inject embedded CSS and JavaScript
5. Render final HTML string
6. Return rendered content

IMAGE LAZY LOADING FLOW:
1. IF total_images > 100 THEN
   - Enable lazy loading for thumbnails
   - Use loading="lazy" attribute
   - Add placeholder styling
2. ELSE
   - Render all images immediately
```

### 2.6 Technical Approach

* **Module:** `gfiat/report/`
* **Pattern:** Template Method pattern for report sections; Strategy pattern for visualization renderers
* **Key Decisions:**
  - Single self-contained HTML file for portability and evidence integrity
  - Jinja2 for templating with strict autoescaping to prevent XSS
  - Base64 encoding for all embedded assets (no external dependencies)
  - Vanilla JavaScript for interactivity (no framework overhead)
  - Exit code 2 for warnings (file still generated) vs 1 for errors (no file)

### 2.7 Architecture Decisions

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Templating Engine | Jinja2, Mako, string.Template | Jinja2 | Industry standard, excellent autoescape support, partial templates |
| Image Embedding | Base64 inline, external files, zip bundle | Base64 inline | Single-file requirement, offline capability, evidence integrity |
| Visualization Library | Matplotlib, Plotly, D3.js | Matplotlib | Already in project, server-side rendering, no JS dependencies |
| Schema Validation | jsonschema, pydantic, manual | jsonschema | Standard JSON Schema format, clear error messages |
| Keypoint Visualization | OpenCV drawMatches, custom SVG | OpenCV drawMatches | Built-in, handles complex cases, consistent styling |
| Exit Codes | 0/1 binary, 0/1/2 gradated | 0/1/2 gradated | Distinguishes errors (1) from warnings (2) |
| HTML Validation | Manual browser testing, html5-parser | html5-parser | Automated validation in CI, catches structural errors |

**Architectural Constraints:**
- Must integrate with Issue #4's JSON output schema (schema version dependency)
- Cannot introduce external runtime dependencies in generated HTML
- Must maintain evidence chain integrity (self-contained, hash-verifiable)
- All user-derived content must be treated as untrusted (XSS prevention)
- Project uses flat `gfiat/` structure (no `src/` directory)

## 3. Requirements

*What must be true when this is done. These become acceptance criteria.*

1. CLI command `python -m gfiat.report ./analysis_output/ -o report.html` generates valid HTML
2. Report generates valid HTML5 structure (validated by html5-parser, no unclosed tags)
3. Executive summary displays accurate counts matching input JSON
4. Risk assessment value is read directly from upstream JSON (not calculated)
5. Twin pairs render side-by-side with visible keypoint match lines
6. ELA overlays display on manipulation-flagged images
7. FFT spectrum visualizations included for manipulation detection
8. Thumbnail grid shows all extracted images with classification labels
9. Click-to-expand modal structure present in HTML (container elements with event listeners)
10. Generated report is fully self-contained (works offline)
11. Report file size warning at 50MB threshold (still generates with exit code 2)
12. Print CSS rules present (`@media print` blocks validated)
13. Invalid JSON produces clear schema validation error
14. Source files with special characters in filenames render correctly

## 4. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| Single HTML file with base64 | Portable, self-contained, evidence-grade | Larger file size, no caching | **Selected** |
| HTML + external assets folder | Smaller HTML, cacheable images | Not self-contained, can become separated | Rejected |
| PDF generation | Native print, widely accepted | Complex to generate, less interactive | Rejected |
| Web app with backend | Dynamic filtering, advanced features | Requires deployment, not offline | Rejected |
| React/Vue SPA bundled | Rich interactivity | Large bundle, unnecessary complexity | Rejected |

**Rationale:** The single self-contained HTML approach best meets the evidence chain integrity requirement while supporting non-technical users who may open the file on air-gapped systems or via email attachment.

## 5. Data & Fixtures

*Per [0108-lld-pre-implementation-review.md](0108-lld-pre-implementation-review.md) - complete this section BEFORE implementation.*

### 5.1 Data Sources

| Attribute | Value |
|-----------|-------|
| Source | Issue #4 analysis pipeline output (`./analysis_output/`) |
| Format | JSON + PNG/JPEG images |
| Size | Typically 10-200 images, 50-500MB analysis output |
| Refresh | Manual (per analysis run) |
| Copyright/License | Derived from source documents; inherits source classification |

### 5.2 Data Pipeline

```
Issue #4 Analysis ──writes──► analysis_output/ ──reads──► Report Generator ──writes──► report.html
       │                              │
       └── analysis.json              └── images/*.{png,jpg}
```

### 5.3 Test Fixtures

| Fixture | Source | Notes |
|---------|--------|-------|
| `tests/fixtures/sample_analysis_output/analysis.json` | Generated | Valid schema v1.0.0 with all field types |
| `tests/fixtures/sample_analysis_output/images/` | Generated | 10 sample images (various types) |
| `tests/fixtures/sample_analysis_output/minimal.json` | Generated | Minimal valid JSON (0 images, no flags) |
| `tests/fixtures/sample_analysis_output/malformed.json` | Generated | Invalid JSON for error testing |
| `tests/fixtures/sample_analysis_output/large/` | Generated | 150 images for lazy-load testing |
| `tests/fixtures/sample_analysis_output/special_chars/` | Generated | Filenames with spaces, emoji, unicode |
| `tests/fixtures/sample_analysis_output/count_verification.json` | Generated | Known counts for summary verification |

### 5.4 Deployment Pipeline

Test fixtures are committed to repository. No external data sources required.

Development → CI Tests → PR Review → Merge

**If data source is external:** N/A - all fixtures are generated and committed.

## 6. Diagram

### 6.1 Mermaid Quality Gate

Before finalizing any diagram, verify in [Mermaid Live Editor](https://mermaid.live) or GitHub preview:

- [x] **Simplicity:** Similar components collapsed (per 0006 §8.1)
- [x] **No touching:** All elements have visual separation (per 0006 §8.2)
- [x] **No hidden lines:** All arrows fully visible (per 0006 §8.3)
- [x] **Readable:** Labels not truncated, flow direction clear
- [ ] **Auto-inspected:** Agent rendered via mermaid.ink and viewed (per 0006 §8.5)

**Agent Auto-Inspection (MANDATORY):**

**Auto-Inspection Results:**
```
- Touching elements: [ ] None / [ ] Found: ___
- Hidden lines: [ ] None / [ ] Found: ___
- Label readability: [ ] Pass / [ ] Issue: ___
- Flow clarity: [ ] Clear / [ ] Issue: ___
```

*Note: Auto-inspection to be completed during implementation phase.*

### 6.2 Diagram

```mermaid
flowchart TB
    subgraph Input["Analysis Output Directory"]
        JSON["analysis.json"]
        IMGS["images/*.png"]
        ELA["ela_overlays/"]
        FFT["fft_spectra/"]
    end

    subgraph Generator["Report Generator Module"]
        VAL["Schema Validator"]
        LOAD["Data Loader"]
        VIZ["Visualization Renderer"]
        TMPL["Jinja2 Templater"]
        ENC["Base64 Encoder"]
    end

    subgraph Templates["HTML Templates"]
        BASE["report.html.j2"]
        EXEC["executive_summary.j2"]
        TWIN["twin_detection.j2"]
        MANIP["manipulation_detection.j2"]
        INV["image_inventory.j2"]
    end

    subgraph Output["Generated Report"]
        HTML["report.html"]
    end

    JSON --> VAL
    VAL --> LOAD
    IMGS --> LOAD
    ELA --> LOAD
    FFT --> LOAD
    LOAD --> VIZ
    VIZ --> ENC
    ENC --> TMPL
    BASE --> TMPL
    EXEC --> TMPL
    TWIN --> TMPL
    MANIP --> TMPL
    INV --> TMPL
    TMPL --> HTML
```

## 7. Security & Safety Considerations

### 7.1 Security

| Concern | Mitigation | Status |
|---------|------------|--------|
| Stored XSS via PDF metadata | Jinja2 autoescaping mandatory; never disable for user content | Addressed |
| Path traversal in filenames | Validate all paths are within analysis directory | Addressed |
| Malicious image content | Base64 encoding preserves content; browser sandboxing handles display | Addressed |
| JavaScript injection | No user content executed as JavaScript; minimal vanilla JS only | Addressed |
| Report tampering | SHA-256 hash embedded in report footer for integrity verification | Addressed |

### 7.2 Safety

| Concern | Mitigation | Status |
|---------|------------|--------|
| Missing input files | Validate all required artifacts before processing | Addressed |
| Malformed JSON | Schema validation with clear error messages | Addressed |
| Memory exhaustion (large images) | Lazy loading for 100+ images; warn at 50MB | Addressed |
| Partial write on failure | Write to temp file, atomic rename on success | Addressed |
| Missing risk_assessment field | Default to "Unknown" with warning in report | Addressed |

**Fail Mode:** Fail Closed - Report not generated on validation errors (exit code 1)

**Recovery Strategy:** Clear error messages guide user to fix input. Partial failures prevented by atomic write.

## 8. Performance & Cost Considerations

### 8.1 Performance

| Metric | Budget | Approach |
|--------|--------|----------|
| Report generation time | < 30 seconds for 100 images | Parallel image encoding, lazy render |
| Memory usage | < 2GB peak | Stream large images, garbage collect |
| Report load time | < 3 seconds in browser | Lazy loading for thumbnails, minimal JS |
| Print render time | < 10 seconds | Print-specific CSS, reduced resolution |

**Bottlenecks:**
- Base64 encoding increases data size by ~33%
- Large analysis directories (200+ images) may exceed 50MB threshold
- Matplotlib rendering is CPU-intensive for many visualizations

### 8.2 Cost Analysis

| Resource | Unit Cost | Estimated Usage | Monthly Cost |
|----------|-----------|-----------------|--------------|
| CPU time | N/A (local) | 30s per report | $0 |
| Storage | N/A (local) | 10-100MB per report | $0 |
| No external APIs | $0 | N/A | $0 |

**Cost Controls:**
- [x] No external API calls - fully offline generation
- [x] No cloud resources required
- [ ] N/A - no cost concerns for local CLI tool

**Worst-Case Scenario:** User analyzes 1000+ images - generation may take several minutes and produce 500MB+ file. Mitigation: `--split-sections` flag (future).

## 9. Legal & Compliance

| Concern | Applies? | Mitigation |
|---------|----------|------------|
| PII/Personal Data | Yes | Report inherits classification of source; no additional PII collected |
| Third-Party Licenses | Yes | Jinja2 (BSD), jsonschema (MIT), html5-parser (Apache-2.0), beautifulsoup4 (MIT) - compatible with project |
| Terms of Service | N/A | No external services used |
| Data Retention | Yes | Report is user-controlled output; no automatic retention |
| Export Controls | N/A | No restricted algorithms or data |

**Data Classification:** Inherits source document classification (typically Confidential for forensic evidence)

**Compliance Checklist:**
- [x] No PII stored without consent (user controls source documents)
- [x] All third-party licenses compatible with project license
- [x] No external API usage
- [x] Data retention is user-controlled (local file output)

## 10. Verification & Testing

*Ref: [0005-testing-strategy-and-protocols.md](0005-testing-strategy-and-protocols.md)*

**Testing Philosophy:** 100% automated test coverage. All scenarios are automated using HTML parsing and structural validation. No manual browser testing required for acceptance criteria.

### 10.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Generate report from valid analysis | Auto | Valid fixtures | report.html created | File exists, valid HTML |
| 020 | Missing analysis directory | Auto | Non-existent path | Error message | Exit 1, lists missing files |
| 030 | Missing required JSON | Auto | Dir without analysis.json | Error message | Exit 1, mentions JSON |
| 040 | Invalid JSON schema | Auto | Malformed JSON fixture | Schema error | Exit 1, validation details |
| 050 | Empty analysis (no images) | Auto | Minimal valid JSON | Report with "no issues" | Valid HTML, 0 counts displayed |
| 055 | Executive summary count accuracy | Auto | count_verification.json fixture | Counts match input | Parse HTML, assert "10 Images Analyzed" matches JSON |
| 060 | Twin pairs rendering | Auto | Fixtures with twin data | Pairs in HTML | Contains side-by-side image containers |
| 070 | Manipulation flags rendering | Auto | Fixtures with flags | Flags in HTML | Contains ELA overlay elements |
| 080 | Image inventory grid | Auto | 10 images | Thumbnail grid | All 10 image elements present with unique IDs |
| 085 | Modal structure validation | Auto | Generated report | Modal containers | HTML contains modal div, close button, event listener script |
| 090 | Large analysis (150 images) | Auto | Large fixtures | Report + warning | Exit 2, lazy loading attribute present |
| 100 | 50MB threshold warning | Auto | Fixtures exceeding 50MB | Warning message | Exit 2, report still created |
| 110 | Special character filenames | Auto | Unicode/emoji filenames | Correct rendering | Filenames display correctly in parsed HTML |
| 120 | Risk assessment display | Auto | JSON with risk field | Risk shown in summary | Correct value from JSON in HTML |
| 130 | Missing risk_assessment | Auto | JSON without risk field | "Unknown" default | Warning, still generates |
| 140 | Print CSS validation | Auto | Generated report | Valid print styles | @media print blocks present in CSS |
| 145 | HTML5 standards compliance | Auto | Generated report | Valid HTML5 | html5-parser validates without errors |
| 150 | No external requests | Auto | Generated report | Self-contained | No http:// or https:// URLs in HTML |
| 160 | XSS prevention (metadata) | Auto | Malicious PDF author name | Escaped in HTML | Script tags escaped, no raw injection |

### 10.2 Test Commands

```bash
# Run all automated tests
poetry run pytest tests/test_report_*.py -v

# Run only fast/mocked tests (exclude large fixtures)
poetry run pytest tests/test_report_*.py -v -m "not slow"

# Run with coverage
poetry run pytest tests/test_report_*.py -v --cov=gfiat/report

# Run HTML validation tests specifically
poetry run pytest tests/test_report_html_validation.py -v

# Generate sample report for exploratory testing
python -m gfiat.report tests/fixtures/sample_analysis_output/ -o /tmp/test_report.html
```

### 10.3 Manual Tests (Only If Unavoidable)

N/A - All scenarios automated.

**Exploratory Testing Notes (Non-Blocking):**
For additional confidence, developers may optionally open generated reports in Chrome, Firefox, Safari, and Edge to visually verify rendering. These are not acceptance criteria and do not block merge. Any issues discovered should be converted to automated regression tests.

## 11. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Issue #4 schema changes after implementation | High | Medium | Lock schema version; versioned validation |
| Base64 bloat makes reports unusable | Medium | Low | Lazy loading, size warnings, future split-sections |
| Browser compatibility issues | Medium | Low | HTML5 standard compliance validated by html5-parser |
| Jinja2 autoescape bypass | High | Low | Code review; never use `|safe` on user content |
| Performance issues with large analyses | Medium | Medium | Benchmarking; lazy loading; progress indicators |
| Project structure mismatch | Medium | Low | Confirmed: project uses `gfiat/` not `src/gfiat/` |

## 12. Definition of Done

### Code
- [ ] Implementation complete and linted
- [ ] Code comments reference this LLD
- [ ] All functions have docstrings
- [ ] Type hints on all public functions
- [ ] SHA-256 integrity hash implemented in report footer

### Tests
- [ ] All 18 automated test scenarios pass
- [ ] Test coverage > 90% for report module
- [ ] HTML5 validation passes for all generated reports

### Documentation
- [ ] LLD updated with any deviations
- [ ] Implementation Report (0103) completed
- [ ] Test Report (0113) completed
- [ ] CLI help text accurate and helpful

### Review
- [ ] Code review completed
- [ ] User approval before closing issue

---

## Appendix: Review Log

*Track all review feedback with timestamps and implementation status.*

### Gemini Review #1 (REVISE)

**Timestamp:** 2026-02-02
**Reviewer:** Gemini 3 Pro
**Verdict:** REVISE

#### Comments

| ID | Comment | Implemented? |
|----|---------|--------------|
| G1.1 | "Path Structure Verification: Confirm project uses `src/` layout" | YES - Updated all paths to `gfiat/` (no src/) |
| G1.2 | "No Human Delegation: Remove Section 10.3 manual tests" | YES - Removed manual tests, moved to exploratory notes |
| G1.3 | "Requirement Coverage at 71.4%, must be ≥95%" | YES - Added tests 055, 085, 145 for gaps |
| G1.4 | "Browser Render (Req 2): Add HTML validator" | YES - Added html5-parser dependency and test 145 |
| G1.5 | "Summary Counts (Req 3): Add count accuracy test" | YES - Added test 055 with count_verification.json fixture |
| G1.6 | "Modals (Req 9): Add modal structure test" | YES - Added test 085 for modal DOM inspection |
| G1.7 | "Integrity Hash: Consider moving SHA-256 to v1" | YES - Moved from TODO to Addressed in Security section |
| G1.8 | "HTML Validation: Include html5validator dependency" | YES - Added html5-parser and beautifulsoup4 |

### Review Summary

| Review | Date | Verdict | Key Issue |
|--------|------|---------|-----------|
| Gemini #1 | 2026-02-02 | REVISE | Manual tests violate protocol; coverage at 71.4% |

**Final Status:** PENDING
<!-- Note: This field is auto-updated to APPROVED by the workflow when finalized -->