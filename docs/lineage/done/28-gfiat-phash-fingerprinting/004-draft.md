# G-FIAT: Perceptual Hash (pHash) Fingerprinting

## User Story
As a forensic geology analyst,
I want to fingerprint extracted images using perceptual hashing,
So that I can rapidly identify near-duplicate images before running expensive SIFT analysis.

## Objective
Implement perceptual hashing to generate similarity-resistant fingerprints for extracted images, enabling fast pre-filtering of potential clone pairs.

## UX Flow

### Scenario 1: Happy Path - Fingerprint Extracted Images
1. User runs `python -m src.gfiat.fingerprint --method phash ./extracted/`
2. System loads all images from the extracted directory
3. System generates 64-bit pHash for each image
4. System updates `manifest.json` with `phash` field per image entry
5. System outputs summary: "Fingerprinted 47 images in 1.2s"
6. Result: manifest.json contains phash hex strings for all images

### Scenario 2: Find Near-Duplicate Pairs
1. User runs `python -m src.gfiat.fingerprint --method phash --compare ./extracted/`
2. System loads pHash values from manifest.json
3. System computes Hamming distance between all pairs
4. System flags pairs with distance < 10 as potential matches
5. Result: JSON output listing candidate pairs with distances

### Scenario 3: Corrupted Image Handling
1. User runs fingerprinting on directory containing a corrupted image
2. System fails to process `image_042.png`
3. System logs warning: "Skipping image_042.png: Unable to decode image"
4. System continues processing remaining images
5. Result: manifest.json updated with phash for valid images, corrupted images marked with `"phash": null`

### Scenario 4: Empty or Missing Directory
1. User runs `python -m src.gfiat.fingerprint --method phash ./nonexistent/`
2. System detects directory does not exist
3. System outputs error: "Error: Directory './nonexistent/' not found"
4. Result: Exit code 1, no changes to filesystem

## Requirements

### Hash Generation
1. Generate 64-bit perceptual hash using DCT-based algorithm
2. Store hash as 16-character hexadecimal string
3. Support PNG, JPEG, TIFF, and BMP image formats
4. Handle grayscale and color images uniformly

### Manifest Integration
1. Add `phash` field to each image entry in manifest.json
2. Preserve all existing manifest fields when updating
3. Support incremental updates (only hash new/modified images)
4. Record timestamp of fingerprinting operation

**Schema Change Example:**
```json
{
  "images": [
    {
      "path": "extracted/image_001.png",
      "source_page": 5,
      "dimensions": [800, 600],
      "format": "PNG",
      "phash": "a4e3b2c1d5f60789",
      "phash_timestamp": "2025-01-15T14:32:00Z"
    }
  ]
}
```

### Similarity Comparison
1. Compute Hamming distance between hash pairs
2. Configurable threshold (default: 10 bits)
3. Output candidate pairs sorted by distance (ascending)
4. Support JSON output format for pipeline integration

### Performance
1. Process 100 images in under 5 seconds
2. Use batch processing for memory efficiency
3. Support parallel processing with `--workers` flag

## Technical Approach
- **Hash Algorithm:** Use `imagehash` library's `phash()` function implementing DCT-based perceptual hashing
- **Image Loading:** PIL/Pillow for format handling and preprocessing
- **Storage:** Hex string representation in manifest.json (16 chars = 64 bits)
- **Comparison:** Bitwise XOR + popcount for Hamming distance calculation
- **Pipeline Position:** Runs after image extraction, before Twin Detection SIFT analysis

### How pHash Works (Reference)
1. Resize image to 32x32 pixels
2. Convert to grayscale
3. Apply Discrete Cosine Transform (DCT)
4. Retain top-left 8x8 DCT coefficients (low frequencies)
5. Compute median of coefficients
6. Generate 64-bit hash: 1 if coefficient > median, else 0

## Risk Checklist
*Quick assessment - details go in LLD. Check all that apply and add brief notes.*

- [ ] **Architecture:** No significant changes - adds new module alongside existing extraction pipeline
- [ ] **Cost:** Minimal - CPU-only operation, no external API calls
- [ ] **Legal/PII:** No - processes already-extracted images, no new data collection
- [ ] **Safety:** Low risk - read-only on images, atomic writes to manifest.json with backup

## Security Considerations
- No external network calls required
- Operates only on local filesystem within specified directory
- No elevation of privileges needed
- Input validation on file paths to prevent directory traversal

## Files to Create/Modify
- `src/gfiat/fingerprint.py` — Core pHash generation and comparison logic
- `src/gfiat/fingerprint/__init__.py` — Module initialization
- `src/gfiat/fingerprint/phash.py` — pHash algorithm implementation
- `src/gfiat/fingerprint/comparison.py` — Hamming distance and pair matching
- `src/gfiat/manifest.py` — Add fingerprint field support (modify existing)
- `tests/test_fingerprint.py` — Unit tests for fingerprinting module
- `tests/fixtures/fingerprint/` — Test images for hash verification

## Dependencies
- **Depends on #TBD** — Image extraction module must be complete (provides input images and manifest.json). *Link to be updated when extraction issue is created.*
- `imagehash` library (add to requirements.txt)
- `Pillow` library (likely already present)

## Out of Scope (Future)
- **Rotation-invariant hashing** — pHash is rotation-sensitive by design; SIFT handles rotated clones
- **dHash and aHash ensemble** — Defer to future enhancement issue
- **GPU acceleration** — Not needed for target performance
- **Database storage** — Manifest.json sufficient for MVP; database for large-scale deployments later
- **Perceptual hash for video frames** — Document-focused MVP

## Acceptance Criteria
- [ ] Generate valid 64-bit pHash for PNG, JPEG, TIFF, and BMP images
- [ ] Store pHash as hex string in manifest.json under each image entry
- [ ] Detect identical images (Hamming distance = 0) with 100% accuracy
- [ ] Detect near-identical images (crops, minor edits) with Hamming distance < 10
- [ ] Process 100 images in under 5 seconds on standard hardware
- [ ] CLI command `python -m src.gfiat.fingerprint --method phash ./extracted/` works
- [ ] Gracefully handle corrupted/unreadable images without crashing
- [ ] JSON output of candidate pairs includes image paths and distances
- [ ] Incremental mode only processes images without existing phash

## Definition of Done

### Implementation
- [ ] Core pHash generation implemented
- [ ] Hamming distance comparison implemented
- [ ] Manifest.json integration complete
- [ ] CLI interface functional
- [ ] Unit tests written and passing (>90% coverage)

### Tools
- [ ] CLI tool documented with `--help` output
- [ ] Example usage in module docstring

### Documentation
- [ ] Update wiki with Fingerprinting module documentation
- [ ] Add algorithm explanation to technical docs
- [ ] Update README.md with new CLI command
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run 0809 Security Audit - PASS
- [ ] Run 0817 Wiki Alignment Audit - PASS

## Testing Notes

### Test Cases
1. **Identical images:** Same image copied twice → Hamming distance = 0
2. **Minor crop:** Image with 5% border crop → Hamming distance < 5
3. **JPEG compression:** Same image at quality 95 vs 50 → Hamming distance < 10
4. **Different images:** Completely different photos → Hamming distance > 20
5. **Homogeneous textures:** Two different uniform gray images → May produce false positive (document limitation)
6. **Corrupted image:** Truncated/malformed image file → Graceful skip with `"phash": null`

### Test Fixtures Needed
- Pair of identical images
- Original + cropped version
- Original + JPEG-compressed version
- Original + brightness-adjusted version
- Two completely different images
- Corrupted image file (truncated)
- Empty/zero-byte file

### Performance Testing
```bash
# Generate 100 test images and time fingerprinting
time python -m src.gfiat.fingerprint --method phash ./test_images_100/
# Should complete in < 5 seconds
```

---

**Labels:** `feature`, `algorithm`, `python`