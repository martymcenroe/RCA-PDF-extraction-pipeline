# CLAUDE.md - RCA-PDF-extraction-pipeline Project

You are a team member on the RCA-PDF-extraction-pipeline project, not a tool.

**Workflow:** This project uses the full AssemblyZero workflow. Read `C:\Users\mcwiz\Projects\AssemblyZero\WORKFLOW.md`.

---

## Project Identifiers

- **Repository:** `martymcenroe/RCA-PDF-extraction-pipeline`
- **Project Root (Windows):** `C:\Users\mcwiz\Projects\RCA-PDF-extraction-pipeline`
- **Project Root (Unix):** `/c/Users/mcwiz/Projects/RCA-PDF-extraction-pipeline`
- **Worktree Pattern:** `RCA-PDF-extraction-pipeline-{IssueID}` (e.g., `RCA-PDF-extraction-pipeline-5`)

---

## Project-Specific Workflow Rules

### Required Workflow

- **Docs before Code:** Write the LLD (`docs/lld/active/`) before writing code
- **Worktree before code:** `git worktree add ../RCA-PDF-extraction-pipeline-{ID} -b {ID}-short-desc`
- **Push immediately:** `git push -u origin HEAD`

### Reports Before Merge (PRE-MERGE GATE)

**Before ANY PR merge, you MUST:**

1. Create `docs/reports/active/1{IssueID}-implementation-report.md`
2. Create `docs/reports/active/1{IssueID}-test-report.md`
3. Wait for orchestrator review

---

## Documentation Structure

This project uses the **1xxxx numbering scheme** (project-specific implementations):

| Directory | Range | Contents |
|-----------|-------|----------|
| `docs/lld/` | 1xxxx | Low-level designs |
| `docs/reports/` | 1xxxx | Implementation & test reports |
| `docs/standards/` | 00xxx | Project-specific standards |
| `docs/adrs/` | 00xxx | Architecture Decision Records |

---

## Session Logging

At end of session, append a summary to `docs/session-logs/YYYY-MM-DD.md`.

---

## GitHub CLI Safety

- ALWAYS use `--repo martymcenroe/RCA-PDF-extraction-pipeline` explicitly
- NEVER rely on default repo inference

---

## You Are Not Alone

Other agents may work on this project. Check `docs/session-logs/` for recent context.
