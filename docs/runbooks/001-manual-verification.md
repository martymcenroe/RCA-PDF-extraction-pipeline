# Runbook: Manual Verification of Extraction Output

**Purpose:** Verify the pipeline output matches the source PDF.

**Time required:** 15-20 minutes

**Files needed:**
- Source PDF: `docs/context/init/W20552.pdf`
- Page classification: `data/output/core_analysis_minimal.json`
- Table extraction: `data/output/core_analysis_minimal.csv`

---

## Part 1: Verify Page Classification

### Step 1.1: Open the PDF

Open `W20552.pdf` in a PDF viewer (browser, Adobe, Preview).

### Step 1.2: Find table pages manually

Scroll through the document looking for pages with the header:

> **"SUMMARY OF ROUTINE CORE ANALYSES RESULTS"**

Note the page numbers. You should find tables on pages **39, 40, 41, 42**.

### Step 1.3: Compare to program output

Open `core_analysis_minimal.json` and check the classifications:

```json
{
  "classifications": {
    "page_39": "table",
    "page_40": "table",
    "page_41": "table",
    "page_42": "table",
    ...
  }
}
```

**Verification questions:**
- [ ] Do the table pages match? (Expected: 39, 40, 41, 42)
- [ ] Are plot pages correctly identified? (Expected: 43, 44, 45 as "plot")
- [ ] Is page 1 identified as "cover"?

### Step 1.4: Check page count

The PDF has 253 pages. Verify the JSON has 253 classifications:

```bash
python -c "import json; d=json.load(open('data/output/core_analysis_minimal.json')); print(len(d['classifications']))"
# Expected: 253
```

---

## Part 2: Verify Table Extraction

### Step 2.1: Open the source table (PDF page 39)

Go to page 39 of the PDF. You'll see a table with columns:
- Core Number
- Sample Number
- Depth (feet)
- Permeability to Air (md)
- Permeability Klinkenberg (md)
- Porosity Ambient (%)
- Porosity NCS (%)
- Grain Density (g/cc)
- Water Saturation (%)
- Oil Saturation (%)
- Total Saturation (%)

### Step 2.2: Verify first row

In the PDF, the first data row is:

| Core | Sample | Depth | Perm Air | Perm Klink | Por Amb | Por NCS | Grain Den | Sat W | Sat O | Sat T |
|------|--------|-------|----------|------------|---------|---------|-----------|-------|-------|-------|
| 1 | 1-1 | 9,580.50 | 0.0011 | 0.0003 | 0.9 | 0.9 | 2.70 | 96.5 | 1.5 | 98.1 |

Open `core_analysis_minimal.csv` and verify row 2 (first data row):

```
1,1-1,9580.5,0.0011,0.0003,0.9,0.9,2.7,96.5,1.5,98.1,39,
```

**Verification questions:**
- [ ] Does core_number match? (Expected: 1)
- [ ] Does sample_number match? (Expected: 1-1)
- [ ] Does depth match? (Expected: 9580.5 - note: trailing zero dropped)
- [ ] Do permeability values match?
- [ ] Do porosity values match?
- [ ] Does grain density match? (Expected: 2.7)
- [ ] Do saturation values match?

### Step 2.3: Verify a fracture sample

In the PDF, sample 1-2(F) is a fracture sample (marked with F):

| Core | Sample | Depth | Perm Air | Por Amb | Grain Den | Sat W | Sat O | Sat T |
|------|--------|-------|----------|---------|-----------|-------|-------|-------|
| 1 | 1-2(F) | 9,581.50 | + | 1.2 | 2.70 | 76.4 | 0.8 | 77.2 |

Note: Fracture samples have "+" instead of permeability and no Klinkenberg or NCS values.

In the CSV:
```
1,1-2(F),9581.5,,,1.2,,2.7,76.4,0.8,77.2,39,fracture
```

**Verification questions:**
- [ ] Is permeability blank (not "+")?
- [ ] Is porosity_ambient = 1.2?
- [ ] Is grain_density = 2.7?
- [ ] Are saturations correct?
- [ ] Does notes contain "fracture"?

### Step 2.4: Verify sample count

Count the data rows in the PDF tables (pages 39-42). You should count **138 samples**.

Verify the CSV has 138 data rows (plus 1 header = 139 lines):

```bash
wc -l data/output/core_analysis_minimal.csv
# Expected: 139
```

### Step 2.5: Spot check random samples

Pick 3-5 random rows from the CSV and verify against the PDF:

1. Row 50: Sample should be around depth 9,620-9,630 ft
2. Row 100: Sample should be around depth 9,680-9,690 ft
3. Last row (138): Should be sample 2-37 at depth 9,727.50 ft

---

## Part 3: Quick Sanity Checks

### Depth range

```bash
# First and last depths
head -2 data/output/core_analysis_minimal.csv | tail -1 | cut -d',' -f3
# Expected: 9580.5

tail -1 data/output/core_analysis_minimal.csv | cut -d',' -f3
# Expected: 9727.5
```

Verify in PDF: First sample is at 9,580.50 ft, last sample is at 9,727.50 ft.

### No duplicate samples

```bash
cut -d',' -f2 data/output/core_analysis_minimal.csv | sort | uniq -d
# Expected: no output (no duplicates)
```

### All pages accounted for

```bash
cut -d',' -f12 data/output/core_analysis_minimal.csv | sort | uniq -c
# Expected: samples distributed across pages 39, 40, 41, 42
```

---

## Verification Checklist

| Check | Expected | Actual | Pass? |
|-------|----------|--------|-------|
| Table pages identified | 39, 40, 41, 42 | | |
| Total pages classified | 253 | | |
| Sample count | 138 | | |
| First depth | 9580.5 | | |
| Last depth | 9727.5 | | |
| First sample | 1-1 | | |
| Last sample | 2-37 | | |
| Fracture samples marked | Yes | | |
| No duplicate samples | Yes | | |

---

## Common Issues

| Issue | Cause | Resolution |
|-------|-------|------------|
| Page numbers off by 1 | PDF viewer uses different numbering | Check if viewer is 0-indexed |
| Trailing zeros missing | Float conversion (9580.50 → 9580.5) | Expected behavior |
| Fracture permeability blank | "+" not stored as value | Correct - see notes field |
| ** in PDF, blank in CSV | No saturation data marker | Correct - ** means no data |
