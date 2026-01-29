# RCA PDF Extraction Pipeline

A Python pipeline for extracting structured data from Routine Core Analysis (RCA) PDF documents.

## Navigation

| Page | Description |
|------|-------------|
| [[Requirements]] | Assignment requirements and deliverables |
| [[Architecture]] | Design decisions and trade-offs |
| [[Performance]] | Benchmarks and scalability analysis |
| [[Extensions]] | Database approach and web viewer |

## Quick Start

### Option A: pip (for graders/Docker)

```bash
pip install -r requirements.txt
python src/core_analysis_minimal.py docs/context/init/W20552.pdf --output data/output/
```

### Option B: poetry (for development)

```bash
poetry install
poetry run python src/core_analysis_minimal.py docs/context/init/W20552.pdf --output data/output/
```

### Option C: Installed package

```bash
poetry install
core-analysis docs/context/init/W20552.pdf --output data/output/
```

## Output

The pipeline produces two files:

| File | Format | Contents |
|------|--------|----------|
| `core_analysis_minimal.csv` | CSV | 138 sample records with 11 data columns |
| `core_analysis_minimal.json` | JSON | Page classifications + sample data |

## Results Summary

For `W20552.pdf` (253 pages, 16.3 MB):

| Metric | Value |
|--------|-------|
| Processing time | 359 ms |
| Table pages identified | 4 (pages 39-42) |
| Plot pages | 3 (pages 43-45) |
| Samples extracted | 138 |
| Depth range | 9,580.50 - 9,727.50 feet |
