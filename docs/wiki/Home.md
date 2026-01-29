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

Outputs are organized into two directories:

### `data/output/spec/` - Assignment Deliverable

| File | Format | Contents |
|------|--------|----------|
| `core_analysis.csv` | CSV | 138 sample records with 11 data columns |
| `core_analysis.json` | JSON | Page classifications + sample data |

### `data/output/extended/` - Database Approach + Viewer

| File | Format | Contents |
|------|--------|----------|
| `core_analysis.csv` | CSV | Same data, produced via database pipeline |
| `core_analysis.json` | JSON | Same data, produced via database pipeline |
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
