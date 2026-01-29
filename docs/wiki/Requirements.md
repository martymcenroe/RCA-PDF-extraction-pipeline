# Requirements Analysis

## Assignment Requirements

The assignment specified building a **small pipeline** to:

1. **Page Classification** - Programmatically identify which pages contain tabular Core Analysis data
2. **Full Table Extraction** - Extract all table data into consolidated CSV/JSON

### Requirement 1: Page Classification

**Specification:**
> Classify pages as table vs non-table content. Output format: `{'page_5': 'table', 'page_1': 'other', ...}`

**Implementation:**

The pipeline classifies pages into 5 categories using keyword matching:

| Classification | Keywords/Signals | Count |
|----------------|------------------|-------|
| `table` | "SUMMARY OF ROUTINE CORE ANALYSES" | 4 |
| `plot` | "PROFILE PLOT", "VERSUS POROSITY" | 3 |
| `cover` | "TABLE OF CONTENTS", "CORE LABORATORIES" | 1 |
| `text` | >100 words, no table markers | 122 |
| `other` | Default fallback | 123 |

**Output (JSON):**
```json
{
  "page_39": "table",
  "page_40": "table",
  "page_41": "table",
  "page_42": "table",
  "page_43": "plot",
  "page_44": "plot",
  "page_45": "plot",
  "page_1": "cover",
  ...
}
```

### Requirement 2: Full Table Extraction

**Specification:**
> Extract all tabular data. Consolidate into single CSV/JSON with preserved column headers.

**Implementation:**

Extracted 138 samples with the following schema:

| Column | Description | Example |
|--------|-------------|---------|
| core_number | Core identifier | 1, 2 |
| sample_number | Sample within core | 1-1, 1-2(F) |
| depth_feet | Depth in feet | 9580.50 |
| permeability_air_md | Air permeability (millidarcys) | 0.0011 |
| permeability_klink_md | Klinkenberg permeability | 0.0003 |
| porosity_ambient_pct | Ambient porosity (%) | 0.9 |
| porosity_ncs_pct | Net confining stress porosity | 0.9 |
| grain_density_gcc | Grain density (g/cc) | 2.70 |
| saturation_water_pct | Water saturation (%) | 96.5 |
| saturation_oil_pct | Oil saturation (%) | 1.5 |
| saturation_total_pct | Total saturation (%) | 98.1 |
| page_number | Source page | 39 |
| notes | Special conditions | fracture, below_detection |

**Special Cases Handled:**

| Case | Marker | Handling |
|------|--------|----------|
| Fracture samples | `(F)` suffix, `+` for permeability | Marked in notes |
| Below detection | `<0.0001` | Preserved as string |
| No saturation data | `**` | Empty field |

## Deliverables Checklist

| Requirement | Status | Location |
|-------------|--------|----------|
| Page classification dict | ✅ | `core_analysis_minimal.json` |
| Consolidated CSV | ✅ | `core_analysis_minimal.csv` |
| Consolidated JSON | ✅ | `core_analysis_minimal.json` |
| Source code | ✅ | `src/core_analysis_minimal.py` |
| Documentation | ✅ | `README.md`, `docs/wiki/` |

## "Small Pipeline" Criteria

The assignment requested a "small pipeline". The minimal solution meets this:

| Metric | Value | Assessment |
|--------|-------|------------|
| Source files | 1 | Single file solution |
| Lines of code | ~200 | Minimal |
| Dependencies | 1 (PyMuPDF) | Minimal |
| Processing time | 359 ms | Fast |
| Commands to run | 2 | `pip install` + `python script` |
