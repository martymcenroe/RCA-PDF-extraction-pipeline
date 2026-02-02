# Issue #30: G-FIAT: Twin/Duplicate Detection (Clone Finder)

# G-FIAT: Twin/Duplicate Detection (Clone Finder)

## User Story
As a **fraud investigator**,
I want **to automatically detect duplicate or manipulated images across geological reports**,
So that **I can identify fraudulent reuse of core photos at different depths or wells**.

## Objective
Implement SIFT-based image comparison to detect potential clone imagesâ€”including those that have been rotated, scaled, or color-adjustedâ€”and generate a report of flagged pairs for investigation.

## UX Flow

### Scenario 1: Happy Path - Clones Detected
1. User runs `python -m src.gfiat.analyze twins ./extracted/`
2. System loads all SIFT descriptors from extracted images
3. System builds FLANN KD-tree index from all descriptors
4. System queries each image against the index using Lowe's ratio test
5. System filters out self-matches (where Image A path == Image B path)
6. System flags pairs exceeding 30% match ratio
7. System generates `twins_report.json` with flagged pairs
8. Result: User reviews report showing 3 potential clone pairs with confidence scores

### Scenario 2: No Clones Found
1. User runs `python -m src.gfiat.analyze twins ./extracted/`
2. System indexes and queries all images
3. System filters out self-matches
4. No pairs exceed the match threshold
5. System generates `twins_report.json` with empty findings array
6. Result: User sees "0 potential clones detected" summary

### Scenario 3: Custom Threshold
1. User runs `python -m src.gfiat.analyze twins ./extracted/ --threshold 0.5`
2. System uses 50% match ratio instead of default 30%
3. Fewer pairs are flagged (higher confidence requirement)
4. Result: Report contains only high-confidence matches

### Scenario 4: Large Dataset Warning
1. User runs twins detection on 500+ images
2. System calculates estimated comparison count
3. System displays warning: "Large dataset: 500 images to process. Consider using --fast-prefilter"
4. If image count exceeds 1,000, system prompts: "This dataset contains 1000+ images. Continue? [y/N]"
5. User confirms to proceed or re-runs with pHash pre-filtering
6. Result: Analysis completes with progress indication (images processed)

### Scenario 5: Corrupt Descriptor File
1. User runs twins detection on directory with corrupt `.sift` descriptor file
2. System attempts to load descriptor, catches corruption error
3. System logs warning: "Skipping image_042.sift: descriptor file corrupt or unreadable"
4. System continues processing remaining valid descriptors
5. Result: Report includes `warnings` array listing skipped files

### Scenario 6: Mirror/Flip Detection (Negative Test Case)
1. User runs twins detection on directory containing horizontally flipped duplicate
2. System attempts SIFT matching (note: SIFT is NOT flip-invariant)
3. Match ratio is typically low (20-50%) due to SIFT limitations
4. Result: Pair may or may not be flagged depending on threshold; this scenario documents detection limits, NOT promised functionality (see Out of Scope)

## Requirements

### Image Comparison (FLANN Indexing Approach)
1. Load SIFT descriptors from all images in extraction output
2. Build a KD-tree index from all descriptors using FLANN
3. Query each image's descriptors against the index for O(log n) lookup per query
4. Use FLANN matcher with k-NN (k=2) for efficient matching
5. Apply Lowe's ratio test with 0.7 threshold to filter weak matches
6. Calculate match ratio: `good_matches / min(keypoints_A, keypoints_B)`
7. **Filter out self-matches:** Exclude pairs where Image A path == Image B path

### Clone Detection
1. Flag pairs where match_ratio exceeds configurable threshold (default 30%)
2. Detect identical images (>99% match expected)
3. Detect rotated duplicates (SIFT is rotation-invariant)
4. Detect scaled duplicates (SIFT is scale-invariant)
5. Handle color-adjusted duplicates (SIFT uses grayscale)

### Output Generation
1. Generate `twins_report.json` in output directory
2. Include metadata: timestamp, image count, threshold used
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
   - `--fast-prefilter`: Use pHash to reduce comparisons (only active when flag is passed)
   - `--verbose`: Show progress and match details
   - `--no-confirm`: Skip confirmation prompt for large datasets

### Safety Limits
1. Display warning when image count exceeds 500 images
2. Require interactive confirmation when image count exceeds 1,000 images
3. Allow bypass of confirmation via `--no-confirm` flag for scripted/CI usage

## Technical Approach
- **SIFT Descriptors:** Leverage existing extraction pipeline descriptors (128-dim vectors per keypoint)
- **FLANN Indexing:** Build KD-tree index from all descriptors for O(log n) queries per image, avoiding O(nÂ²) pairwise loops. This is the **mandated approach**â€”do NOT implement brute-force pairwise comparison.
- **Lowe's Ratio Test:** Filter matches where best distance < 0.7 Ã— second-best distance
- **Match Scoring:** Normalize by minimum keypoint count to handle images of different complexity
- **Self-Match Filtering:** Explicitly exclude pairs where both paths resolve to the same file
- **pHash Pre-filter:** Optional perceptual hash (ImageHash library, BSD licenseâ€”verified compatible) activated only via `--fast-prefilter` flag to skip obviously different pairs (Hamming distance > 20)

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No significant system structure changesâ€”adds new analysis module
- [x] **Cost:** Large datasets require significant compute; mitigated by FLANN indexing (O(n log n) vs O(nÂ²)) and confirmation prompt at 1,000+ images
- [ ] **Legal/PII:** Noâ€”processes already-extracted geological images, no personal data
- [ ] **Safety:** Noâ€”read-only analysis, no data modification
- [x] **Dependencies:** pHash pre-filter uses `ImageHash` library (BSD licenseâ€”verified compatible)

## Security Considerations
- Input validation: Only process files from designated extraction directory
- No external network callsâ€”all processing is local
- Output written only to specified output directory

## Files to Create/Modify
- `src/gfiat/analysis/twins.py` â€” Core twin detection logic and FLANN indexing
- `src/gfiat/analysis/__init__.py` â€” Export twins module
- `src/gfiat/cli/analyze.py` â€” Add `twins` subcommand
- `tests/test_twins.py` â€” Unit tests for matching logic
- `tests/fixtures/twins/` â€” Test images (identical, rotated, scaled, different, corrupt descriptor, mirrored)
- `pyproject.toml` â€” Add `ImageHash` dependency for optional pHash pre-filter

## Dependencies
- Issue #002 (SIFT Feature Extraction) must be completed firstâ€”twins detection requires extracted descriptors
- **Note:** If descriptors are missing for an image, log warning and skip (do not attempt re-extraction; that is Issue #002's responsibility)
- **External:** `ImageHash` library for optional pHash pre-filter (BSD licenseâ€”verified compatible)

## Out of Scope (Future)
- **Geometric verification (RANSAC):** Would reduce false positives but adds complexityâ€”defer to enhancement issue
- **Cross-report comparison:** Comparing images across multiple PDFsâ€”separate workflow
- **GPU acceleration:** CUDA-based matching for massive datasets
- **Visual diff output:** Side-by-side image comparison visualization
- **Fallback re-extraction:** If descriptors missing, we skip rather than re-extract (Issue #002 scope)
- **Mirror/Flip-specific detection:** SIFT is not flip-invariant; dedicated flip detection deferred to enhancement

## Acceptance Criteria
- [ ] Successfully indexes and queries all images from extraction output directory
- [ ] Filters out self-matches (same file path pairs excluded from results)
- [ ] Detects identical images with >99% match ratio
- [ ] Detects 90Â° rotated duplicates (test with manually rotated image)
- [ ] Detects 50% scaled duplicates (test with resized image)
- [ ] Generates valid `twins_report.json` with all required fields
- [ ] Threshold is configurable via `--threshold` flag
- [ ] CLI command `python -m src.gfiat.analyze twins ./extracted/` works
- [ ] Completes 100-image comparison in under 60 seconds on standard dev environment (4-core CPU, 16GB RAM)
- [ ] Handles missing/corrupt descriptor files gracefully with warnings (logs skipped files, continues processing)
- [ ] Displays confirmation prompt when image count exceeds 1,000

## Definition of Done

### Implementation
- [ ] Core twin detection implemented in `twins.py`
- [ ] FLANN indexing with Lowe's ratio test working
- [ ] Self-match filtering implemented
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
2. **Rotated pair:** Image A + Image A rotated 90Â°, 180Â°, 270Â°
3. **Scaled pair:** Image A + Image A at 50% and 200% size
4. **Color-adjusted pair:** Image A + Image A with brightness/contrast changes
5. **Different images:** Two genuinely different core photos (should NOT match)
6. **Corrupt descriptor:** Invalid `.sift` file to verify fail-safe behavior
7. **Mirror/Flip pair:** Image A + Image A flipped horizontally (to document detection limitsâ€”negative test case)
8. **False positive pair:** Two different images with similar textures (e.g., sand/gravel) to verify Lowe's ratio threshold robustness

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

# Test pHash pre-filter
python -m src.gfiat.analyze twins ./large_dataset/ --fast-prefilter
```

### Expected Results
| Test Case | Expected Match Ratio |
|-----------|---------------------|
| Identical | 95-100% |
| Rotated 90Â° | 70-95% |
| Scaled 50% | 60-90% |
| Color-adjusted | 80-95% |
| Mirror/Flip | 20-50% (limitedâ€”see Out of Scope) |
| Different images | <10% |
| False positive (similar texture) | <30% (should NOT trigger default threshold) |

## Labels
`algorithm`, `performance`, `fraud-detection`, `analysis`

## Effort Estimate
**Size: M (Medium)** â€” Algorithmic complexity, FLANN integration, and comprehensive testing requirements.

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

---

<sub>**Gemini Review:** APPROVED | **Model:** `gemini-3-pro-preview` | **Date:** 2026-02-01 | **Reviews:** 5</sub>
