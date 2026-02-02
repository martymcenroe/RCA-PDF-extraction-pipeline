# G-FIAT: SIFT Feature Extraction Engine

## User Story
As a geologist analyzing core sample imagery,
I want rotation and scale invariant feature extraction from my images,
So that I can match duplicate or near-duplicate images even when they've been rotated, cropped, or rescaled.

## Objective
Implement SIFT (Scale-Invariant Feature Transform) keypoint extraction using OpenCV to generate persistent descriptors that survive geometric transformations where perceptual hashes fail.

## UX Flow

### Scenario 1: Happy Path - Extract Features from Directory
1. User runs `python -m src.gfiat.fingerprint --method sift ./extracted/`
2. System scans directory for supported image files
3. For each image:
   - Converts to grayscale
   - Extracts SIFT keypoints and descriptors
   - Incrementally writes descriptors to `.npy` file (streaming write, not memory accumulation)
   - Updates manifest with keypoint metadata
4. System reports: "Processed 47 images, extracted 38,420 total keypoints"
5. Result: `./extracted/sift_descriptors/` directory with `.npy` files and updated manifest

### Scenario 2: Large Image Handling
1. User processes directory containing 6000x4000 pixel images
2. System detects images exceed 4000x4000 threshold
3. System automatically downsamples to max dimension while preserving aspect ratio
4. System logs: "Downsampled image_042.jpg from 6000x4000 to 4000x2667"
5. Result: Features extracted successfully with downsampling noted in manifest

### Scenario 3: Uniform Texture Warning
1. User processes image with large uniform regions (e.g., mudstone with minimal features)
2. System extracts only 23 keypoints (below typical threshold)
3. System logs warning: "Low keypoint count (23) for image_019.jpg - uniform texture detected"
4. Result: Processing continues, warning captured in manifest for user review

### Scenario 4: Invalid Image Format
1. User's directory contains unsupported file (e.g., `.pdf`, corrupted `.jpg`)
2. System logs error: "Skipping document.pdf - unsupported format" with error type recorded
3. System continues processing remaining images
4. Result: Summary includes skipped file count; log file contains filename and error type for each skipped file

### Scenario 5: Dry Run Preview
1. User runs `python -m src.gfiat.fingerprint --method sift --dry-run ./extracted/`
2. System scans directory and reports: "Dry run: Would process 47 images (3 would be downsampled)"
3. No files are created or modified
4. Result: User can preview processing scope before committing

## Requirements

### Feature Extraction
1. Detect SIFT keypoints using OpenCV's `cv2.SIFT_create()`
2. Generate 128-dimensional float32 descriptor for each keypoint
3. Retain top N keypoints by response strength (configurable, default 1000)
4. Handle grayscale conversion using `cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)`

### Storage Format
1. Save descriptors as NumPy `.npy` files (one per image)
2. Write `.npy` files incrementally per-image (process image → write file → release memory) to prevent RAM accumulation
3. File naming: `{original_filename}_sift.npy`
4. Store keypoint metadata in manifest:
   - Keypoint count
   - Image dimensions (original and processed)
   - Downsampling factor if applied
   - Top keypoint locations (x, y, scale, orientation)

### Performance
1. Process images up to 4000x4000 pixels without downsampling
2. Auto-downsample larger images with aspect ratio preservation
3. Target processing time: <5 seconds per typical geological image
4. Memory usage must not exceed 2GB during batch processing of 100 images
5. Each image processed and written independently; memory released after each image

### Input Validation & Security
1. **Output path sanitization:** Validate `--output-dir` to prevent directory traversal attacks
2. Reject paths containing `..` or absolute paths outside project root
3. Confine all writes to within the project/sandbox root directory
4. Log rejected path attempts with sanitized error message

### CLI Interface
1. Command: `python -m src.gfiat.fingerprint --method sift <input_path>`
2. Options:
   - `--max-keypoints N` (default: 1000)
   - `--max-dimension N` (default: 4000)
   - `--output-dir PATH` (default: `<input_path>/sift_descriptors/`) — validated for path traversal
   - `--dry-run` — preview processing without extracting features
   - `--verbose` for detailed logging

## Technical Approach
- **OpenCV SIFT:** Use `cv2.SIFT_create()` with configurable nfeatures parameter for keypoint detection and descriptor generation. Standard `opencv-python-headless` package (BSD-licensed, SIFT available since v4.4.0).
- **NumPy Storage:** Serialize descriptor arrays to `.npy` format with per-image write strategy (write immediately after extraction, release memory before next image)
- **Manifest Integration:** Extend existing manifest schema to include SIFT metadata per image
- **Batch Processing:** Process images sequentially with progress reporting; memory released after each image write
- **Path Validation:** Implement `validate_output_path()` function that canonicalizes paths and rejects any path outside project root

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** Adds new fingerprinting method alongside existing pHash - follows established pattern
- [x] **Cost:** SIFT descriptors are ~128KB per 1000 keypoints per image - storage scales with image count
- [ ] **Legal/PII:** No PII involved - geological imagery only. Using BSD-licensed `opencv-python-headless` (SIFT free since OpenCV 4.4.0)
- [ ] **Safety:** Read-only on source images; writes only to validated output directory within project root

## Security Considerations
- Read-only access to source images (no modification)
- **Output path validation:** All output paths validated against directory traversal (rejects `..`, validates canonical path is within project root)
- Output directory created with standard permissions (0755)
- No network calls or external API dependencies
- OpenCV is a well-maintained, widely-audited library

## Files to Create/Modify
- `src/gfiat/fingerprint/sift.py` — Core SIFT extraction logic
- `src/gfiat/fingerprint/path_validator.py` — Output path sanitization and validation
- `src/gfiat/fingerprint/__init__.py` — Register SIFT as available method
- `src/gfiat/fingerprint/cli.py` — Add `--method sift` and `--dry-run` options
- `src/gfiat/manifest/schema.py` — Extend schema for SIFT metadata
- `tests/fingerprint/test_sift.py` — Unit tests for SIFT extraction
- `tests/fingerprint/test_path_validator.py` — Unit tests for path validation
- `tests/fixtures/` — Add test images with known keypoint counts

## Dependencies
- OpenCV headless (`opencv-python-headless>=4.5.0`) — standard BSD-licensed package, SIFT included since 4.4.0
- NumPy (already in project)
- Extraction phase must be complete (images available in `./extracted/`)

## Out of Scope (Future)
- **Keypoint matching** — separate issue for comparing descriptors between images
- **SURF/ORB alternatives** — may add as options in future iteration
- **SQLite storage** — evaluate after measuring `.npy` performance at scale
- **GPU acceleration** — CUDA SIFT for large batch processing
- **Keypoint visualization** — debug tool to overlay keypoints on images

## Acceptance Criteria
- [ ] `python -m src.gfiat.fingerprint --method sift ./extracted/` executes without error
- [ ] `.npy` files created in output directory for each processed image
- [ ] Manifest updated with keypoint count per image
- [ ] Grayscale conversion handles RGB, RGBA, and already-grayscale images
- [ ] Images >4000px on any dimension are automatically downsampled
- [ ] Processing completes for directory with 100+ images with memory usage not exceeding 2GB
- [ ] Low-keypoint images (<50) generate warning in output
- [ ] Unsupported/corrupted files are skipped; log file records filename and error type for each skipped file
- [ ] `--max-keypoints` flag limits stored keypoints per image
- [ ] `--output-dir` rejects paths containing `..` or paths outside project root
- [ ] `--dry-run` flag previews processing without creating files
- [ ] Unit tests cover: normal extraction, large image downsampling, uniform texture, invalid input, path traversal rejection

## Definition of Done

### Implementation
- [ ] Core SIFT extraction implemented in `sift.py`
- [ ] Path validation implemented in `path_validator.py`
- [ ] CLI integration complete with all specified options
- [ ] Unit tests written and passing (>90% coverage on new code)

### Tools
- [ ] CLI documented with `--help` output
- [ ] Example usage in module docstring

### Documentation
- [ ] Update wiki with SIFT feature explanation
- [ ] Update README.md with new `--method sift` option
- [ ] Document storage format in technical docs
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Manual Testing
```bash
# Basic extraction
python -m src.gfiat.fingerprint --method sift ./test_images/

# Dry run preview
python -m src.gfiat.fingerprint --method sift --dry-run ./test_images/

# With options
python -m src.gfiat.fingerprint --method sift --max-keypoints 500 --verbose ./test_images/

# Verify output
ls ./test_images/sift_descriptors/
python -c "import numpy as np; d = np.load('image_001_sift.npy'); print(d.shape)"

# Test path traversal rejection (should fail)
python -m src.gfiat.fingerprint --method sift --output-dir ../../etc/passwd ./test_images/
```

### Edge Cases to Test
1. **Rotation invariance:** Extract features from original and 45° rotated version, verify similar keypoint count
2. **Scale invariance:** Extract from original and 50% scaled version
3. **Uniform image:** Process solid color image, expect <10 keypoints with warning
4. **Large image:** Process 8000x6000 image, verify downsampling occurs
5. **Mixed directory:** Include `.txt`, `.pdf` files alongside images, verify graceful skipping with logged errors
6. **Path traversal:** Attempt `--output-dir ../../../tmp/`, verify rejection
7. **Memory constraint:** Process 100+ images, verify memory stays under 2GB
8. **Dry run:** Verify no files created when `--dry-run` flag used

## Original Brief
# G-FIAT: SIFT Feature Extraction Engine

## Problem

Perceptual hashes fail when images are rotated, scaled, or cropped. A photo of core sample at 9,000ft rotated 30 degrees and darkened will have a completely different pHash than the original. We need rotation and scale invariant feature extraction.

## Proposed Solution

Implement SIFT (Scale-Invariant Feature Transform) using OpenCV to generate keypoint descriptors that persist through geometric transformations.

### Core Functionality
- Detect keypoints (distinctive textures like grain boundaries, vugs, fractures)
- Generate 128-dimensional descriptors for each keypoint
- Store descriptors in efficient format for later matching
- Typical geological image yields 500-2000 keypoints

### How SIFT Works
1. Build scale-space pyramid (Gaussian blur at multiple scales)
2. Find local extrema (potential keypoints)
3. Filter weak keypoints and edge responses
4. Assign orientation to each keypoint
5. Generate 128-dim descriptor from local gradients

### Output Format
- NumPy `.npy` files for descriptors (efficient storage)
- Keypoint metadata in manifest (x, y, scale, orientation)
- Or SQLite database for larger datasets

## Acceptance Criteria

- [ ] Extract SIFT keypoints from all images in extraction output
- [ ] Store descriptors in `.npy` format per image
- [ ] Update manifest with keypoint count per image
- [ ] Handle grayscale conversion properly (SIFT requires grayscale)
- [ ] Process images up to 4000x4000 pixels
- [ ] CLI: `python -m src.gfiat.fingerprint --method sift ./extracted/`

## Technical Considerations

- SIFT was patented until 2020, now free in OpenCV
- Memory intensive for large images - may need to downsample
- Consider SURF or ORB as faster alternatives (less accurate)
- Keypoints on uniform textures are unreliable - rock photos should have enough variation
- Store only top N keypoints by response strength to manage storage

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-02-01 | **Reviews:** 2</sub>
