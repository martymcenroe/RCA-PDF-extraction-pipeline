# Assignment Requirements

## Audit Results

| Req | Name | Status | Message |
|-----|------|--------|---------|
| F1 | Classification output exists | PASS | Found 253 page classifications |
| F2 | Table pages identified | PASS | Found 4 table pages |
| F3 | Non-table pages identified | PASS | Found 249 non-table pages |
| F4 | Extraction matches classification | PASS | All extracted pages (39, 40, 41, 42) are classified as table |
| F5 | All tables extracted | PASS | Extracted 138 rows (expected 138) |
| F6 | Consolidated output exists | PASS | Both CSV and JSON outputs exist |
| F7 | Output format correct | PASS | Formats: CSV, JSON |
| F8 | Column headers preserved | PASS | Headers match PDF (7 patterns found) |
| F9 | Header variations handled | PASS | Headers verified across pages 39, 40, 41, 42 |
| Q1 | Code is modular | WARN | Multiple modules in src/ |
| Q2 | Code is clean | PASS | Pylint score: 9.31/10 |
| Q3 | Solution loops efficiently | PASS | Processing time: 359ms for 253 pages |
| Q4 | Noise handled | WARN | Minor noise (Page Number column) |
| Q5 | Tool selection explained | PASS | Tools mentioned: pymupdf, tesseract, openai |
| Q6 | Trade-offs documented | PASS | Trade-off discussion found in README.md |
| D1 | Source code provided | PASS | Found 7 Python files in src/ |
| D2 | README exists | PASS | README.md exists |
| D3 | README explains approach | PASS | Approach explanation found |
| D4 | README has run instructions | PASS | Run instructions with code blocks found |

**Summary: 17 PASS, 2 WARN, 0 FAIL, 0 BLOCKER**

---

## Column Headers (Exact from PDF)

| # | Header |
|---|--------|
| 1 | Core Number |
| 2 | Sample Number |
| 3 | Sample Depth, feet |
| 4 | Permeability, millidarcys to Air |
| 5 | Permeability, millidarcys Klinkenberg |
| 6 | Porosity, percent Ambient |
| 7 | Porosity, percent NCS |
| 8 | Grain Density, gm/cc |
| 9 | Fluid Saturations, percent Water |
| 10 | Fluid Saturations, percent Oil |
| 11 | Fluid Saturations, percent Total |
| 12 | Page Number *(added by pipeline)* |

## Output Files

| File | Description |
|------|-------------|
| `page_classification.json` | `{"page_39": "table", "page_1": "other", ...}` |
| `full_table_extraction.csv` | 138 samples with 12 columns |
| `header_verification.txt` | Verifies headers match across pages 39-42 |

## Special Cases Handled

| Case | PDF Marker | Output |
|------|------------|--------|
| Below detection limit | `<0.0001` | Preserved, replicated to both permeability columns |
| Fractured sample | `+` | Preserved, replicated to both permeability columns |
| No saturation data | `**` | Preserved, replicated to all three saturation columns |
| Fracture indicator | `(F)` or `(f)` | Preserved in Sample Number |

## See Also

- [Architecture](./Architecture) - Pipeline design and tool selection
- [Clean-Code](./Clean-Code) - Pylint score: 9.31/10
- [Security](./Security) - Bandit scan results, CSV injection protection
