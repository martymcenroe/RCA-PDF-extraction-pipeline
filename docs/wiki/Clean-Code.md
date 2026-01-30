# Clean Code

This project maintains high code quality standards verified through automated linting.

## Pylint Score

**Current Score: 9.26/10**

The codebase is evaluated using [Pylint](https://pylint.org/), a static code analysis tool that checks for errors, enforces coding standards, and looks for code smells.

### Score Thresholds

| Score | Status | Description |
|-------|--------|-------------|
| 8.0+ | PASS | Clean, well-structured code |
| 6.0-7.9 | WARN | Acceptable but could be improved |
| <6.0 | FAIL | Needs attention before submission |

### Running the Linter

```bash
# Check a specific file
poetry run python -m pylint src/core_analysis.py --score=y

# Check all source files
poetry run python -m pylint src/ --score=y
```

### Audit Integration

The Q2 check in our audit script automatically runs Pylint and reports the score:

```bash
poetry run python scripts/audit.py --verbose
```

Output:
```
[OK] Q2: Code is clean - PASS
    Pylint score: 9.26/10
```

## Code Quality Principles

### 1. Single Responsibility
Each module has a clear purpose:
- `core_analysis.py` - Main extraction pipeline
- `page_classifier.py` - Page type classification
- `table_extractor.py` - Table data extraction
- `pdf_dissector.py` - PDF parsing utilities

### 2. Meaningful Names
Variables and functions use descriptive names that reveal intent:
```python
def verify_headers_across_pages(self, table_pages: list[int]) -> dict:
    """Verify headers are consistent across all table pages."""
```

### 3. Type Hints
All public functions include type annotations for better IDE support and documentation:
```python
def save_header_verification(
    self,
    output_path: str,
    table_pages: list[int] | None = None,
) -> str:
```

### 4. Docstrings
Functions include docstrings explaining purpose, arguments, and return values:
```python
def _extract_headers_from_db(self, conn: sqlite3.Connection, page_num: int = 39) -> list[str]:
    """
    Extract and flatten multi-row table headers from the database.

    Args:
        conn: Database connection.
        page_num: Page number containing the table headers.

    Returns:
        List of flattened header strings in column order.
    """
```

### 5. Error Handling
Meaningful error messages with context:
```python
if not self.db_path.exists():
    raise FileNotFoundError(f"Database not found: {db_path}")
```

### 6. Security
Input validation and output path restrictions:
```python
def _validate_output_path(self, output_path: str) -> bool:
    """Ensure output path is within allowed directories."""
    abs_path = os.path.abspath(output_path)
    for allowed_root in ALLOWED_OUTPUT_ROOTS:
        if abs_path.startswith(os.path.abspath(allowed_root)):
            return True
    raise ValueError(f"Output path '{output_path}' outside allowed directories")
```

## Installing Development Tools

```bash
# Install pylint
pip install pylint>=3.0.0

# Or via poetry (if using extras)
pip install -e ".[dev]"
```

## See Also

- [Assignment Requirements](./Assignment-Requirements.md) - Full requirements walkthrough
- [Performance](./Performance.md) - Processing time benchmarks
