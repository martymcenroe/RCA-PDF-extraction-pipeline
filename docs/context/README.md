# Context

External inputs and reference materials organized by purpose.

## Subdirectories

| Directory | Mutability | Purpose |
|-----------|------------|---------|
| `init/` | **Immutable** | Original requirements, specs, emails - source of truth |
| `lld/` | Mutable | (future) Research gathered for LLD writing |
| `rag/` | Mutable | (future) Context chunks for RAG injection |

## Principles

- `init/` is sacred - never modify, only add versioned updates
- Other subdirectories support working context that can evolve
- All context traces back to `init/` as the authoritative source
