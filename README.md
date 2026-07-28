# RCA PDF Extraction Pipeline

A Python pipeline that turns unstructured **Routine Core Analysis (RCA)** PDF
reports — the multi-hundred-page documents that hold subsurface geological
measurements in tables, plots, and free text — into clean, structured data.

Given a report, it (1) classifies every page as a data table or not, and
(2) extracts the tabular core-analysis data into a single consolidated CSV/JSON
with column headers preserved across pages. The bundled example (`W20552`, a
public RCA report of 253 pages) yields **138 samples extracted in 371 ms**.

## What it produces

| Output | File | Description |
|--------|------|-------------|
| **Page classification** | [`data/output/spec/page_classification.json`](data/output/spec/page_classification.json) | Every page labeled: `{"page_39": "table", "page_43": "plot", ...}` |
| **Consolidated table** | [`data/output/spec/full_table_extraction.csv`](data/output/spec/full_table_extraction.csv) | 138 samples × 11 data columns, headers normalized across pages |
| **Pipeline source** | [`src/core_analysis.py`](src/core_analysis.py) | The extraction engine |
| **Extended viewer** | [`data/output/extended/`](data/output/extended/) | SQLite database + extracted images for a web viewer |

---

## Quick Start

```bash
pip install -r requirements.txt
python -m src.core_analysis data/output/extended/W20552_elements.db --output data/output/spec/ --original-headers
```

Pre-computed outputs are committed, so you can inspect results without running.

---

## Output Format

**Page classification** (`data/output/spec/page_classification.json`):
```json
{
  "page_1": "other",
  "page_39": "table",
  "page_40": "table",
  "page_41": "table",
  "page_42": "table",
  "page_43": "plot"
}
```

**Consolidated table** (`data/output/spec/full_table_extraction.csv`):
```
Core Number,Sample Number,Sample Depth feet,Permeability millidarcys to Air,Permeability millidarcys Klinkenberg,Porosity percent Ambient,Porosity percent NCS,Grain Density gm/cc,Fluid Saturations percent Water,Fluid Saturations percent Oil,Fluid Saturations percent Total,Page Number
1,1-1,9580.5,0.0011,0.0003,0.9,0.9,2.7,96.5,1.5,98.1,39
1,1-2(F),9581.5,+,+,1.2,,2.7,76.4,0.8,77.2,39
```

---

## Design note: why not OCR?

This PDF has **embedded text** (not scanned images), so OCR would be the wrong
tool — slower, and in the paid case, expensive — for no gain:

| Approach | Time | Cost | Result |
|----------|------|------|--------|
| **Text extraction** (used) | 371 ms | $0 | Works perfectly |
| Tesseract OCR | ~30 s | $0 | 80× slower, same result |
| OpenAI Vision | ~10 s | ~$0.50/doc | Costs money, same result |

OCR is for scanned documents where the text isn't selectable. The first thing
to check is whether you can extract the embedded text directly — here you can,
which also avoids OCR's failure modes: misread characters (0/O, 1/l, 5/S),
illegible subscripts, scan artifacts, and confidence-threshold tuning.

**Library:** PyMuPDF — a fast C library that extracts text with positional
coordinates. Trade-off noted: it is AGPL-licensed.

---

## Project Structure

```
├── data/output/
│   ├── spec/                        ← structured outputs
│   │   ├── full_table_extraction.csv   ← consolidated table extraction
│   │   ├── page_classification.json    ← per-page classification
│   │   └── header_verification.txt     ← header-consistency proof
│   └── extended/                    ← database + viewer artifacts
│       ├── W20552_elements.db       ← SQLite database (224K elements)
│       └── W20552_images/           ← extracted images (468 files)
├── src/
│   └── core_analysis.py             ← main pipeline
├── tests/                           ← 44 unit tests
├── docs/wiki/                       ← detailed documentation
└── requirements.txt                 ← dependencies (PyMuPDF, Flask, Click)
```

---

## Documentation

- [Validation](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Validation) — acceptance criteria and how each is met
- [Architecture](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Architecture) — design decisions and trade-offs
- [Performance](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Performance) — benchmarks and scalability
- [Extensions](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Extensions) — database approach and web viewer

---

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for non-commercial use; commercial use requires a license.

The bundled `W20552` report is public Routine Core Analysis data used here as a
demonstration dataset.
