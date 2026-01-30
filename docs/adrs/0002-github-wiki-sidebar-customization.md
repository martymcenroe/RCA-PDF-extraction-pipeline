# ADR-0002: GitHub Wiki Sidebar Customization

**Status:** Accepted
**Date:** 2026-01-30

## Context

GitHub Wiki displays pages in alphabetical order by default in the sidebar. We needed custom ordering to place "Quo-Vadis" (vision) last, after "Security".

## Decision

Created a `_Sidebar.md` file in the wiki repository to control page order.

## Lesson Learned

When you create a custom `_Sidebar.md`, GitHub renders it as plain markdown instead of using its default styled navigation. This causes:

- **Font size reduction** - Plain links render smaller than the default navigation
- **Loss of styling** - No hover effects, different spacing

### Solution

Use h3 headers (`###`) for each link to restore larger font size:

```markdown
### [[Home]]

---

### [[Assignment-Requirements]]

### [[Architecture]]

### [[Security]]
```

### What NOT to do

Plain links without headers:

```markdown
[[Home]]

[[Assignment-Requirements]]
```

This renders with smaller fonts than the default sidebar.

## Consequences

- Custom sidebar order achieved
- Font size restored using h3 headers
- Slightly different visual style than default (acceptable trade-off)
