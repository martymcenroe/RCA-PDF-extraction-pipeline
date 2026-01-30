# Idea: Code Modularity Refactor

**Status:** Enhancement
**Effort:** Low (1-2 hours)
**Value:** Medium - improves code quality score

---

## Problem

The audit (Q1) flagged that `src/core_analysis_minimal.py` has only 1 function, suggesting limited modularization.

Current structure:
```python
# One main function does everything
def main():
    # Parse args
    # Open PDF
    # Classify pages
    # Extract tables
    # Write output
    pass
```

This violates separation of concerns and makes testing difficult.

---

## Current State

```bash
$ grep -c "^def " src/core_analysis_minimal.py
1
```

The script is ~200 lines with logic embedded in `main()`.

---

## Proposal

Refactor into discrete, testable functions:

```python
def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    ...

def classify_page(page: fitz.Page) -> str:
    """Classify a single page as table/plot/cover/text/other."""
    ...

def classify_document(doc: fitz.Document) -> dict[str, str]:
    """Classify all pages in document."""
    ...

def extract_samples_from_page(page: fitz.Page) -> list[dict]:
    """Extract sample data from a single table page."""
    ...

def extract_all_samples(doc: fitz.Document, table_pages: list[int]) -> list[dict]:
    """Extract samples from all table pages."""
    ...

def write_csv(samples: list[dict], path: Path) -> None:
    """Write samples to CSV file."""
    ...

def write_json(classifications: dict, samples: list[dict], path: Path) -> None:
    """Write classifications and samples to JSON file."""
    ...

def main() -> None:
    """Main entry point - orchestrates the pipeline."""
    args = parse_args()
    doc = fitz.open(args.pdf_path)

    classifications = classify_document(doc)
    table_pages = [k for k, v in classifications.items() if v == "table"]

    samples = extract_all_samples(doc, table_pages)

    write_csv(samples, args.output / "core_analysis.csv")
    write_json(classifications, samples, args.output / "core_analysis.json")
```

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Testable** | Each function can be unit tested independently |
| **Readable** | Clear separation of concerns |
| **Reusable** | Functions can be imported by other scripts |
| **Debuggable** | Easier to isolate issues |
| **Pylint score** | Should improve code quality metrics |

---

## Function Inventory

Target structure (7 functions):

| Function | Responsibility | Lines (est) |
|----------|---------------|-------------|
| `parse_args()` | CLI argument parsing | 15 |
| `classify_page()` | Single page classification | 25 |
| `classify_document()` | Iterate pages, build dict | 10 |
| `extract_samples_from_page()` | Parse table page text | 50 |
| `extract_all_samples()` | Iterate table pages | 10 |
| `write_csv()` | CSV output | 15 |
| `write_json()` | JSON output | 15 |
| `main()` | Orchestration | 20 |

---

## Testing

After refactor, add unit tests:

```python
def test_classify_page_table():
    """Verify table page classification."""
    # Mock a page with table keywords
    ...

def test_classify_page_plot():
    """Verify plot page classification."""
    ...

def test_extract_samples_from_page():
    """Verify sample extraction from known page."""
    ...
```

---

## Metrics

**Before:**
- Functions: 1
- Pylint score: ~6.5/10 (estimated)
- Test coverage: 0%

**After (target):**
- Functions: 7-8
- Pylint score: ≥8.0/10
- Test coverage: ≥70%

---

## Constraints

- Maintain "minimal" philosophy - no new dependencies
- Keep total lines under 250
- Preserve existing behavior exactly
- Single file (don't split into multiple modules)

---

## Next Steps

1. [ ] Extract `classify_page()` and `classify_document()`
2. [ ] Extract `extract_samples_from_page()` and `extract_all_samples()`
3. [ ] Extract `write_csv()` and `write_json()`
4. [ ] Refactor `main()` to use new functions
5. [ ] Run audit to verify Q1 passes
6. [ ] Add unit tests for each function
