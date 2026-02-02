# 131 - Feature: Error Level Analysis (ELA) for Image Manipulation Detection

<!-- Template Metadata
Last Updated: 2026-02-02
Updated By: Issue #31 implementation
Update Reason: Initial LLD creation for ELA analysis feature
-->

## 1. Context & Goal
* **Issue:** #31
* **Objective:** Implement Error Level Analysis (ELA) to detect image manipulation by comparing JPEG compression artifacts across image regions, flagging areas with anomalous error distributions that indicate potential tampering.
* **Status:** Draft
* **Related Issues:** None

### Open Questions

- [x] Should ELA overlay images be JPEG or PNG format? **Answer: JPEG with `_ela.jpg` suffix per issue spec**
- [x] What is the default timeout for per-image processing? **Answer: 60 seconds per issue spec**
- [ ] Should we support parallel processing configuration (thread count)?

## 2. Proposed Changes

*This section is the **source of truth** for implementation. Describe exactly what will be built.*

### 2.1 Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `src/gfiat/analyzers/ela.py` | Add | Core ELA analysis implementation |
| `src/gfiat/analyzers/__init__.py` | Modify | Export ELA analyzer classes |
| `src/gfiat/cli/analyze.py` | Modify | Add `ela` subcommand to CLI |
| `src/gfiat/models/ela_report.py` | Add | Data classes for ELA results |
| `tests/test_ela.py` | Add | Unit tests for ELA analysis |
| `tests/fixtures/ela/` | Add | Test images directory |
| `tests/fixtures/ela/fixture_metadata.json` | Add | Ground truth for automated verification |
| `docs/0003-file-inventory.md` | Modify | Add new files to inventory |

### 2.2 Dependencies

```toml
# pyproject.toml additions (if any)
# opencv-python and numpy are expected to already be installed
opencv-python = "^4.8.0"  # Already present - verify
numpy = "^1.24.0"  # Already present - verify
```

### 2.3 Data Structures

```python
# Pseudocode - NOT implementation
class BoundingBox(TypedDict):
    x: int  # Top-left x coordinate
    y: int  # Top-left y coordinate
    width: int  # Box width in pixels
    height: int  # Box height in pixels
    error_level: float  # Mean error level in this region

class ELAImageResult(TypedDict):
    image_path: str  # Path to analyzed image
    ela_overlay_path: str  # Path to generated ELA overlay
    mean_error: float  # Mean error level across image (0-255)
    max_error: float  # Maximum error level (0-255)
    std_dev: float  # Standard deviation of error levels
    likelihood_score: float  # Manipulation likelihood (0.0-1.0)
    anomalous_regions: list[BoundingBox]  # Regions exceeding threshold
    notes: list[str]  # Warnings like "high-detail area"

class ELAReport(TypedDict):
    analysis_timestamp: str  # ISO format timestamp
    input_path: str  # Input file or directory
    output_path: str  # Output directory
    parameters: ELAParameters  # Analysis parameters used
    results: list[ELAImageResult]  # Per-image results
    skipped_files: list[SkippedFile]  # Non-JPEG, symlinks, errors
    summary: ELASummary  # Aggregate statistics

class ELAParameters(TypedDict):
    quality: int  # JPEG compression quality (default: 90)
    scale: int  # Visibility multiplier (default: 15)
    threshold: float  # Detection sensitivity (default: 0.5)
    timeout: int  # Per-image timeout in seconds (default: 60)

class SkippedFile(TypedDict):
    path: str  # File path
    reason: str  # Why skipped (non-JPEG, symlink, timeout, error)

class ELASummary(TypedDict):
    total_images: int  # Total JPEG images processed
    flagged_count: int  # Images with likelihood > threshold
    skipped_count: int  # Files skipped
    processing_time_seconds: float  # Total processing time
```

### 2.4 Function Signatures

```python
# src/gfiat/analyzers/ela.py

def analyze_image(
    image_path: Path,
    quality: int = 90,
    scale: int = 15,
    threshold: float = 0.5,
) -> ELAImageResult:
    """Perform ELA analysis on a single JPEG image."""
    ...

def generate_ela_map(
    original: np.ndarray,
    recompressed: np.ndarray,
    scale: int = 15,
) -> np.ndarray:
    """Calculate scaled pixel-wise difference between original and recompressed."""
    ...

def calculate_likelihood_score(
    error_map: np.ndarray,
) -> tuple[float, dict]:
    """
    Calculate manipulation likelihood using heuristic formula.
    Returns (score, metrics_dict).
    """
    ...

def detect_anomalous_regions(
    error_map: np.ndarray,
    threshold_multiplier: float = 2.0,
) -> list[BoundingBox]:
    """Identify regions with anomalous error levels using connected components."""
    ...

def analyze_directory(
    input_path: Path,
    output_path: Path,
    quality: int = 90,
    scale: int = 15,
    threshold: float = 0.5,
    timeout: int = 60,
) -> ELAReport:
    """Analyze all JPEG images in directory with parallel processing."""
    ...

# src/gfiat/cli/analyze.py

def ela_command(
    input_path: str,
    output: str = "./ela_output/",
    quality: int = 90,
    scale: int = 15,
    threshold: float = 0.5,
    timeout: int = 60,
) -> None:
    """CLI handler for ELA analysis subcommand."""
    ...
```

### 2.5 Logic Flow (Pseudocode)

```
ELA Single Image Analysis:
1. Validate input is JPEG format
2. Read original image with OpenCV
3. Create temporary file for recompressed image
4. TRY:
   - Compress image to temp file at specified quality
   - Read recompressed image
   - Calculate pixel-wise absolute difference
   - Scale difference values for visibility
   - Calculate statistics (mean, max, std_dev)
   - Detect anomalous regions via connected components
   - Calculate likelihood score using formula
   - Save ELA overlay to output path
   - Return ELAImageResult
5. FINALLY:
   - Delete temporary file (guaranteed cleanup)

ELA Directory Analysis:
1. Validate input path exists
2. Create output directory if needed
3. Scan directory recursively for files
4. FOR each file:
   - IF symlink THEN skip with warning
   - IF not JPEG THEN skip with warning
   - ELSE add to processing queue
5. Process images in parallel with ThreadPoolExecutor
6. FOR each future with timeout:
   - IF timeout exceeded THEN skip with warning
   - IF exception THEN log error, skip
   - ELSE collect result
7. Generate summary statistics
8. Write JSON report to output directory
9. Return ELAReport

Likelihood Score Calculation:
1. Calculate normalized_std_dev = std_dev(error_map) / 255
2. Calculate normalized_max_error = max(error_map) / 255
3. Detect edges using Canny edge detection
4. Calculate boundary_anomaly_ratio:
   - mean_error = mean(error_map)
   - edge_threshold = 2 × mean_error
   - count edge pixels exceeding threshold
   - ratio = anomalous_edge_pixels / total_edge_pixels
5. Score = (0.4 × normalized_std_dev) + (0.3 × normalized_max_error) + (0.3 × boundary_anomaly_ratio)
6. Return min(1.0, max(0.0, score))
```

### 2.6 Technical Approach

* **Module:** `src/gfiat/analyzers/ela.py`
* **Pattern:** Functional core with imperative shell; pure functions for analysis, I/O at edges
* **Key Decisions:** 
  - Use OpenCV for JPEG re-compression to match typical manipulation tools
  - Connected component analysis for region detection (more robust than simple thresholding)
  - Parallel processing with timeout to handle large images gracefully
  - Try/finally pattern ensures temp file cleanup even on exceptions

### 2.7 Architecture Decisions

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Image library | OpenCV, Pillow, scikit-image | OpenCV | Best JPEG compression control, likely already in project |
| Parallel processing | multiprocessing, concurrent.futures, asyncio | concurrent.futures.ThreadPoolExecutor | Simple timeout support, I/O bound task |
| Region detection | Simple threshold, connected components, watershed | Connected components | Good balance of accuracy and simplicity |
| Temp file handling | tempfile.NamedTemporaryFile, manual create/delete | Manual with try/finally | Explicit control over cleanup timing |

**Architectural Constraints:**
- Must use existing image processing infrastructure if present
- No external API calls or network access
- Must handle arbitrary directory structures safely

## 3. Requirements

*What must be true when this is done. These become acceptance criteria.*

1. Generate ELA map for each JPEG image in input path
2. Detection of known manipulated regions with >50% bounding box overlap
3. Clean images produce likelihood scores below baseline threshold
4. Output ELA overlay images with `_ela` suffix alongside analysis
5. Flag images with anomalous error distributions when likelihood exceeds threshold
6. CLI command `python -m src.gfiat.analyze ela ./extracted/` functions as specified
7. Non-JPEG files skipped with appropriate warning logged
8. Recursive directory scan skips symlinks to prevent infinite loops
9. Temporary files deleted even if analysis process raises unhandled exception
10. JSON report generated with all specified fields
11. Quality, scale, threshold, and timeout parameters configurable via CLI flags
12. Images exceeding timeout threshold skipped with warning logged

## 4. Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| ELA only | Simple, well-understood technique | Limited to JPEG artifacts | **Selected** |
| ELA + FFT combined | Stronger detection signal | More complex, scope creep | Rejected (future issue) |
| ML-based classifier | Higher accuracy potential | Requires training data, calibration | Rejected (future issue) |
| Pillow for compression | Pure Python, simpler install | Less control over JPEG parameters | Rejected |

**Rationale:** ELA-only approach provides proven forensic value with manageable complexity. FFT and ML enhancements explicitly deferred to future issues per scope definition.

## 5. Data & Fixtures

### 5.1 Data Sources

| Attribute | Value |
|-----------|-------|
| Source | User-provided local JPEG images |
| Format | JPEG image files |
| Size | Variable (typical: 1-50 MB per image) |
| Refresh | Manual (user runs analysis) |
| Copyright/License | User-owned or licensed content |

### 5.2 Data Pipeline

```
User Images (JPEG) ──read──► OpenCV ──recompress──► TempFile ──compare──► ELA Map ──save──► Output Directory
```

### 5.3 Test Fixtures

| Fixture | Source | Notes |
|---------|--------|-------|
| `manipulated_sample.jpg` | Generated | Create by splicing region from one image to another |
| `clean_sample.jpg` | Generated | Unmodified JPEG image |
| `high_detail_sample.jpg` | Generated | Image with text/sharp edges |
| `fixture_metadata.json` | Created during implementation | Ground truth bounding boxes, baseline scores |

### 5.4 Deployment Pipeline

Test fixtures are generated once during implementation and committed to repository. No external data fetching required. Fixture metadata documents expected outputs for automated verification.

## 6. Diagram

### 6.1 Mermaid Quality Gate

- [x] **Simplicity:** Components consolidated appropriately
- [x] **No touching:** All elements have visual separation
- [x] **No hidden lines:** All arrows fully visible
- [x] **Readable:** Labels not truncated, flow direction clear
- [ ] **Auto-inspected:** Agent rendered via mermaid.ink and viewed

**Auto-Inspection Results:**
```
- Touching elements: [ ] None / [ ] Found: ___
- Hidden lines: [ ] None / [ ] Found: ___
- Label readability: [ ] Pass / [ ] Issue: ___
- Flow clarity: [ ] Clear / [ ] Issue: ___
```

### 6.2 Diagram

```mermaid
flowchart TD
    subgraph Input
        A[User CLI Command]
        B[Input Directory]
    end
    
    subgraph Scanning
        C{File Type?}
        D[Skip: Non-JPEG]
        E[Skip: Symlink]
        F[JPEG Queue]
    end
    
    subgraph Processing
        G[ThreadPoolExecutor]
        H[analyze_image]
        I[generate_ela_map]
        J[calculate_likelihood_score]
        K[detect_anomalous_regions]
    end
    
    subgraph Output
        L[ELA Overlay Image]
        M[JSON Report]
        N[Console Output]
    end
    
    A --> B
    B --> C
    C -->|Non-JPEG| D
    C -->|Symlink| E
    C -->|JPEG| F
    F --> G
    G --> H
    H --> I
    I --> J
    J --> K
    K --> L
    K --> M
    M --> N
```

```mermaid
sequenceDiagram
    participant CLI
    participant Analyzer
    participant TempFile
    participant OpenCV
    participant Output
    
    CLI->>Analyzer: analyze_directory(path, params)
    loop Each JPEG
        Analyzer->>OpenCV: Read original image
        Analyzer->>TempFile: Create temp file
        Analyzer->>OpenCV: Compress at quality level
        Analyzer->>OpenCV: Read recompressed
        Analyzer->>Analyzer: Calculate ELA map
        Analyzer->>Analyzer: Detect anomalies
        Analyzer->>Output: Save ELA overlay
        Analyzer->>TempFile: Delete (finally block)
    end
    Analyzer->>Output: Write JSON report
    Analyzer-->>CLI: Return ELAReport
```

## 7. Security & Safety Considerations

### 7.1 Security

| Concern | Mitigation | Status |
|---------|------------|--------|
| Path traversal via symlinks | Skip symlinks during directory traversal | Addressed |
| Malicious image files | OpenCV handles parsing; errors caught and logged | Addressed |
| Output directory injection | Validate output path, use pathlib for safe joins | Addressed |
| Temp file exposure | Create in system temp dir, delete immediately after use | Addressed |

### 7.2 Safety

| Concern | Mitigation | Status |
|---------|------------|--------|
| Original image modification | Read-only operations; never write to input files | Addressed |
| Temp file leakage | Try/finally pattern guarantees cleanup | Addressed |
| Resource exhaustion (large images) | Per-image timeout with configurable limit | Addressed |
| Infinite loop (recursive symlinks) | Symlinks skipped during traversal | Addressed |
| Disk space exhaustion | ELA overlays similar size to originals; user controls output location | Addressed |

**Fail Mode:** Fail Closed - Individual image failures logged but don't stop batch processing. Final report indicates what failed.

**Recovery Strategy:** Re-run analysis on failed images individually with increased timeout or after freeing resources.

## 8. Performance & Cost Considerations

### 8.1 Performance

| Metric | Budget | Approach |
|--------|--------|----------|
| Per-image latency | < 5s typical | OpenCV native operations, parallel processing |
| Memory | < 500MB peak | Process images sequentially within thread, don't hold all in memory |
| Disk I/O | Minimize temp file lifetime | Create, use, delete temp file immediately |

**Bottlenecks:** 
- Large images (>50MP) may approach timeout
- Disk I/O for writing ELA overlays is sequential

### 8.2 Cost Analysis

| Resource | Unit Cost | Estimated Usage | Monthly Cost |
|----------|-----------|-----------------|--------------|
| Local compute | $0 | User machine | $0 |
| Disk space | $0 | ~1x input size for overlays | $0 |

**Cost Controls:**
- [x] No cloud resources used
- [x] No API calls
- [x] Fully local processing

**Worst-Case Scenario:** User runs on directory with thousands of large images. Timeout mechanism prevents hangs. Parallel processing bounded by ThreadPoolExecutor default workers.

## 9. Legal & Compliance

| Concern | Applies? | Mitigation |
|---------|----------|------------|
| PII/Personal Data | Yes | Images may contain PII; no data transmitted, all local processing |
| Third-Party Licenses | No | OpenCV is BSD licensed, compatible with project |
| Terms of Service | N/A | No external services used |
| Data Retention | N/A | User controls their files; tool doesn't persist data |
| Export Controls | No | Standard image processing, no encryption |

**Data Classification:** User-controlled - tool processes whatever user provides locally

**Compliance Checklist:**
- [x] No PII transmitted externally
- [x] All third-party licenses compatible (OpenCV BSD, NumPy BSD)
- [x] No external API usage
- [x] No data retention by tool

## 10. Verification & Testing

### 10.1 Test Scenarios

| ID | Scenario | Type | Input | Expected Output | Pass Criteria |
|----|----------|------|-------|-----------------|---------------|
| 010 | Analyze manipulated image | Auto | `manipulated_sample.jpg` | ELA overlay + high score | BBox overlap >50% with ground truth |
| 020 | Analyze clean image | Auto | `clean_sample.jpg` | ELA overlay + low score | Score below baseline in metadata |
| 030 | High-detail image | Auto | `high_detail_sample.jpg` | ELA overlay + notes | Contains "high-detail area" note |
| 040 | Skip non-JPEG | Auto | Directory with PNG | Warning logged, PNG skipped | Report shows skipped file |
| 050 | Skip symlink | Auto | Directory with symlink | Warning logged, symlink skipped | No infinite loop, skipped in report |
| 060 | Empty directory | Auto | Empty directory | Info message | "No JPEG images found" logged |
| 070 | Timeout exceeded | Auto | Mock slow processing | Skip with warning | Report shows timeout skip |
| 080 | Temp file cleanup on error | Auto | Mock exception during analysis | Temp file deleted | No orphaned temp files |
| 090 | CLI parameters | Auto | Various CLI args | Correct parameters passed | Parameters in report match CLI |
| 100 | JSON report structure | Auto | Any valid JPEG | Valid JSON report | Report validates against schema |
| 110 | Corrupted JPEG | Auto | Corrupted JPEG file | Error logged, continue | Other files still processed |
| 120 | Very small image | Auto | 50x50 JPEG | Processed or skipped with note | Graceful handling |

### 10.2 Test Commands

```bash
# Run all automated tests
poetry run pytest tests/test_ela.py -v

# Run only fast/mocked tests (exclude live)
poetry run pytest tests/test_ela.py -v -m "not live"

# Run with coverage
poetry run pytest tests/test_ela.py -v --cov=src/gfiat/analyzers/ela --cov-report=term-missing
```

### 10.3 Manual Tests (Only If Unavoidable)

| ID | Scenario | Why Not Automated | Steps |
|----|----------|-------------------|-------|
| M010 | Visual ELA overlay quality | Requires human assessment of forensic utility | 1. Run ELA on manipulated_sample.jpg 2. Open _ela.jpg overlay 3. Verify manipulated region visually highlighted 4. Confirm overlay is interpretable |

## 11. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| False positives on high-detail regions | Med | High | Add notes for high-detail areas, threshold tuning |
| OpenCV version incompatibility | Med | Low | Pin version, test in CI |
| Very large images cause memory issues | High | Low | Timeout mechanism, streaming if needed |
| Test fixtures don't match real-world cases | Med | Med | Create diverse fixtures, document limitations |
| Score formula needs calibration | Med | Med | Document as heuristic, allow threshold tuning |

## 12. Definition of Done

### Code
- [ ] Implementation complete in `src/gfiat/analyzers/ela.py`
- [ ] Models defined in `src/gfiat/models/ela_report.py`
- [ ] CLI integrated in `src/gfiat/cli/analyze.py`
- [ ] Code linted and formatted

### Tests
- [ ] All 12 test scenarios pass
- [ ] Test coverage >80% on new code
- [ ] Integration test with sample manipulated image

### Documentation
- [ ] LLD updated with any deviations
- [ ] Implementation Report (0103) completed
- [ ] Update wiki with ELA methodology and interpretation guide
- [ ] Update README.md with new CLI command
- [ ] Add files to `docs/0003-file-inventory.md`

### Review
- [ ] Code review completed
- [ ] 0809 Security Audit - PASS
- [ ] 0817 Wiki Alignment Audit - PASS
- [ ] User approval before closing issue

---

## Appendix: Review Log

*Track all review feedback with timestamps and implementation status.*

### Review Summary

| Review | Date | Verdict | Key Issue |
|--------|------|---------|-----------|
| - | - | - | Awaiting initial review |

**Final Status:** PENDING