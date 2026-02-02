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

## Requirements

### Image Analysis
1. Calculate aspect ratio and flag extreme rectangles (likely logos/banners)
2. Generate color histogram and compute earth-tone ratio (browns, grays, tans)
3. Perform texture analysis using edge detection or frequency analysis
4. Calculate edge density and regularity metrics

### Classification
1. Assign one of: `rock_photo`, `thin_section`, `chart`, `logo`, `diagram`, `unknown`
2. Compute confidence score (0.0-1.0) based on heuristic agreement
3. Support configurable thresholds for classification boundaries
4. Distinguish thin section photomicrographs from core plug photos

### Manifest Integration
1. Read existing manifest from extraction output
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

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No structural changes - new standalone module
- [ ] **Cost:** Minimal - local image processing only, no API calls
- [ ] **Legal/PII:** No - processes geological images only, no personal data
- [ ] **Safety:** Low risk - read-only on images, atomic manifest writes prevent corruption

## Security Considerations
- Image processing uses standard libraries (PIL, scikit-image) with no code execution risk
- File paths validated to prevent directory traversal
- Override config parsed with strict JSON schema validation
- No network access required

## Files to Create/Modify
- `src/gfiat/classify.py` — Main classifier module with CLI entry point
- `src/gfiat/classifiers/aspect_ratio.py` — Aspect ratio heuristic
- `src/gfiat/classifiers/color_histogram.py` — Color analysis heuristic
- `src/gfiat/classifiers/texture.py` — Texture analysis heuristic
- `src/gfiat/classifiers/edge_density.py` — Edge detection heuristic
- `src/gfiat/classifiers/ensemble.py` — Voting ensemble combining heuristics
- `tests/test_classify.py` — Unit tests for classifier
- `tests/fixtures/classify/` — Test images (rock, logo, chart samples)

## Dependencies
- Image extraction module must be complete (provides manifest format)
- PIL/Pillow for image loading
- NumPy for array operations
- scikit-image for advanced image analysis

## Out of Scope (Future)
- **ML-based classifier** — Start with heuristics, ML model deferred pending accuracy evaluation
- **Training data collection** — Not needed for heuristic approach
- **GPU acceleration** — Heuristics are fast enough on CPU
- **Real-time classification** — Batch processing only for MVP
- **Web UI for manual review** — CLI override config sufficient for MVP

## Acceptance Criteria
- [ ] CLI `python -m src.gfiat.classify ./extracted/` processes all images in directory
- [ ] Each image receives classification: `rock_photo`, `thin_section`, `chart`, `logo`, `diagram`, or `unknown`
- [ ] Each classification includes confidence score between 0.0 and 1.0
- [ ] Rock/core photos identified with >80% accuracy on test dataset
- [ ] Obvious non-photos (logos, charts) filtered with >90% accuracy
- [ ] Manifest updated with `classification` and `classification_confidence` fields
- [ ] Manual override via `--overrides config.json` applies specified classifications
- [ ] Thin section photomicrographs distinguished from core plug photos
- [ ] Graceful handling of corrupted/unreadable images (skip with warning)

## Definition of Done

### Implementation
- [ ] Core classifier module implemented with all heuristics
- [ ] Ensemble voting logic combining heuristic scores
- [ ] Unit tests written and passing (>90% coverage on classifier logic)

### Tools
- [ ] CLI entry point with `--overrides` and `--threshold` options
- [ ] `--dry-run` option to preview classifications without modifying manifest
- [ ] `--verbose` option for debugging heuristic scores

### Documentation
- [ ] Update wiki with classifier usage and heuristic explanations
- [ ] Document override config JSON schema
- [ ] Add tuning guide for classification thresholds

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created with accuracy metrics

### Verification
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes
- Test dataset should include: clear rock photos, logos, charts, diagrams, thin sections, and edge cases
- Edge cases to test: black and white photos, photos with scale bars, heavily annotated core photos
- Force low confidence by using ambiguous images (rock-textured backgrounds, geological diagrams)
- Test override by manually classifying known-misclassified images
- Verify manifest integrity by comparing pre/post classification (only classification fields should change)