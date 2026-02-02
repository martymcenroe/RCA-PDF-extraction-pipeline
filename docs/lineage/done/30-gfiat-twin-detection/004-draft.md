# G-FIAT: Twin/Duplicate Detection (Clone Finder)

## User Story
As a **fraud investigator**,
I want **to automatically detect duplicate or manipulated images across geological reports**,
So that **I can identify fraudulent reuse of core photos at different depths or wells**.

## Objective
Implement SIFT-based image comparison to detect potential clone images—including those that have been rotated, scaled, or color-adjusted—and generate a report of flagged pairs for investigation.

## UX Flow

### Scenario 1: Happy Path - Clones Detected
1. User runs `python -m src.gfiat.analyze twins ./extracted/`
2. System loads all SIFT descriptors from extracted images
3. System compares all image pairs using FLANN matching with Lowe's ratio test
4. System flags pairs exceeding 30% match ratio
5. System generates `twins_report.json` with flagged pairs
6. Result: User reviews report showing 3 potential clone pairs with confidence scores

### Scenario 2: No Clones Found
1. User runs `python -m src.gfiat.analyze twins ./extracted/`
2. System compares all image pairs
3. No pairs exceed the match threshold
4. System generates `twins_report.json` with empty findings array
5. Result: User sees "0 potential clones detected" summary

### Scenario 3: Custom Threshold
1. User runs `python -m src.gfiat.analyze twins ./extracted/ --threshold 0.5`
2. System uses 50% match ratio instead of default 30%
3. Fewer pairs are flagged (higher confidence requirement)
4. Result: Report contains only high-confidence matches

### Scenario 4: Large Dataset Warning
1. User runs twins detection on 500+ images
2. System calculates 124,750 pair comparisons needed
3. System displays warning: "Large dataset: ~125K comparisons. Consider using --fast-prefilter"
4. If pair count exceeds 200,000, system prompts: "This will perform 200K+ comparisons. Continue? [y/N]"
5. User confirms to proceed or re-runs with pHash pre-filtering
6. Result: Analysis completes with progress indication

### Scenario 5: Corrupt Descriptor File
1. User runs twins detection on directory with corrupt `.sift` descriptor file
2. System attempts to load descriptor, catches corruption error
3. System logs warning: "Skipping image_042.sift: descriptor file corrupt or unreadable"
4. System continues processing remaining valid descriptors
5. Result: Report includes `warnings` array listing skipped files

## Requirements

### Image Comparison
1. Load SIFT descriptors from all images in extraction output
2. Compare every unique image pair (A,B where A < B)
3. Use FLANN matcher with k-NN (k=2) for efficient matching
4. Apply Lowe's ratio test with 0.7 threshold to filter weak matches
5. Calculate match ratio: `good_matches / min(keypoints_A, keypoints_B)`

### Clone Detection
1. Flag pairs where match_ratio exceeds configurable threshold (default 30%)
2. Detect identical images (>99% match expected)
3. Detect rotated duplicates (SIFT is rotation-invariant)
4. Detect scaled duplicates (SIFT is scale-invariant)
5. Handle color-adjusted duplicates (SIFT uses grayscale)

### Output Generation
1. Generate `twins_report.json` in output directory
2. Include metadata: timestamp, image count, pair count, threshold used
3. For each flagged pair, include:
   - Image A: path, page number, depth (if extractable from filename)
   - Image B: path, page number, depth (if extractable from filename)
   - Match count (good matches after ratio test)
   - Match ratio (percentage)
   - Confidence score (based on match quality distribution)

### CLI Interface
1. Command: `python -m src.gfiat.analyze twins <input_dir>`
2. Options:
   - `--threshold`: Match ratio threshold (default: 0.30)
   - `--output`: Output directory (default: input_dir)
   - `--fast-prefilter`: Use pHash to reduce comparisons
   - `--verbose`: Show progress and match details
   - `--no-confirm`: Skip confirmation prompt for large datasets

### Safety Limits
1. Display warning when pair count exceeds 100,000 comparisons
2. Require interactive confirmation when pair count exceeds 200,000 comparisons
3. Allow bypass of confirmation via `--no-confirm` flag for scripted/CI usage

## Technical Approach
- **SIFT Descriptors:** Leverage existing extraction pipeline descriptors (128-dim vectors per keypoint)
- **FLANN Matching:** Use OpenCV's FLANN-based matcher with KD-tree index for O(log n) queries
- **Lowe's Ratio Test:** Filter matches where best distance < 0.7 × second-best distance
- **Match Scoring:** Normalize by minimum keypoint count to handle images of different complexity
- **pHash Pre-filter:** Optional perceptual hash to skip obviously different pairs (Hamming distance > 20)

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No significant system structure changes—adds new analysis module
- [x] **Cost:** O(n²) comparisons could be expensive for large datasets; 100 images = 4,950 pairs (acceptable), 1000 images = 499,500 pairs (needs pre-filtering). Mitigated by confirmation prompt at 200K+ pairs.
- [ ] **Legal/PII:** No—processes already-extracted geological images, no personal data
- [ ] **Safety:** No—read-only analysis, no data modification

## Security Considerations
- Input validation: Only process files from designated extraction directory
- No external network calls—all processing is local
- Output written only to specified output directory

## Files to Create/Modify
- `src/gfiat/analysis/twins.py` — Core twin detection logic and FLANN matching
- `src/gfiat/analysis/__init__.py` — Export twins module
- `src/gfiat/cli/analyze.py` — Add `twins` subcommand
- `tests/test_twins.py` — Unit tests for matching logic
- `tests/fixtures/twins/` — Test images (identical, rotated, scaled, different, corrupt descriptor)

## Dependencies
- Issue #002 (SIFT Feature Extraction) must be completed first—twins detection requires extracted descriptors
- **Note:** If descriptors are missing for an image, log warning and skip (do not attempt re-extraction; that is Issue #002's responsibility)

## Out of Scope (Future)
- **Geometric verification (RANSAC):** Would reduce false positives but adds complexity—defer to enhancement issue
- **Cross-report comparison:** Comparing images across multiple PDFs—separate workflow
- **GPU acceleration:** CUDA-based matching for massive datasets
- **Visual diff output:** Side-by-side image comparison visualization
- **Fallback re-extraction:** If descriptors missing, we skip rather than re-extract (Issue #002 scope)

## Acceptance Criteria
- [ ] Successfully compares all image pairs from extraction output directory
- [ ] Detects identical images with >99% match ratio
- [ ] Detects 90° rotated duplicates (test with manually rotated image)
- [ ] Detects 50% scaled duplicates (test with resized image)
- [ ] Generates valid `twins_report.json` with all required fields
- [ ] Threshold is configurable via `--threshold` flag
- [ ] CLI command `python -m src.gfiat.analyze twins ./extracted/` works
- [ ] Completes 100-image comparison in under 60 seconds on standard dev environment (4-core CPU, 16GB RAM)
- [ ] Handles missing/corrupt descriptor files gracefully with warnings (logs skipped files, continues processing)
- [ ] Displays confirmation prompt when pair count exceeds 200,000

## Definition of Done

### Implementation
- [ ] Core twin detection implemented in `twins.py`
- [ ] FLANN matching with Lowe's ratio test working
- [ ] CLI integration complete
- [ ] Unit tests written and passing (>80% coverage)

### Tools
- [ ] CLI tool documented with `--help`
- [ ] Example usage in module docstring

### Documentation
- [ ] Update wiki with twins detection workflow
- [ ] Add algorithm explanation to technical docs
- [ ] Document threshold tuning guidelines

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/twins-detection/implementation-report.md` created
- [ ] `docs/reports/twins-detection/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Test Fixtures Required
1. **Identical pair:** Same image, different filenames
2. **Rotated pair:** Image A + Image A rotated 90°, 180°, 270°
3. **Scaled pair:** Image A + Image A at 50% and 200% size
4. **Color-adjusted pair:** Image A + Image A with brightness/contrast changes
5. **Different images:** Two genuinely different core photos (should NOT match)
6. **Corrupt descriptor:** Invalid `.sift` file to verify fail-safe behavior

### Manual Testing Steps
```bash
# Basic run
python -m src.gfiat.analyze twins ./test_extracted/

# With custom threshold
python -m src.gfiat.analyze twins ./test_extracted/ --threshold 0.5

# Verify output
cat ./test_extracted/twins_report.json | jq '.findings | length'

# Test large dataset confirmation bypass
python -m src.gfiat.analyze twins ./large_dataset/ --no-confirm
```

### Expected Results
| Test Case | Expected Match Ratio |
|-----------|---------------------|
| Identical | 95-100% |
| Rotated 90° | 70-95% |
| Scaled 50% | 60-90% |
| Color-adjusted | 80-95% |
| Different images | <10% |

## Labels
`algorithm`, `performance`, `fraud-detection`, `analysis`

## Effort Estimate
**Size: M (Medium)** — Algorithmic complexity, FLANN integration, and comprehensive testing requirements.

## Original Brief
# G-FIAT: Twin/Duplicate Detection (Clone Finder)

## Problem

Fraudulent geological reports may reuse the same core photo at different depths or across different wells. A photo labeled "9,000 ft" might be the same sample as "9,050 ft" - just rotated and color-adjusted. We need to detect these "twins" even when manipulated.

## Proposed Solution

Implement SIFT descriptor matching to compare all image pairs and flag potential clones based on keypoint match ratio.

### Core Functionality
- Compare SIFT descriptors between all image pairs
- Use FLANN matcher for efficient approximate nearest neighbor search
- Apply Lowe's ratio test (0.7 threshold) to filter weak matches
- Flag pairs where >30% of keypoints match as potential clones

### Matching Algorithm
```
For each image pair (A, B):
  1. Load SIFT descriptors
  2. Run FLANN k-NN matching (k=2)
  3. Apply Lowe's ratio test: keep if m.distance < 0.7 * n.distance
  4. Calculate match_ratio = good_matches / min(keypoints_A, keypoints_B)
  5. If match_ratio > 0.30, flag as CLONE
```

### Output Format
- JSON report of flagged pairs with:
  - Image A path, page, depth (if extractable)
  - Image B path, page, depth
  - Match count and ratio
  - Confidence score

## Acceptance Criteria

- [ ] Compare all image pairs from extraction output
- [ ] Detect identical images (should show ~100% match)
- [ ] Detect rotated duplicates (test with manually rotated image)
- [ ] Detect scaled duplicates (test with resized image)
- [ ] Generate `twins_report.json` with flagged pairs
- [ ] Configurable threshold (default 30%)
- [ ] CLI: `python -m src.gfiat.analyze twins ./extracted/`

## Technical Considerations

- O(n^2) comparison - 100 images = 4,950 pairs (manageable)
- For larger datasets, use pHash pre-filter to reduce pairs
- FLANN is approximate - may miss some matches (acceptable tradeoff)
- Consider geometric verification (RANSAC) to reduce false positives
- Depth information may be in filename or require OCR from PDF