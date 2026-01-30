# Assignment Requirements Walkthrough

This document maps each assignment requirement to our implementation approach.

## Overview

The assignment asks us to build a PDF extraction pipeline for Routine Core Analysis (RCA) reports. The pipeline must:
1. Classify pages by type
2. Extract tabular data
3. Handle multi-page tables correctly

## Requirements and Implementation

### 1. Page Classification

**Requirement:** Classify each page as table, plot, cover, text, or other.

**Our Approach:**
- `_classify_page()` method in `core_analysis.py`
- Keyword-based classification with confidence scoring
- Output: `page_classification.json` with format `{"page_1": "type", ...}`

**Key Classifications:**
- `table`: Pages containing "SUMMARY OF ROUTINE CORE ANALYSES" (pages 39-42)
- `plot`: Pages with "PROFILE PLOT", "VERSUS POROSITY", "CROSS PLOT"
- `cover`: Pages with "CORE ANALYSIS REPORT", "TABLE OF CONTENTS"
- `text`: Dense text without table markers
- `other`: Everything else

### 2. Table Data Extraction

**Requirement:** Extract all data from the summary table into a structured format.

**Our Approach:**
- Column boundary detection using predefined X-coordinate ranges
- Multi-row header flattening (4-row header structure)
- Sample parsing with depth value anchoring
- Output: `full_table_extraction.csv`

**Exact Column Headers (from PDF):**

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
| 12 | Page Number *(appended by pipeline)* |

### 3. Handle Header Variations Across Pages

**Requirement:** "Handle any potential header variations across pages"

**Our Approach (Issue #16):**
- Extract headers from ALL table pages, not just the first
- Compare headers across pages for consistency
- Output verification report to `header_verification.txt`
- Log warnings if mismatches detected

**Implementation:**
- `verify_headers_across_pages()` method
- `save_header_verification()` method
- Uses first table page as reference

**Rationale:** See ADR 0001 for detailed reasoning.

### 4. Handle Merged Cells

**Requirement:** Handle merged/spanning cells in the table.

**Our Approach:**
- Detect merged cell indicators: `+`, `**`, `<0.0001`
- Replicate values to all columns in the group:
  - `+` or `<X` in permeability → replicate to both Air and Klinkenberg columns
  - `**` in saturations → replicate to all three saturation columns

**Example:**
```
PDF shows: <0.0001 (spanning two permeability columns)
Output:    <0.0001, <0.0001 (in both columns)
```

### 5. CSV Injection Protection

**Requirement:** (Implicit - security best practice)

**Our Approach:**
- `csv_sanitizer.py` module
- Prefix formula characters (`=`, `+`, `-`, `@`, etc.) with single quote
- Applied to all string values in CSV output

### 6. Output Path Security

**Requirement:** (Implicit - security best practice)

**Our Approach:**
- `_validate_output_path()` method
- Whitelist of allowed output directories
- Prevents path traversal attacks

## Output Files

| File | Description | Assignment Part |
|------|-------------|-----------------|
| `page_classification.json` | Page type mapping | Part 1 |
| `full_table_extraction.csv` | Extracted table data | Part 2 |
| `header_verification.txt` | Header consistency check | Supplement |

## Running the Pipeline

```bash
# From project root
poetry run python -m src.core_analysis data/parsed/rca_report.db -o data/output/spec

# With original PDF headers (instead of canonical names)
poetry run python -m src.core_analysis data/parsed/rca_report.db -o data/output/extended --original-headers
```

## Verification

To verify the implementation meets requirements:

1. **Page Classification:** Check `page_classification.json` has entries for all pages
2. **Table Extraction:** Verify CSV has 161 samples from pages 39-42
3. **Header Verification:** Check `header_verification.txt` shows "VERIFIED"
4. **Merged Cells:** Look for `+` and `**` values appearing in multiple columns
