# G-FIAT: Perceptual Hash (pHash) Fingerprinting

## Problem

Comparing images byte-by-byte is useless for detecting clones - any minor edit defeats it. We need a fingerprinting method that produces similar hashes for visually similar images, enabling rapid pre-filtering before expensive SIFT analysis.

## Proposed Solution

Implement perceptual hashing using the `imagehash` library for fast "near-exact match" filtering.

### Core Functionality
- Generate pHash for each extracted image
- Store hashes in a lightweight format (hex string)
- Compare hashes using Hamming distance
- Flag pairs below threshold (e.g., Hamming distance < 10) as potential matches

### How pHash Works
1. Resize image to 32x32
2. Convert to grayscale
3. Apply DCT (Discrete Cosine Transform)
4. Keep top-left 8x8 DCT coefficients
5. Compute median and generate 64-bit hash

### Integration Point
- Runs after image extraction
- Updates manifest.json with `phash` field per image
- Provides fast pre-filter for Twin Detection module

## Acceptance Criteria

- [ ] Generate pHash for all images in extraction output
- [ ] Store hashes in manifest.json
- [ ] Detect identical images (Hamming distance = 0)
- [ ] Detect near-identical images (Hamming distance < 10)
- [ ] Process 100 images in under 5 seconds
- [ ] CLI: `python -m src.gfiat.fingerprint --method phash ./extracted/`

## Technical Considerations

- pHash is rotation-sensitive - won't catch rotated clones (that's SIFT's job)
- Good for exact duplicates and minor crops
- False positive rate increases with very homogeneous images (e.g., uniform rock textures)
- Consider also implementing dHash and aHash for ensemble comparison
