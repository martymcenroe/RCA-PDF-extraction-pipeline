# Issue #37: Silent exception handler in src/table_extractor.py:118

## Location
`src/table_extractor.py:118`

## Code
```python
try:
    # table extraction logic
except Exception:
    pass
```

## Problem
Broad `except Exception: pass` silently swallows ALL exceptions including:
- Programming bugs (TypeError, AttributeError)
- Resource issues (MemoryError)
- Unexpected PDF structure issues

## Impact
- Bugs are hidden, not surfaced
- Debugging becomes impossible
- No way to know if tables were skipped or why

## Suggested Fix
1. Narrow the exception type to expected failures
2. Add logging
```python
except (ValueError, KeyError) as e:
    logger.warning(f"Failed to extract table: {e}")
```

## Found By
Automated codebase completeness scan