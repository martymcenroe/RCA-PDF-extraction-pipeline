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
