# RCA PDF Extraction Pipeline

A Python pipeline that extracts structured data from Routine Core Analysis (RCA) PDF documents.

**Deliverables:**
1. Page Classification - Identifies table pages vs other content
2. Table Extraction - Consolidated CSV/JSON with 138 samples

## Quick Start

### pip (recommended for graders)

```bash
pip install -r requirements.txt
python src/core_analysis_minimal.py docs/context/init/W20552.pdf --output data/output/
```

### poetry (for development)

```bash
poetry install
poetry run python src/core_analysis_minimal.py docs/context/init/W20552.pdf --output data/output/

# Or use the installed command
core-analysis docs/context/init/W20552.pdf --output data/output/
```

## Output

| File | Description |
|------|-------------|
| `core_analysis_minimal.csv` | 138 samples, 11 data columns |
| `core_analysis_minimal.json` | Page classifications + sample data |

**Sample CSV row:**
```
core_number,sample_number,depth_feet,permeability_air_md,...
1,1-1,9580.50,0.0011,0.0003,0.9,0.9,2.70,96.5,1.5,98.1,39,
```

**Page classification:**
```json
{"page_39": "table", "page_40": "table", "page_43": "plot", "page_1": "cover", ...}
```

## Results

| Metric | Value |
|--------|-------|
| Processing time | 359 ms |
| Table pages | 4 (pages 39-42) |
| Samples extracted | 138 |
| Depth range | 9,580.50 - 9,727.50 ft |

## Documentation

| Document | Contents |
|----------|----------|
| [Wiki Home](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki) | Navigation and quick start |
| [Requirements](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Requirements) | Assignment requirements and deliverables |
| [Architecture](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Architecture) | Design decisions and trade-offs |
| [Performance](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Performance) | Benchmarks and scalability |
| [Extensions](https://github.com/martymcenroe/RCA-PDF-extraction-pipeline/wiki/Extensions) | Database approach and web viewer |

## Project Structure

```
src/
├── core_analysis_minimal.py   # Main pipeline (RECOMMENDED)
├── core_analysis.py           # Database-backed alternative
└── elementizer/               # PDF element toolkit (extension)

data/output/
├── core_analysis_minimal.csv  # Output
└── core_analysis_minimal.json
```

## Dependencies

**Core (required):**
- PyMuPDF >= 1.24.0

**Extended (optional):**
- flask >= 3.0.0 (web viewer)
- click >= 8.0.0 (elementizer CLI)

## Why Text Extraction vs OCR?

| Approach | Time | Cost | Accuracy |
|----------|------|------|----------|
| Text extraction (used) | 359 ms | $0 | 100% |
| Tesseract OCR | ~30 s | $0 | 95-99% |
| OpenAI Vision | ~10 s | ~$0.50 | 98-99% |

The PDF has embedded extractable text. OCR would add latency and cost with no accuracy benefit.

## License

MIT
