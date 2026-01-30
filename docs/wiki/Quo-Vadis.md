# Quo Vadis

*"Where are we going?"* - Future directions for this project.

## Current State

The pipeline is **complete and passing all requirements**:
- 17 PASS, 2 WARN, 0 FAIL, 0 BLOCKER
- Pylint score: 9.31/10
- Processing time: 359ms for 253 pages

## Potential Extensions

### High Value / Low Effort

| Extension | Description | Effort |
|-----------|-------------|--------|
| **REST API** | Wrap pipeline in Flask/FastAPI endpoint for integration | Low |
| **Batch CLI** | Process multiple PDFs with glob patterns | Low |
| **Excel Export** | Add .xlsx output option (openpyxl) | Low |

### High Value / Medium Effort

| Extension | Description | Effort |
|-----------|-------------|--------|
| **OCR Fallback** | Detect scanned pages, route to Tesseract | Medium |
| **Confidence Scoring** | Score extraction confidence per row | Medium |
| **Schema Validation** | Validate output against JSON Schema | Medium |

### Research / Exploration

| Extension | Description | Notes |
|-----------|-------------|-------|
| **LLM-Assisted Extraction** | Use GPT-4 Vision for ambiguous tables | Cost: ~$0.50/doc |
| **Template Learning** | Learn table structure from examples | Would generalize to new formats |
| **Multi-Document Correlation** | Cross-reference data across reports | Useful for trend analysis |

## The Bigger Vision: Global Data Ingestion

The current pipeline extracts data from a single PDF. The larger vision is an **Automated Subsurface Data Ingestion Pipeline** that harvests RCA reports from global geological repositories to build a high-diversity training dataset.

### Target Data Sources

| Source | Region | Access | Notes |
|--------|--------|--------|-------|
| USGS CRC | USA | Public | Library Number lookup, bulk download |
| NDIC | North Dakota | Subscription | Monolithic well files |
| University Lands | Texas | Public | API number search |
| UK NDR | UK Continental Shelf | Public | 2,000+ wells, 43GB bulk package |
| DISKOS | Norway | Public | Volve field open dataset |
| WAPIMS | Western Australia | Public | Basket batch download |
| AER | Alberta, Canada | Public | Non-confidential wells |

### Architecture Concept

```
┌─────────────────┐
│ Core Controller │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    ▼         ▼        ▼        ▼        ▼
┌───────┐ ┌──────┐ ┌─────┐ ┌──────┐ ┌─────┐
│ USGS  │ │ NDIC │ │ NDR │ │DISKOS│ │ ... │
│Module │ │Module│ │Module│ │Module│ │     │
└───────┘ └──────┘ └─────┘ └──────┘ └─────┘
```

Each module handles site-specific: authentication, search logic, navigation, and download.

### Deliverables

- Standardized storage: `/data/raw/{source}/{region}/{well}_{API}.pdf`
- Metadata manifest: JSON with source URL, timestamp, API, well name, formation
- Integrity verification: file size validation

*Full specification: [docs/research/Software specification - Automated Subsurface Data Ingestion Pipeline.md](../docs/research/)*

## Briefs Completed

| # | Brief | Issue | Status |
|---|-------|-------|--------|
| 3 | Preserve original column headers | #13, #14 | Done |
| 4 | Footnote symbol handling | #4 | Done |
| 5 | Header normalization across pages | #16 | Done |
| 6 | Data analysis prep output | - | Done |
| 7 | Code modularity refactor | - | Done |
| 8 | Spec/extended output comparison | #15 | Done |
| 9 | Data analysis validation | - | Done |
| 10 | Fix pylint audit integration | #10 | Done |

## Briefs Pending

*None currently - ready for new ideas!*

## Contributing Ideas

To propose a new extension:

1. Create a brief in `ideas/active/NN-short-name.md`
2. Include: problem statement, proposed solution, effort estimate
3. Discuss before implementing

## See Also

- [Extensions](./Extensions) - Detailed documentation of existing extensions
- [Architecture](./Architecture) - Current design and trade-offs
- [Assignment-Requirements](./Assignment-Requirements) - Audit results
