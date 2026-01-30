# ADR 0001: Header Variation Strategy

## Status

Accepted

## Context

The assignment specification requires us to "handle any potential header variations across pages" when extracting data from the multi-page RCA summary table (pages 39-42).

During investigation, we discovered that:
1. All four table pages (39-42) contain identical headers in the PDF structure
2. The headers are extracted from the Y-coordinate range 170-230 on each page
3. The current implementation extracts headers from page 39 only and caches them

The question: How should we handle potential header variations when the current PDF has none?

## Decision

We will implement a **verification-first approach**:

1. **Verify headers match across all table pages** at extraction time
2. **Use first table page headers as canonical** (reference)
3. **Output verification results** to `header_verification.txt`
4. **Log warnings** if any mismatches are detected (but continue extraction)

## Rationale

### Why not just assume headers are always identical?

The assignment explicitly requires handling variations. Even if the current PDF has consistent headers, future PDFs may not. By implementing verification, we:
- Satisfy the assignment requirement explicitly
- Create an audit trail proving headers were checked
- Detect any unexpected variations in future documents

### Why verify at extraction time rather than pre-processing?

- Headers are needed for column mapping during extraction anyway
- Avoids duplicate database queries
- Single pass through table pages

### Why use first page as reference?

- First table page typically contains the most complete header structure
- Consistent ordering (always pages 39, 40, 41, 42)
- Simple to understand and debug

### Why output to a file instead of just logging?

- Creates a permanent record for audit purposes
- Human-readable verification artifact
- Can be included in submission/documentation

## Consequences

### Positive

- Assignment requirement explicitly satisfied with verification proof
- Future header variations will be detected and logged
- Verification report provides clear audit trail
- No breaking changes to existing extraction logic

### Negative

- Additional database queries (one per table page for header extraction)
- Slightly longer extraction time (negligible in practice)
- Additional output file to manage

### Neutral

- Header verification is optional (can be disabled if needed)
- Current PDF will always show "VERIFIED" status

## Implementation

See Issue #16 for implementation details:
- `verify_headers_across_pages()` method compares headers
- `save_header_verification()` outputs human-readable report
- Integrated into main extraction pipeline
