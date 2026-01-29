# Standard 00801: Submission Audit Methodology

**Purpose:** Define a repeatable, automated methodology for auditing assignment compliance.

---

## Overview

This document defines how to audit the RCA PDF extraction pipeline submission against the assignment requirements. The audit assumes an automated grading system that:

1. Clones the repository
2. Runs verification scripts
3. Checks outputs against expected formats
4. Evaluates code quality metrics

---

## Requirement Decomposition

The assignment instructions are decomposed into **atomic, verifiable requirements**:

### Category 1: Functional Requirements (MUST PASS)

| ID | Requirement | Source Text |
|----|-------------|-------------|
| F1 | Page classification output exists | "Output: A simple list or dictionary identifying the 'Table Pages'" |
| F2 | Classification identifies table pages | "Programmatically identify which pages...contain tabular Core Analysis data" |
| F3 | Classification identifies non-table pages | "...and which pages do not (e.g., cover pages, text summaries, or plots)" |
| F4 | Table extraction iterates classified pages | "Iterate through all pages identified as containing tables" |
| F5 | All tables extracted | "Extract the data from every table found" |
| F6 | Output is consolidated dataset | "Consolidate the extracted data into a single structured dataset" |
| F7 | Output format is CSV or JSON | "(CSV or JSON)" |
| F8 | Column headers preserved | "You must preserve column headers" |
| F9 | Header variations handled | "handle any potential header variations across pages" |

### Category 2: Quality Requirements (EVALUATED)

| ID | Requirement | Source Text |
|----|-------------|-------------|
| Q1 | Code is modular | "Is the code modular and clean?" |
| Q2 | Code is clean | "Is the code modular and clean?" |
| Q3 | Solution loops efficiently | "Does your solution loop efficiently through the document?" |
| Q4 | Noise is handled | "How do you handle the 'noise' (e.g., headers, footers, scan artifacts)?" |
| Q5 | Tool selection explained | "be prepared to explain your choice" |
| Q6 | Trade-offs documented | "cost/latency trade-offs" |

### Category 3: Deliverable Requirements (MUST PASS)

| ID | Requirement | Source Text |
|----|-------------|-------------|
| D1 | Source code provided | "The source code (GitHub link or Zip file)" |
| D2 | README exists | "A brief README" |
| D3 | README explains approach | "explaining your approach" |
| D4 | README explains how to run | "how to run the code" |

---

## Verification Methods

### Automated Verification Types

| Type | Description | Tool |
|------|-------------|------|
| `EXISTS` | File/directory exists | `test -f` / `test -d` |
| `SCHEMA` | Output matches expected schema | Python JSON/CSV validation |
| `CONTENT` | Output contains expected content | grep / Python |
| `METRIC` | Code metric meets threshold | pylint, radon, mypy |
| `BENCHMARK` | Performance meets threshold | time measurement |
| `COMPARE` | Two outputs match | diff / Python |

### Verification Scripts

All verification is performed by `scripts/audit.py` which:

1. Runs each check
2. Records PASS/FAIL/WARN status
3. Captures evidence (output snippets, metrics)
4. Generates audit report

---

## Audit Execution

### Prerequisites

```bash
pip install pylint radon mypy pandas
```

### Run Audit

```bash
python scripts/audit.py --output docs/audit/audit-report.md
```

### Audit Output

The audit produces:

1. `docs/audit/audit-report.md` - Human-readable report
2. `docs/audit/audit-results.json` - Machine-readable results
3. Exit code: 0 if all MUST PASS items pass, 1 otherwise

---

## Requirement-to-Verification Mapping

| Req ID | Verification Type | Method | Pass Criteria |
|--------|------------------|--------|---------------|
| F1 | EXISTS + SCHEMA | Check JSON has `classifications` key | Key exists, is dict |
| F2 | CONTENT | Check classifications contain "table" values | ≥1 page classified as table |
| F3 | CONTENT | Check classifications contain non-table values | ≥1 page classified as other |
| F4 | CONTENT | Check extracted pages match classified pages | All table pages have data |
| F5 | CONTENT | Check row count matches expected | 138 rows (known for W20552) |
| F6 | EXISTS | Single CSV or JSON output file | File exists |
| F7 | EXISTS | File extension is .csv or .json | Extension check |
| F8 | CONTENT | Headers match PDF headers | **BLOCKER** - see brief 005 |
| F9 | CONTENT | Multi-page tables merged correctly | **BLOCKER** - see brief 004 |
| Q1 | METRIC | Function count, avg function length | Functions <50 lines |
| Q2 | METRIC | Pylint score, type hints | Score ≥7.0/10 |
| Q3 | BENCHMARK | Processing time | <5 seconds for 253 pages |
| Q4 | CONTENT | No garbage in output | No known noise patterns |
| Q5 | CONTENT | README mentions tool names | Keywords present |
| Q6 | CONTENT | README mentions trade-offs | Keywords present |
| D1 | EXISTS | Source files exist | `src/*.py` exists |
| D2 | EXISTS | README exists | `README.md` exists |
| D3 | CONTENT | README has approach section | Section header or keywords |
| D4 | CONTENT | README has run instructions | Command examples present |

---

## Known Blockers

These requirements **currently fail** and have associated briefs:

| Req ID | Status | Brief | Description |
|--------|--------|-------|-------------|
| F8 | FAIL | 005 | Column headers are invented, not preserved from PDF |
| F9 | FAIL | 004 | Header variations not handled (multi-row headers) |

---

## Audit Schedule

| When | Trigger | Scope |
|------|---------|-------|
| Pre-commit | git hook | Quick checks (EXISTS, SCHEMA) |
| PR | CI/CD | Full audit |
| Pre-submission | Manual | Full audit + manual review |

---

## Re-running the Audit

To re-run this audit:

```bash
# Full audit with report generation
python scripts/audit.py

# Specific category only
python scripts/audit.py --category functional
python scripts/audit.py --category quality
python scripts/audit.py --category deliverables

# Verbose output
python scripts/audit.py --verbose
```

---

## Extending the Audit

To add new requirements:

1. Add requirement to table in this document
2. Add verification function to `scripts/audit.py`
3. Add to `REQUIREMENTS` dict in script
4. Run audit to verify
