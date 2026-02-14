# CLAUDE.md - RCA-PDF-extraction-pipeline

**Workflow:** Full AssemblyZero workflow. Read `C:\Users\mcwiz\Projects\AssemblyZero\WORKFLOW.md`.

---

## Project Identifiers

- **Repository:** `martymcenroe/RCA-PDF-extraction-pipeline`
- **Worktree Pattern:** `RCA-PDF-extraction-pipeline-{IssueID}`

---

## Workflow Rules

- **Docs before Code:** Write the LLD (`docs/lld/active/`) before writing code
- **Worktree before code:** `git worktree add ../RCA-PDF-extraction-pipeline-{ID} -b {ID}-short-desc`
- **Push immediately:** `git push -u origin HEAD`

### Pre-Merge Gate

Before ANY PR merge:
1. Create `docs/reports/active/1{IssueID}-implementation-report.md`
2. Create `docs/reports/active/1{IssueID}-test-report.md`
3. Wait for orchestrator review

---

## Documentation Structure

| Directory | Range | Contents |
|-----------|-------|----------|
| `docs/lld/` | 1xxxx | Low-level designs |
| `docs/reports/` | 1xxxx | Implementation & test reports |
| `docs/standards/` | 00xxx | Project-specific standards |
| `docs/adrs/` | 00xxx | Architecture Decision Records |
