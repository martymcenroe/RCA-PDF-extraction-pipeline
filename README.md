# RCA PDF Extraction Pipeline

## Deliverables

| Deliverable | File | Description |
|-------------|------|-------------|
| **Page Classification** | [`data/output/spec/core_analysis.json`](data/output/spec/core_analysis.json) | Dict of all 253 pages: `{"page_39": "table", ...}` |
| **Table Extraction** | [`data/output/spec/core_analysis.csv`](data/output/spec/core_analysis.csv) | 138 samples with 11 data columns |
| **Source Code** | [`src/core_analysis_minimal.py`](src/core_analysis_minimal.py) | Single-file pipeline (~300 lines) |
| **Extended (Viewer)** | [`data/output/extended/`](data/output/extended/) | Database + images for web viewer |

**Results:** 4 table pages identified (39-42), 138 samples extracted in 371ms.

---

## Quick Start

```bash
pip install -r requirements.txt
python src/core_analysis_minimal.py docs/context/init/W20552.pdf --output data/output/
```

Output files are already included in the repo - no need to run unless verifying.

---

## Output Format

**Page Classification** (`data/output/spec/core_analysis.json`):
```json
{
  "classifications": {
    "page_39": "table",
    "page_40": "table",
    "page_41": "table",
    "page_42": "table",
    "page_43": "plot",
    "page_1": "cover",
    ...
  }
}
```

**Table Extraction** (`data/output/spec/core_analysis.csv`):
```
core_number,sample_number,depth_feet,permeability_air_md,permeability_klink_md,porosity_ambient_pct,porosity_ncs_pct,grain_density_gcc,saturation_water_pct,saturation_oil_pct,saturation_total_pct,page_number,notes
1,1-1,9580.5,0.0011,0.0003,0.9,0.9,2.7,96.5,1.5,98.1,39,
1,1-2(F),9581.5,,,1.2,,2.7,76.4,0.8,77.2,39,fracture
...
```

---

## Tool Selection & Trade-offs

| Tool | Why Chosen | Alternative | Trade-off |
|------|------------|-------------|-----------|
| **PyMuPDF** | Fast C library, extracts text + positions | pdfplumber, PyPDF2 | AGPL license |
| **Text extraction** | PDF has embedded text (not scanned) | OCR (Tesseract, Vision API) | Won't work on scanned PDFs |

**Cost/Latency:**

| Approach | Time | Cost | When to Use |
|----------|------|------|-------------|
| Text extraction (used) | 371 ms | $0 | Embedded text PDFs |
| Tesseract OCR | ~30 s | $0 | Scanned PDFs, no budget |
| OpenAI Vision | ~10 s | ~$0.50/doc | Scanned PDFs, need accuracy |

---

## Project Structure

```
├── data/output/
│   ├── spec/                        ← ASSIGNMENT DELIVERABLES
│   │   ├── core_analysis.csv        ← Table extraction output
│   │   └── core_analysis.json       ← Page classification output
│   └── extended/                    ← DATABASE APPROACH + VIEWER
│       ├── W20552_elements.db       ← SQLite database (224K elements)
│       └── W20552_images/           ← Extracted images (468 files)
├── src/
│   └── core_analysis_minimal.py     ← MAIN PIPELINE
├── tests/                           ← 18 unit tests
├── docs/wiki/                       ← Detailed documentation
└── requirements.txt                 ← Dependencies (PyMuPDF only)
```

---

## Documentation

- [Wiki: Requirements Analysis](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Requirements) - How requirements were met
- [Wiki: Architecture](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Architecture) - Design decisions
- [Wiki: Performance](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Performance) - Benchmarks
- [Wiki: Extensions](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Extensions) - Database approach & viewer

---

## License

MIT
