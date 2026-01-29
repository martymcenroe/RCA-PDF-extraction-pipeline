# Init - Source of Truth Documents

**IMMUTABLE** - This directory contains pristine reference materials that define project requirements.

## Purpose

These documents are the **source of truth** upon which delivery is based. They should be:
- **Immutable** - Never modified after initial placement
- **Authoritative** - The definitive reference for requirements
- **Complete** - All external inputs needed to understand scope

## Contents

| File | Type | Description |
|------|------|-------------|
| *(add your files here)* | | |

## Usage

1. **Place original documents here** - PDFs, emails, specs, contracts
2. **Never modify them** - If updates come in, add new versioned files
3. **Reference in LLDs** - Link to these files when writing designs
4. **Trace requirements** - Implementation should trace back to these docs

## Naming Convention

```
YYYY-MM-DD-source-description.ext
```

Examples:
- `2026-01-29-client-email-requirements.pdf`
- `2026-01-29-sow-v1.pdf`
- `2026-01-30-client-email-clarification.pdf`

## Not For

- Documents we create (use `docs/lld/`, `docs/reports/`)
- Test data (use `tests/fixtures/`)
- App runtime data (use `data/`)
