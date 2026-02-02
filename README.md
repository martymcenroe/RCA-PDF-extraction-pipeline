# RCA PDF Extraction Pipeline

## Deliverables

| Deliverable | File | Description |
|-------------|------|-------------|
| **Page Classification** | [`data/output/spec/page_classification.json`](data/output/spec/page_classification.json) | Dict of all 253 pages: `{"page_39": "table", ...}` |
| **Full Table Extraction** | [`data/output/spec/full_table_extraction.csv`](data/output/spec/full_table_extraction.csv) | 138 samples with 11 data columns |
| **Source Code** | [`src/core_analysis.py`](src/core_analysis.py) | Extraction pipeline |
| **Extended (Viewer)** | [`data/output/extended/`](data/output/extended/) | Database + images for web viewer |

**Results:** 4 table pages identified (39-42), 138 samples extracted in 371ms.

---

## Quick Start

```bash
pip install -r requirements.txt
python -m src.core_analysis data/output/extended/W20552_elements.db --output data/output/spec/ --original-headers
```

Output files are already included in the repo - no need to run unless verifying.

---

## Output Format

**Page Classification** (`data/output/spec/page_classification.json`):
```json
{
  "page_1": "other",
  "page_39": "table",
  "page_40": "table",
  "page_41": "table",
  "page_42": "table",
  "page_43": "plot",
  ...
}
```

**Full Table Extraction** (`data/output/spec/full_table_extraction.csv`):
```
Core Number,Sample Number,Sample Depth feet,Permeability millidarcys to Air,Permeability millidarcys Klinkenberg,Porosity percent Ambient,Porosity percent NCS,Grain Density gm/cc,Fluid Saturations percent Water,Fluid Saturations percent Oil,Fluid Saturations percent Total,Page Number
1,1-1,9580.5,0.0011,0.0003,0.9,0.9,2.7,96.5,1.5,98.1,39
1,1-2(F),9581.5,+,+,1.2,,2.7,76.4,0.8,77.2,39
...
```

---

## Why Not OCR?

This PDF has **embedded text** (not scanned images), so OCR would be overkill:

| Approach | Time | Cost | Result |
|----------|------|------|--------|
| **Text extraction** (used) | 371 ms | $0 | Works perfectly |
| Tesseract OCR | ~30 s | $0 | 80x slower, same result |
| OpenAI Vision | ~10 s | ~$0.50/doc | Costs money, same result |

OCR is for scanned documents where text isn't selectable. Always check if you can just extract the text first.

**Problems we avoid by not using OCR:**
- Misread characters (0 vs O, 1 vs l, 5 vs S)
- Small text illegibility (footnotes, subscripts)
- Scan artifacts from dirty glass or paper creases
- Confidence thresholds and error handling

**Library:** PyMuPDF - fast C library, extracts text with positions. Trade-off: AGPL license.

---

## Project Structure

```
├── data/output/
│   ├── spec/                        ← ASSIGNMENT DELIVERABLES
│   │   ├── full_table_extraction.csv   ← Part 2: Table extraction output
│   │   ├── page_classification.json    ← Part 1: Page classification output
│   │   └── header_verification.txt     ← Header consistency proof
│   └── extended/                    ← DATABASE APPROACH + VIEWER
│       ├── W20552_elements.db       ← SQLite database (224K elements)
│       └── W20552_images/           ← Extracted images (468 files)
├── src/
│   └── core_analysis.py             ← MAIN PIPELINE
├── tests/                           ← 44 unit tests
├── docs/wiki/                       ← Detailed documentation
└── requirements.txt                 ← Dependencies (PyMuPDF, Flask, Click)
```

---

## Documentation

- [Wiki: Requirements Analysis](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Assignment-Requirements) - How requirements were met
- [Wiki: Architecture](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Architecture) - Design decisions
- [Wiki: Performance](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Performance) - Benchmarks
- [Wiki: Extensions](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Extensions) - Database approach & viewer

---

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) - Free for non-commercial use. Commercial use requires a license.
