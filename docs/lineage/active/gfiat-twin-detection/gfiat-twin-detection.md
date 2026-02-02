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
