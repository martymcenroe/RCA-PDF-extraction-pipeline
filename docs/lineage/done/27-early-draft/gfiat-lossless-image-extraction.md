# G-FIAT: Lossless PDF Image Extraction

## Problem

PDF rendering destroys forensic evidence. Taking screenshots or converting pages to JPGs introduces new compression artifacts that mask the original manipulation signatures. To detect image fraud, we need the raw image bytes exactly as embedded in the PDF.

Current extraction approaches re-encode images, making forensic analysis unreliable.

## Proposed Solution

Build a lossless image extraction module using PyMuPDF that bypasses the PDF rendering layer and accesses raw binary streams of image objects (XObjects).

### Core Functionality
- Extract images from PDFs without re-encoding
- Access raw XObject binary streams directly
- Preserve original compression artifacts (JPEG, JBIG2, TIFF)
- Generate JSON manifest linking each image to source page and bounding box

### Dependencies (Poetry)
- `pymupdf` (already installed)
- `opencv-python-headless`
- `imagehash`
- `numpy`
- `scipy`
- `matplotlib`

### Output Format
- Directory of raw image files (preserving original format)
- `manifest.json` with structure:
  ```json
  {
    "source_pdf": "path/to/file.pdf",
    "extraction_date": "ISO8601",
    "images": [
      {
        "id": "img_001",
        "page": 1,
        "bbox": [x0, y0, x1, y1],
        "format": "jpeg",
        "file": "img_001.jpg",
        "xref": 42
      }
    ]
  }
  ```

## Acceptance Criteria

- [ ] Extract all images from `docs/context/init/W20552.pdf` without re-encoding
- [ ] Preserve original image format (JPEG stays JPEG, not converted to PNG)
- [ ] Generate manifest.json with page/bbox metadata for each image
- [ ] Verify extracted images are byte-identical to PDF XObject streams
- [ ] CLI: `python -m src.gfiat.extract path/to/pdf.pdf --output-dir ./output`

## Technical Considerations

- PyMuPDF's `get_images()` returns XRef numbers for raw stream access
- Use `doc.extract_image(xref)` to get raw bytes without re-encoding
- Some PDFs use inline images - may need special handling
- JBIG2 images require external decoder if present
