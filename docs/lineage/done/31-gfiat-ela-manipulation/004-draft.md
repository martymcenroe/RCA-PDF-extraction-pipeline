# Error Level Analysis (ELA) for Image Manipulation Detection

## User Story
As a **forensic analyst**,
I want **to detect digitally manipulated regions in extracted images using Error Level Analysis**,
So that **I can identify spliced content, copy-paste alterations, and other forms of image tampering**.

## Objective
Implement Error Level Analysis (ELA) to detect image manipulation by comparing JPEG compression artifacts across image regions, flagging areas with anomalous error distributions that indicate potential tampering.

## UX Flow

### Scenario 1: Analyze Images for Manipulation (Happy Path)
1. User runs `python -m src.gfiat.analyze ela ./extracted/`
2. System scans directory for JPEG images
3. For each image, system re-compresses at 90% quality and calculates pixel-wise differences
4. System generates ELA overlay images alongside originals
5. System outputs JSON report with error levels and manipulation likelihood scores
6. Result: User reviews flagged images and ELA overlays to assess manipulation

### Scenario 2: Non-JPEG Image Encountered
1. User runs ELA analysis on a directory containing PNG files
2. System detects PNG format (no compression artifacts to analyze)
3. System logs warning: "Skipping {filename}: ELA only applicable to JPEG images"
4. System continues processing remaining JPEG files
5. Result: Report includes list of skipped files with reason

### Scenario 3: High False Positive Region
1. User analyzes image with legitimately high-detail regions (text, sharp edges)
2. System detects high error levels in these regions
3. System applies region-based analysis to distinguish detail from manipulation
4. System flags region but notes "high-detail area - verify manually"
5. Result: User receives nuanced report distinguishing likely manipulation from natural artifacts

### Scenario 4: No Images Found
1. User runs ELA analysis on empty directory
2. System finds no JPEG files
3. System outputs: "No JPEG images found in {path}"
4. Result: User is informed clearly without error

### Scenario 5: Symlink in Directory Tree
1. User runs ELA analysis on directory containing symlinks
2. System detects symlink during recursive scan
3. System skips symlink and logs: "Skipping symlink: {path}"
4. Result: Infinite loop prevented, analysis continues on regular files

## Requirements

### Core Analysis
1. Re-compress input image at configurable quality level (default: 90%)
2. Calculate pixel-wise absolute difference between original and re-compressed
3. Scale difference values for visibility (configurable multiplier, default: 15)
4. Generate ELA overlay image saved alongside original with `_ela` suffix

### Detection Heuristics
1. Calculate mean and maximum error levels per image
2. Identify uniform low-error regions (potential copy-paste from same compression level)
3. Detect high-error boundaries (splice edges between different sources)
4. Compute manipulation likelihood score (0.0-1.0) based on error distribution anomalies

### Output Format
1. Save ELA overlay images as `{original_name}_ela.jpg`
2. Generate JSON report containing:
   - Image path
   - Mean/max error levels
   - Regions exceeding threshold (bounding boxes)
   - Manipulation likelihood score
   - List of skipped non-JPEG files

### CLI Interface
1. Command: `python -m src.gfiat.analyze ela <input_path>`
2. Support both single file and directory input
3. Options: `--quality` (compression quality), `--scale` (visibility multiplier), `--threshold` (detection sensitivity), `--timeout` (per-image timeout in seconds, default: 60)
4. Output path defaults to `./ela_output/` or specified via `--output`

## Technical Approach
- **Image Processing:** OpenCV for image I/O, compression, and difference calculation
- **Temporary Files:** Use `tempfile` module for re-compressed intermediates with try/finally cleanup to ensure deletion even on exceptions
- **Region Detection:** Connected component analysis on thresholded ELA map to identify anomalous regions
- **Scoring Algorithm:** Statistical analysis of error distribution (standard deviation, histogram entropy) to compute likelihood score — purely heuristic, no calibration dataset required
- **Batch Processing:** Parallel processing with `concurrent.futures` for directory analysis
- **Timeout Handling:** Per-image timeout to prevent hanging on very large images

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No significant structural changes - adds new analysis module
- [ ] **Cost:** Moderate disk I/O for temporary files; cleaned up after processing via try/finally
- [ ] **Legal/PII:** Images may contain sensitive content; no data leaves local system
- [ ] **Safety:** Temporary files created and deleted in try/finally block; no risk of data loss to originals

## Security Considerations
- Original images are never modified; only read operations performed
- Temporary re-compressed files are created in system temp directory and deleted after analysis (guaranteed via try/finally)
- No network access required; all processing is local
- Output directory permissions inherit from parent; no elevated privileges needed
- Symlinks are skipped during directory traversal to prevent infinite loops or path traversal attacks

## Files to Create/Modify
- `src/gfiat/analyzers/ela.py` — Core ELA analysis implementation
- `src/gfiat/analyzers/__init__.py` — Export ELA analyzer
- `src/gfiat/cli/analyze.py` — Add `ela` subcommand to CLI
- `src/gfiat/models/ela_report.py` — Data classes for ELA results
- `tests/test_ela.py` — Unit tests for ELA analysis
- `tests/fixtures/ela/` — Test images (manipulated and clean samples)

## Dependencies
- OpenCV (`opencv-python`) — likely already installed for image processing
- NumPy — likely already installed

## Out of Scope (Future)
- **Video frame analysis** — ELA for video deferred to future issue
- **Machine learning classifier** — ML-based manipulation detection beyond heuristics
- **FFT combination** — Combining with frequency analysis for stronger signal (mentioned in brief, separate issue)
- **Interactive GUI** — Visual tool for exploring ELA results
- **Cloud processing** — Batch processing via cloud infrastructure
- **Calibration dataset** — Score is purely heuristic; calibrated ML scoring is future scope

## Acceptance Criteria
- [ ] Generate ELA map for each JPEG image in input path
- [ ] When running against `tests/fixtures/ela/manipulated_sample.jpg`, system outputs a bounding box overlapping the known manipulated region by >50%
- [ ] When running against `tests/fixtures/ela/clean_sample.jpg`, likelihood score is <0.3
- [ ] Output ELA overlay images with `_ela` suffix alongside analysis
- [ ] Flag images with anomalous error distributions (likelihood > 0.7)
- [ ] CLI command `python -m src.gfiat.analyze ela ./extracted/` works as specified
- [ ] Non-JPEG files are skipped with appropriate warning logged
- [ ] Recursive directory scan skips symlinks to prevent infinite loops
- [ ] Temporary files are successfully deleted even if the analysis process raises an unhandled exception (try/finally implementation)
- [ ] JSON report generated with all specified fields
- [ ] Quality, scale, threshold, and timeout parameters are configurable via CLI flags
- [ ] Images exceeding timeout threshold are skipped with warning logged

## Definition of Done

### Implementation
- [ ] Core ELA analysis implemented in `src/gfiat/analyzers/ela.py`
- [ ] Unit tests written and passing (>80% coverage on new code)
- [ ] Integration test with sample manipulated image

### Tools
- [ ] CLI `ela` subcommand added to analyze module
- [ ] Help text documents all options and usage

### Documentation
- [ ] Update wiki with ELA analysis methodology and interpretation guide
- [ ] Update README.md with new CLI command
- [ ] Add files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Test Setup
1. Create test fixtures with known manipulated images (splice a region from one image to another)
2. Include clean images for false-positive testing
3. Include high-detail images (text, sharp edges) for edge case testing
4. Document exact bounding box coordinates of manipulated regions in fixture metadata

### Fixture-Based Verification
1. `tests/fixtures/ela/manipulated_sample.jpg` — Known spliced region at documented coordinates
2. `tests/fixtures/ela/clean_sample.jpg` — Unmodified image for baseline
3. `tests/fixtures/ela/high_detail_sample.jpg` — Text/edges for false positive testing
4. `tests/fixtures/ela/fixture_metadata.json` — Ground truth bounding boxes for automated verification

### Manual Verification
1. Run against `tests/fixtures/ela/manipulated_sample.jpg`
2. Verify ELA overlay highlights the spliced region
3. Verify JSON report shows elevated likelihood score (>0.7)
4. Verify detected bounding box overlaps known region by >50%
5. Run against `tests/fixtures/ela/clean_sample.jpg`
6. Verify likelihood score is low (<0.3)

### Edge Cases to Test
- PNG file in directory (should skip with warning)
- Corrupted JPEG file (should handle gracefully, log error, continue)
- Very small image (<100px) (should process or skip with note)
- Already heavily compressed image (quality <50)
- Image with no manipulation but high natural detail
- Symlink in directory (should skip with warning, no infinite loop)
- Very large image exceeding timeout (should skip with warning)
- Process crash during analysis (temp files still cleaned up)

## Labels
`feature`, `forensics`, `size: M`

## Original Brief
# G-FIAT: Error Level Analysis (ELA) for Manipulation Detection

## Problem

When an image region is digitally edited (e.g., a porous patch spliced from another sample), it often has different compression characteristics than the surrounding original content. Re-saved JPEG regions show different error levels than once-compressed regions.

## Proposed Solution

Implement Error Level Analysis to detect splicing and manipulation by comparing compression artifacts across image regions.

### Core Functionality
- Re-compress image at known quality (95%)
- Calculate pixel-wise difference from original
- Scale difference to visible range (multiply by 10-20)
- High-error regions indicate manipulation or splicing

### Algorithm
```python
def ela_analysis(image_path, quality=90, scale=15):
    # 1. Load original image
    original = cv2.imread(image_path)

    # 2. Re-save at specified quality
    cv2.imwrite(temp_path, original, [cv2.IMWRITE_JPEG_QUALITY, quality])
    resaved = cv2.imread(temp_path)

    # 3. Calculate absolute difference
    diff = cv2.absdiff(original, resaved)

    # 4. Scale for visibility
    ela_image = diff * scale

    return ela_image
```

### Output Format
- ELA overlay images saved alongside originals
- JSON report with:
  - Image path
  - Mean/max error levels
  - Regions exceeding threshold
  - Manipulation likelihood score

## Acceptance Criteria

- [ ] Generate ELA map for each extracted image
- [ ] Detect uniform regions (potential copy-paste)
- [ ] Detect high-error boundaries (splice edges)
- [ ] Output ELA overlay images for visual inspection
- [ ] Flag images with anomalous error distributions
- [ ] CLI: `python -m src.gfiat.analyze ela ./extracted/`

## Technical Considerations

- Only works on JPEG images (PNG has no compression artifacts)
- False positives on legitimately high-detail regions
- Quality parameter affects sensitivity (lower = more sensitive, more noise)
- May need region-based analysis, not just image-wide
- Combine with FFT analysis for stronger signal