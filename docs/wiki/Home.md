# RCA PDF Extraction Pipeline

A Python pipeline for extracting structured data from Routine Core Analysis (RCA) PDF documents.

## Navigation

| Page | Description |
|------|-------------|
| [[Requirements]] | Assignment requirements and deliverables |
| [[Architecture]] | Design decisions and trade-offs |
| [[Code-Quality]] | Modularity metrics and analysis |
| [[Security]] | Vulnerability scanning and controls |
| [[Performance]] | Benchmarks and scalability analysis |
| [[Extensions]] | Database approach and web viewer |

## Quick Start

### Option A: pip (for graders/Docker)

```bash
pip install -r requirements.txt
python -m src.core_analysis data/output/extended/W20552_elements.db --output data/output/spec/ --original-headers
```

### Option B: poetry (for development)

```bash
poetry install
poetry run python -m src.core_analysis data/output/extended/W20552_elements.db --output data/output/spec/ --original-headers
```

### Option C: Installed package

```bash
poetry install
core-analysis docs/context/init/W20552.pdf --output data/output/
```

## Output

Outputs are organized into two directories:

### `data/output/spec/` - Assignment Deliverable

| File | Format | Contents |
|------|--------|----------|
| `page_classification.json` | JSON | Part 1: Page classifications |
| `full_table_extraction.csv` | CSV | Part 2: 138 sample records with 11 data columns |

### `data/output/extended/` - Database Approach + Viewer

| File | Format | Contents |
|------|--------|----------|
| `page_classification.json` | JSON | Part 1: Page classifications |
| `full_table_extraction.csv` | CSV | Part 2: Same extraction data |
| `W20552_elements.db` | SQLite | 224K extracted PDF elements |
| `W20552_images/` | PNG files | 468 extracted images |

See [[Extensions]] for viewer usage.

## Results Summary

For `W20552.pdf` (253 pages, 16.3 MB):

| Metric | Value |
|--------|-------|
| Processing time | 359 ms |
| Table pages identified | 4 (pages 39-42) |
| Plot pages | 3 (pages 43-45) |
| Samples extracted | 138 |
| Depth range | 9,580.50 - 9,727.50 feet |
