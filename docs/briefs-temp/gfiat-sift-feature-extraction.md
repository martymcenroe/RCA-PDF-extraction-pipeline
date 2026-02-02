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
