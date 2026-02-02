# Issue #33: G-FIAT: Rock Photo Classifier

# G-FIAT: Rock Photo Classifier

## User Story
As a geological analyst,
I want to automatically classify images extracted from geological reports,
So that I can focus forensic analysis on actual rock/core photographs and skip irrelevant imagery like logos and charts.

## Objective
Build an image classifier that distinguishes rock sample photographs from other imagery types (logos, charts, diagrams) using visual heuristics, enabling efficient downstream processing.

## UX Flow

### Scenario 1: Classify Extracted Images (Happy Path)
1. User runs `python -m src.gfiat.classify ./extracted/`
2. System loads manifest and iterates through extracted images
3. System analyzes each image using heuristic classifiers
4. System outputs classification results with confidence scores
5. Result: Updated manifest with `classification` field for each image

### Scenario 2: Low Confidence Classification
1. User runs classifier on images
2. System encounters ambiguous image (e.g., stylized rock diagram)
3. System assigns `unknown` classification with low confidence score
4. Result: Image flagged for manual review

### Scenario 3: Manual Override via Config
1. User creates override config specifying image classifications
2. User runs classifier with `--overrides overrides.json`
3. System applies manual classifications, skipping heuristic analysis for specified images
4. Result: Manual classifications preserved in manifest

### Scenario 4: No Images Found
1. User runs classifier on empty or invalid directory
2. System detects no valid images or manifest
3. System exits with clear error message
4. Result: User informed of issue, no manifest corruption

### Scenario 5: Decompression Bomb Protection
1. User runs classifier on directory containing malicious oversized image
2. System detects image exceeds `MAX_IMAGE_PIXELS` threshold before full decompression
3. System logs warning and skips the malicious file
4. Result: System remains stable, other images processed normally

## Requirements

### Ground Truth Dataset
1. Curate and label a test dataset of at least 50 images covering all classification categories
2. Dataset must include: rock_photo (15+), thin_section (10+), chart (10+), logo (5+), diagram (5+), unknown/ambiguous (5+)
3. Store labeled dataset in `tests/fixtures/classify/ground_truth/` with classification manifest
4. Ground truth manifest serves as source of truth for accuracy calculations

### Image Analysis
1. Calculate aspect ratio and flag extreme rectangles (likely logos/banners)
2. Generate color histogram and compute earth-tone ratio (browns, grays, tans)
3. Perform texture analysis using edge detection or frequency analysis
4. Calculate edge density and regularity metrics

### Supported Image Formats
1. Support JPEG/JPG image files
2. Support PNG image files
3. Support TIFF image files
4. Reject unsupported formats with clear error message

### Resource Protection
1. Set `PIL.Image.MAX_IMAGE_PIXELS` to 89,478,485 (default) or configurable limit to prevent decompression bombs
2. Validate image file size does not exceed 50MB before attempting to load
3. Validate image dimensions do not exceed 10,000 x 10,000 pixels
4. Log warning and skip images that exceed resource limits

### Classification
1. Assign one of: `rock_photo`, `thin_section`, `chart`, `logo`, `diagram`, `unknown`
2. Compute confidence score (0.0-1.0) based on heuristic agreement
3. Support configurable thresholds for classification boundaries
4. Distinguish thin section photomicrographs from core plug photos

### Manifest Integration
1. Read existing manifest from extraction output (see Dependencies for schema)
2. Add `classification` and `classification_confidence` fields per image
3. Preserve all existing manifest data
4. Write updated manifest atomically (temp file + rename)

### Override System
1. Accept JSON config file mapping image paths to manual classifications
2. Manual overrides take precedence over heuristic results
3. Mark overridden entries with `classification_source: "manual"`

## Technical Approach
- **Aspect Ratio Filter:** PIL/Pillow to get dimensions, flag width:height ratios > 3:1 as likely logos/banners
- **Color Analysis:** NumPy histogram binning, compute percentage of pixels in earth-tone HSV ranges
- **Texture Analysis:** Scikit-image for Laplacian variance (blur detection) and local binary patterns
- **Edge Density:** Canny edge detection, compute edge pixel percentage and regularity score
- **Ensemble Classifier:** Weighted voting from heuristics, confidence = agreement level
- **Resource Protection:** Set `Image.MAX_IMAGE_PIXELS` before any image load operations

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No structural changes - new standalone module
- [ ] **Cost:** Minimal - local image processing only, no API calls
- [ ] **Legal/PII:** No - processes geological images only, no personal data
- [x] **Safety:** Medium risk - image processing vulnerable to decompression bombs; mitigated via `MAX_IMAGE_PIXELS` limit and file size validation

## Security Considerations
- **Decompression Bomb Protection:** `PIL.Image.MAX_IMAGE_PIXELS` set to prevent memory exhaustion from malicious images
- **File Size Validation:** Reject files >50MB before loading into memory
- Image processing uses standard libraries (PIL, scikit-image) with no code execution risk
- File paths validated to prevent directory traversal
- Override config parsed with strict JSON schema validation
- No network access required

## Files to Create/Modify
- `src/gfiat/classify.py` â€” Main classifier module with CLI entry point
- `src/gfiat/classifiers/aspect_ratio.py` â€” Aspect ratio heuristic
- `src/gfiat/classifiers/color_histogram.py` â€” Color analysis heuristic
- `src/gfiat/classifiers/texture.py` â€” Texture analysis heuristic
- `src/gfiat/classifiers/edge_density.py` â€” Edge detection heuristic
- `src/gfiat/classifiers/ensemble.py` â€” Voting ensemble combining heuristics
- `src/gfiat/classifiers/resource_guard.py` â€” Decompression bomb and resource limit protection
- `tests/test_classify.py` â€” Unit tests for classifier
- `tests/fixtures/classify/` â€” Test images (rock, logo, chart samples)
- `tests/fixtures/classify/ground_truth/` â€” Labeled ground truth dataset for accuracy verification
- `tests/fixtures/classify/ground_truth/manifest.json` â€” Ground truth classification labels

## Dependencies
- **Image extraction module** ([Issue #42](https://github.com/org/repo/issues/42)) must be complete â€” provides manifest format
  - **Manifest Schema (Locked):**
    ```json
    {
      "version": "1.0",
      "source_document": "string",
      "extraction_date": "ISO8601 string",
      "images": [
        {
          "path": "string (relative path to extracted image)",
          "page": "number (1-indexed page number)",
          "type": "string (embedded|inline|background)",
          "width": "number (pixels)",
          "height": "number (pixels)",
          "format": "string (jpeg|png|tiff)"
        }
      ]
    }
    ```
  - Classifier adds `classification`, `classification_confidence`, and optionally `classification_source` fields to each image entry
- PIL/Pillow for image loading
- NumPy for array operations
- scikit-image for advanced image analysis

## Out of Scope (Future)
- **ML-based classifier** â€” Start with heuristics, ML model deferred pending accuracy evaluation
- **Training data collection** â€” Ground truth dataset is for testing only, not ML training
- **GPU acceleration** â€” Heuristics are fast enough on CPU
- **Real-time classification** â€” Batch processing only for MVP
- **Web UI for manual review** â€” CLI override config sufficient for MVP
- **Confusion matrix output** â€” Useful for debugging but not MVP requirement

## Acceptance Criteria
- [ ] CLI `python -m src.gfiat.classify ./extracted/` processes all images in directory
- [ ] Each image receives classification: `rock_photo`, `thin_section`, `chart`, `logo`, `diagram`, or `unknown`
- [ ] Each classification includes confidence score between 0.0 and 1.0
- [ ] Rock/core photos identified with >80% accuracy on ground truth test dataset
- [ ] Images labeled as logos/charts in the ground truth dataset filtered with >90% accuracy
- [ ] Manifest updated with `classification` and `classification_confidence` fields
- [ ] Manual override via `--overrides config.json` applies specified classifications
- [ ] Thin section photomicrographs distinguished from core plug photos
- [ ] Graceful handling of corrupted/unreadable images (skip with warning)
- [ ] Images exceeding resource limits (>50MB or decompression bomb) skipped with warning
- [ ] Ground truth dataset of 50+ labeled images created and committed

## Definition of Done

### Implementation
- [ ] Core classifier module implemented with all heuristics
- [ ] Ensemble voting logic combining heuristic scores
- [ ] Resource guard module protecting against decompression bombs
- [ ] Unit tests written and passing (>90% coverage on classifier logic)
- [ ] Ground truth dataset curated with 50+ labeled images across all categories

### Tools
- [ ] CLI entry point with `--overrides` and `--threshold` options
- [ ] `--dry-run` option to preview classifications without modifying manifest
- [ ] `--verbose` option for debugging heuristic scores

### Documentation
- [ ] Update wiki with classifier usage and heuristic explanations
- [ ] Document override config JSON schema
- [ ] Add tuning guide for classification thresholds
- [ ] Document ground truth dataset format and how to extend it

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created with accuracy metrics against ground truth

### Verification
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes
- **Ground Truth Verification:** Run classifier against `tests/fixtures/classify/ground_truth/` and compare to `manifest.json` labels
- **Accuracy calculation:** `(correct classifications / total ground truth images) * 100`
- Test dataset should include: clear rock photos, logos, charts, diagrams, thin sections, and edge cases
- Edge cases to test: black and white photos, photos with scale bars, heavily annotated core photos
- Force low confidence by using ambiguous images (rock-textured backgrounds, geological diagrams)
- Test override by manually classifying known-misclassified images
- Verify manifest integrity by comparing pre/post classification (only classification fields should change)
- **Resource protection tests:** Include oversized test image (or mock) to verify decompression bomb protection

## Labels
`feature`, `g-fiat`, `mvp`

## Original Brief
# G-FIAT: Rock Photo Classifier

## Problem

Geological reports contain many image types: logos, charts, diagrams, maps, and actual core/rock photos. Running forensic analysis on logos is pointless and wastes compute. We need to automatically identify which images are actual rock sample photographs.

## Proposed Solution

Build a classifier to distinguish rock photos from other imagery based on visual characteristics.

### Classification Heuristics

1. **Aspect Ratio Filter**
   - Core photos are typically square or portrait
   - Logos are often wide rectangles
   - Charts have specific aspect ratios

2. **Color Histogram Analysis**
   - Rock photos: earth tones (browns, grays, tans)
   - Logos: often have bright/saturated colors
   - Charts: high contrast, limited color palette

3. **Texture Analysis**
   - Rock photos: high-frequency noise (grain texture)
   - Logos: smooth gradients or solid colors
   - Charts: sharp edges, uniform regions

4. **Edge Density**
   - Rock photos: organic, irregular edges
   - Diagrams: geometric, regular edges

### Output
- Classification label per image: `rock_photo`, `chart`, `logo`, `diagram`, `unknown`
- Confidence score
- Updated manifest with classification

## Acceptance Criteria

- [ ] Classify images from extraction output
- [ ] Identify rock/core photos with >80% accuracy
- [ ] Filter out obvious non-photos (logos, charts)
- [ ] Add `classification` field to manifest
- [ ] Allow manual override via config file
- [ ] CLI: `python -m src.gfiat.classify ./extracted/`

## Technical Considerations

- Start with heuristics, consider ML model later if needed
- May need training data for ML approach
- Some legitimate photos may be misclassified (accept manual override)
- Thin section photomicrographs look different from core photos
- Consider separate class for thin sections vs. core plugs

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-02-01 | **Reviews:** 3</sub>
