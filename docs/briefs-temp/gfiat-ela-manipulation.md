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
