# Refactor core_analysis_minimal.py for Modularity and Testability

## User Story
As a developer maintaining the codebase,
I want `src/core_analysis_minimal.py` refactored into discrete, testable functions,
So that the code is easier to test, debug, and maintain while improving quality metrics.

## Objective
Extract the monolithic `main()` function into 7-8 focused functions that each handle a single responsibility, enabling unit testing and improving the Pylint score.

## UX Flow

### Scenario 1: Running the Script (No Behavior Change)
1. User runs `python src/core_analysis_minimal.py input.pdf --output ./results`
2. Script classifies pages, extracts samples, writes output files
3. Result: Identical output to current implementation (CSV and JSON files)

### Scenario 2: Importing Functions for Reuse
1. Developer imports `from core_analysis_minimal import classify_page`
2. Developer calls `classify_page(page)` on a single page
3. Result: Returns classification string ("table", "plot", "cover", "text", "other")

### Scenario 3: Unit Testing a Component
1. Test calls `extract_samples_from_page(mock_page)`
2. Function processes the mock page independently
3. Result: Returns list of sample dictionaries without side effects

## Requirements

### Code Structure
1. Extract `parse_args()` for CLI argument handling
2. Extract `classify_page()` for single page classification logic
3. Extract `classify_document()` to iterate pages and build classification dict
4. Extract `extract_samples_from_page()` for table parsing logic
5. Extract `extract_all_samples()` to iterate table pages
6. Extract `write_csv()` for CSV output
7. Extract `write_json()` for JSON output
8. Refactor `main()` to orchestrate the pipeline using above functions

### Constraints
1. No new dependencies (maintain "minimal" philosophy)
2. Total file length under 250 lines
3. Preserve exact existing behavior
4. Single file (no module splitting)

## Technical Approach
- **Function Extraction:** Move logical blocks from `main()` into named functions with clear signatures
- **Type Hints:** Add type annotations to all function signatures for clarity
- **Docstrings:** Add Google-style docstrings to each function
- **Return Values:** Functions return data rather than mutating shared state
- **CLI Parsing:** Use `argparse` (standard library only) — no external CLI libraries (`click`, `typer`, etc.) to maintain the "minimal" constraint

## Data Handling
**All processing is performed locally; no data is transmitted to external endpoints.** Input PDF files are read from the local filesystem, processed in memory, and output files (CSV, JSON) are written to the local filesystem only.

## Security Considerations
- No network operations or external data transmission
- File paths are validated via `argparse` before use
- No user-supplied code execution; all operations are predefined
- Output directory must exist or be created with standard permissions

## Target Function Inventory

| Function | Responsibility | Est. Lines |
|----------|---------------|------------|
| `parse_args()` | CLI argument parsing | 15 |
| `classify_page()` | Single page classification | 25 |
| `classify_document()` | Iterate pages, build dict | 10 |
| `extract_samples_from_page()` | Parse table page text | 50 |
| `extract_all_samples()` | Iterate table pages | 10 |
| `write_csv()` | CSV output | 15 |
| `write_json()` | JSON output | 15 |
| `main()` | Orchestration | 20 |

## Files to Create/Modify
- `src/core_analysis_minimal.py` — Refactor into 7-8 functions
- `tests/test_core_analysis_minimal.py` — Add unit tests for extracted functions

## Dependencies
- None — this is a standalone refactor using only Python standard library (`argparse`, `csv`, `json`, `pathlib`)

## Out of Scope (Future)
- Splitting into multiple modules — maintain single-file simplicity
- Adding new features or capabilities — behavior-preserving refactor only
- Comprehensive test coverage — target 70%, full coverage is future work

## Acceptance Criteria
- [ ] File contains 7-8 distinct functions (up from 1)
- [ ] `grep -c "^def " src/core_analysis_minimal.py` returns ≥7
- [ ] Running script produces identical output to before refactor
- [ ] Each function has type hints and docstring
- [ ] Pylint score ≥8.0/10
- [ ] No new dependencies added
- [ ] File remains under 250 lines
- [ ] Audit Q1 (code quality) passes

## Definition of Done

### Implementation
- [ ] All 7-8 functions extracted and working
- [ ] Unit tests written for each extracted function
- [ ] Test coverage ≥70%

### Tools
- [ ] N/A — no CLI tools affected

### Documentation
- [ ] Update docstrings in refactored file
- [ ] Add new files to `docs/0003-file-inventory.md`

### Reports (Pre-Merge Gate)
- [ ] `docs/reports/{IssueID}/implementation-report.md` created
- [ ] `docs/reports/{IssueID}/test-report.md` created

### Verification
- [ ] Run full audit suite — Q1 PASS
- [ ] Run pytest — all tests pass
- [ ] Run pylint — score ≥8.0/10

## Testing Notes

**Regression Testing:**
```bash
# Before refactor, capture output
python src/core_analysis_minimal.py test.pdf --output ./before/

# After refactor, capture output
python src/core_analysis_minimal.py test.pdf --output ./after/

# Compare outputs
diff before/core_analysis.csv after/core_analysis.csv
diff before/core_analysis.json after/core_analysis.json
```

**Unit Test Examples:**
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

## Metrics

| Metric | Before | After (Target) |
|--------|--------|----------------|
| Functions | 1 | 7-8 |
| Pylint score | ~6.5/10 | ≥8.0/10 |
| Test coverage | 0% | ≥70% |

## Labels
`tech-debt`, `refactor`

## Effort Estimate
**T-Shirt Size: S (Small)** — Low complexity, no new logic, behavior-preserving refactor only