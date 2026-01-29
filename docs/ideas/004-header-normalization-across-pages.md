# Idea: Header Normalization Across Pages

**Status:** Blocker (missed requirement)
**Effort:** Medium (4-8 hours)
**Value:** Critical - core assignment requirement

---

## Problem

The assignment explicitly requires: "handle any potential header variations across pages."

Current implementation extracts tables page-by-page with no header awareness. Each table is stored independently:

```python
{
    "page_number": 39,
    "table_index": 0,
    "rows": [["Header A", "Header B", ...], ["data", "data", ...]]
}
```

This fails when:
1. Headers span multiple rows (merged cells)
2. Continuation pages omit headers entirely
3. Continuation pages have abbreviated headers
4. Column order differs between pages

---

## Observed Variations in W20552.pdf

Pages 39-42 contain the core analysis tables. Variations observed:

| Page | Header Behavior |
|------|-----------------|
| 39 | Full multi-row header with merged cells |
| 40-42 | Continuation - headers repeated or omitted |

Specific issues:
- "Permeability (md)" spans two sub-columns: "Air" and "Klink"
- "Porosity (%)" spans two sub-columns: "Ambient" and "NCS"
- "Fluid Saturation (%)" spans three sub-columns: "Water", "Oil", "Total"

---

## Proposal

Build a header normalization layer that:

1. **Detects header rows** - Distinguish headers from data
2. **Resolves merged cells** - Flatten multi-row headers into single row
3. **Normalizes column names** - Consistent naming across pages
4. **Matches schemas** - Identify when tables are continuations
5. **Merges tables** - Combine continuation pages into single logical table

---

## Implementation

### Phase 1: Header Detection

```python
def is_header_row(row: list[str], data_rows: list[list[str]]) -> bool:
    """Detect if row is a header vs data."""
    # Headers typically:
    # - Contain text, not numbers
    # - Have different patterns than data rows
    # - Appear at top of table

    numeric_count = sum(1 for cell in row if is_numeric(cell))
    if numeric_count > len(row) / 2:
        return False  # Mostly numbers = data row
    return True
```

### Phase 2: Merged Cell Resolution

```python
def flatten_headers(rows: list[list[str]]) -> list[str]:
    """Flatten multi-row headers into single row.

    Input (2 rows):
      ["", "Permeability (md)", "", "Porosity (%)", ""]
      ["Sample", "Air", "Klink", "Ambient", "NCS"]

    Output (1 row):
      ["Sample", "Permeability Air md", "Permeability Klink md",
       "Porosity Ambient pct", "Porosity NCS pct"]
    """
    # Track spanning headers
    # Combine parent + child names
    # Normalize units (%, md, g/cc)
```

### Phase 3: Schema Matching

```python
def tables_match_schema(table1: Table, table2: Table) -> bool:
    """Determine if two tables have compatible schemas."""
    headers1 = normalize_headers(table1.headers)
    headers2 = normalize_headers(table2.headers)

    # Exact match
    if headers1 == headers2:
        return True

    # Subset match (continuation without headers)
    if len(headers2) == 0 and len(table2.rows[0]) == len(headers1):
        return True

    # Fuzzy match (abbreviated headers)
    similarity = calculate_header_similarity(headers1, headers2)
    return similarity > 0.8
```

### Phase 4: Table Merging

```python
def merge_continuation_tables(tables: list[Table]) -> list[Table]:
    """Merge tables that are continuations of each other."""
    merged = []
    current = None

    for table in sorted(tables, key=lambda t: t.page_number):
        if current is None:
            current = table
        elif tables_match_schema(current, table):
            # Append rows, skip duplicate headers
            current.rows.extend(table.data_rows)
        else:
            merged.append(current)
            current = table

    if current:
        merged.append(current)

    return merged
```

---

## Canonical Header Mapping

For RCA documents, define expected headers:

```python
CANONICAL_HEADERS = {
    "core_number": ["Core", "Core No", "Core #"],
    "sample_number": ["Sample", "Sample No", "Sample #", "Samp"],
    "depth_feet": ["Depth", "Depth (ft)", "Depth Feet"],
    "permeability_air_md": ["Air", "Perm Air", "Ka"],
    "permeability_klink_md": ["Klink", "Perm Klink", "Kk"],
    "porosity_ambient_pct": ["Ambient", "Por Amb", "Phi Amb"],
    "porosity_ncs_pct": ["NCS", "Por NCS", "Phi NCS"],
    "grain_density_gcc": ["Grain Density", "GD", "Density"],
    "saturation_water_pct": ["Water", "Sw", "Water Sat"],
    "saturation_oil_pct": ["Oil", "So", "Oil Sat"],
    "saturation_total_pct": ["Total", "St", "Total Sat"],
}

def normalize_header(raw: str) -> str:
    """Map raw header to canonical name."""
    raw_lower = raw.lower().strip()
    for canonical, variants in CANONICAL_HEADERS.items():
        if any(v.lower() in raw_lower for v in variants):
            return canonical
    return raw  # Unknown header
```

---

## Deliverable

Update `src/rca_pipeline/table_extractor.py` to:

1. Accept `normalize_headers=True` flag (default True)
2. Return merged tables with canonical column names
3. Include `header_source_page` in metadata

Output structure:

```python
{
    "table_id": "core_analysis",
    "header_source_page": 39,
    "pages_spanned": [39, 40, 41, 42],
    "columns": ["core_number", "sample_number", "depth_feet", ...],
    "rows": [
        {"core_number": 4, "sample_number": "6-1", "depth_feet": 9580.5, ...},
        # ... all 138 rows merged
    ]
}
```

---

## Testing

```python
def test_header_normalization():
    """Verify headers are normalized across pages."""
    result = extract_tables("W20552.pdf", normalize_headers=True)

    # Should produce single merged table
    core_tables = [t for t in result if "core" in t["table_id"]]
    assert len(core_tables) == 1

    # Should have canonical column names
    assert "permeability_air_md" in core_tables[0]["columns"]
    assert "Permeability (md)" not in str(core_tables[0]["columns"])

    # Should have all rows
    assert len(core_tables[0]["rows"]) == 138

def test_merged_cell_handling():
    """Verify merged header cells are flattened."""
    # Parent "Permeability (md)" with children "Air", "Klink"
    # Should become "permeability_air_md", "permeability_klink_md"
```

---

## Next Steps

1. [ ] Analyze W20552.pdf pages 39-42 header structure in detail
2. [ ] Implement `flatten_headers()` for merged cells
3. [ ] Implement `normalize_header()` mapping
4. [ ] Implement `merge_continuation_tables()`
5. [ ] Add tests for header normalization
6. [ ] Update pipeline to use normalized output
