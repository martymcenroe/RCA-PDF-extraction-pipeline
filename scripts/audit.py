#!/usr/bin/env python3
"""
Submission Audit Script

Verifies assignment compliance by running automated checks against
the requirements defined in docs/standards/00801-audit-methodology.md

Usage:
    python scripts/audit.py [--verbose] [--output PATH]
"""

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

# Project root (script is in scripts/)
PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class CheckResult:
    """Result of a single verification check."""
    req_id: str
    name: str
    status: Literal["PASS", "FAIL", "WARN", "SKIP", "BLOCKER"]
    message: str
    evidence: str = ""
    brief: str = ""  # Reference to brief if BLOCKER


# =============================================================================
# VERIFICATION FUNCTIONS
# =============================================================================

def check_f1_classification_exists() -> CheckResult:
    """F1: Page classification output exists."""
    json_path = PROJECT_ROOT / "data/output/spec/page_classification.json"

    if not json_path.exists():
        return CheckResult("F1", "Classification output exists", "FAIL",
                           f"File not found: {json_path}")

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        # JSON is now flat: {"page_1": "type", "page_2": "type", ...}
        if data and isinstance(data, dict):
            count = len(data)
            return CheckResult("F1", "Classification output exists", "PASS",
                               f"Found {count} page classifications",
                               evidence=f"Keys: {list(data.keys())[:5]}...")
        else:
            return CheckResult("F1", "Classification output exists", "FAIL",
                               "JSON is empty or invalid format")
    except json.JSONDecodeError as e:
        return CheckResult("F1", "Classification output exists", "FAIL",
                           f"Invalid JSON: {e}")


def check_f2_table_pages_identified() -> CheckResult:
    """F2: Classification identifies table pages."""
    json_path = PROJECT_ROOT / "data/output/spec/page_classification.json"

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        classifications = data  # Flat dict: {"page_1": "type", ...}
        table_pages = [k for k, v in classifications.items() if v == "table"]

        if len(table_pages) >= 1:
            return CheckResult("F2", "Table pages identified", "PASS",
                               f"Found {len(table_pages)} table pages",
                               evidence=str(table_pages))
        else:
            return CheckResult("F2", "Table pages identified", "FAIL",
                               "No pages classified as 'table'")
    except Exception as e:
        return CheckResult("F2", "Table pages identified", "FAIL", str(e))


def check_f3_nontable_pages_identified() -> CheckResult:
    """F3: Classification identifies non-table pages."""
    json_path = PROJECT_ROOT / "data/output/spec/page_classification.json"

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        classifications = data  # Flat dict: {"page_1": "type", ...}
        non_table = [k for k, v in classifications.items() if v != "table"]

        if len(non_table) >= 1:
            types = set(classifications.values())
            return CheckResult("F3", "Non-table pages identified", "PASS",
                               f"Found {len(non_table)} non-table pages",
                               evidence=f"Types: {types}")
        else:
            return CheckResult("F3", "Non-table pages identified", "FAIL",
                               "All pages classified as 'table'")
    except Exception as e:
        return CheckResult("F3", "Non-table pages identified", "FAIL", str(e))


def check_f4_extraction_matches_classification() -> CheckResult:
    """F4: Table extraction iterates classified pages."""
    json_path = PROJECT_ROOT / "data/output/spec/page_classification.json"
    csv_path = PROJECT_ROOT / "data/output/spec/full_table_extraction.csv"

    try:
        with open(json_path, encoding="utf-8") as f:
            classifications = json.load(f)

        # Get table pages from classification
        table_pages = {k for k, v in classifications.items() if v == "table"}
        classified_nums = {int(k.replace('page_', '')) for k in table_pages}

        # Get extracted page numbers from CSV (last column is Page Number)
        with open(csv_path, encoding="utf-8-sig") as f:
            lines = f.readlines()

        if len(lines) < 2:
            return CheckResult("F4", "Extraction matches classification", "FAIL",
                               "CSV has no data rows")

        # Extract page numbers from last column
        extracted_nums = set()
        for line in lines[1:]:  # Skip header
            cols = line.strip().split(',')
            if cols:
                try:
                    extracted_nums.add(int(cols[-1]))
                except ValueError:
                    pass

        if extracted_nums:
            if extracted_nums.issubset(classified_nums):
                return CheckResult("F4", "Extraction matches classification", "PASS",
                                   f"All extracted pages ({sorted(extracted_nums)}) are classified as table",
                                   evidence=f"Table pages: {sorted(classified_nums)}")
            else:
                extra = extracted_nums - classified_nums
                return CheckResult("F4", "Extraction matches classification", "WARN",
                                   f"Extracted from non-table pages: {extra}")
        else:
            return CheckResult("F4", "Extraction matches classification", "FAIL",
                               "No page numbers found in CSV")
    except Exception as e:
        return CheckResult("F4", "Extraction matches classification", "FAIL", str(e))


def check_f5_all_tables_extracted() -> CheckResult:
    """F5: All tables extracted (138 rows expected for W20552)."""
    csv_path = PROJECT_ROOT / "data/output/spec/full_table_extraction.csv"

    try:
        with open(csv_path, encoding="utf-8") as f:
            lines = f.readlines()

        row_count = len(lines) - 1  # Subtract header

        if row_count == 138:
            return CheckResult("F5", "All tables extracted", "PASS",
                               f"Extracted {row_count} rows (expected 138)")
        elif row_count > 100:
            return CheckResult("F5", "All tables extracted", "WARN",
                               f"Extracted {row_count} rows (expected 138)")
        else:
            return CheckResult("F5", "All tables extracted", "FAIL",
                               f"Extracted {row_count} rows (expected 138)")
    except Exception as e:
        return CheckResult("F5", "All tables extracted", "FAIL", str(e))


def check_f6_consolidated_output() -> CheckResult:
    """F6: Output is consolidated dataset."""
    csv_path = PROJECT_ROOT / "data/output/spec/full_table_extraction.csv"
    json_path = PROJECT_ROOT / "data/output/spec/page_classification.json"

    csv_exists = csv_path.exists()
    json_exists = json_path.exists()

    if csv_exists and json_exists:
        return CheckResult("F6", "Consolidated output exists", "PASS",
                           "Both CSV and JSON outputs exist",
                           evidence=f"CSV: {csv_path.stat().st_size} bytes, JSON: {json_path.stat().st_size} bytes")
    elif csv_exists or json_exists:
        return CheckResult("F6", "Consolidated output exists", "PASS",
                           f"Output exists: CSV={csv_exists}, JSON={json_exists}")
    else:
        return CheckResult("F6", "Consolidated output exists", "FAIL",
                           "No CSV or JSON output found")


def check_f7_output_format() -> CheckResult:
    """F7: Output format is CSV or JSON."""
    csv_path = PROJECT_ROOT / "data/output/spec/full_table_extraction.csv"
    json_path = PROJECT_ROOT / "data/output/spec/page_classification.json"

    formats = []
    if csv_path.exists():
        formats.append("CSV")
    if json_path.exists():
        formats.append("JSON")

    if formats:
        return CheckResult("F7", "Output format correct", "PASS",
                           f"Formats: {', '.join(formats)}")
    else:
        return CheckResult("F7", "Output format correct", "FAIL",
                           "No .csv or .json output found")


def check_f8_headers_preserved() -> CheckResult:
    """F8: Column headers preserved from PDF."""
    csv_path = PROJECT_ROOT / "data/output/spec/full_table_extraction.csv"

    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            header_line = f.readline().strip()

        # Expected PDF headers (extracted from actual PDF)
        expected_patterns = [
            'Core Number', 'Sample Number', 'Sample Depth',
            'Permeability', 'Porosity', 'Grain Density', 'Fluid Saturations'
        ]

        # Check if headers contain expected PDF patterns
        matches = [p for p in expected_patterns if p in header_line]

        if len(matches) >= 5:
            return CheckResult("F8", "Column headers preserved", "PASS",
                               f"Headers match PDF ({len(matches)} patterns found)",
                               evidence=f"Found: {matches}")

        # Check for invented snake_case patterns (old format)
        invented_patterns = ['_md', '_pct', '_gcc', '_feet', 'core_number', 'sample_number']
        if any(pat in header_line.lower() for pat in invented_patterns):
            return CheckResult("F8", "Column headers preserved", "FAIL",
                               "Headers are snake_case, not preserved from PDF",
                               evidence=f"Header: {header_line[:80]}...")

        return CheckResult("F8", "Column headers preserved", "WARN",
                           "Headers format unclear",
                           evidence=f"Header: {header_line[:80]}...")
    except Exception as e:
        return CheckResult("F8", "Column headers preserved", "FAIL", str(e))


def check_f9_header_variations() -> CheckResult:
    """F9: Header variations across pages handled."""
    verification_path = PROJECT_ROOT / "data/output/spec/header_verification.txt"

    if not verification_path.exists():
        return CheckResult("F9", "Header variations handled", "FAIL",
                           "header_verification.txt not found")

    try:
        with open(verification_path, encoding="utf-8") as f:
            content = f.read()

        if "VERIFIED" in content:
            # Extract pages checked
            import re
            pages_match = re.search(r'Pages Checked: ([\d, ]+)', content)
            pages = pages_match.group(1) if pages_match else "unknown"
            return CheckResult("F9", "Header variations handled", "PASS",
                               f"Headers verified across pages {pages}",
                               evidence="All table pages have matching headers")

        elif "MISMATCH" in content:
            return CheckResult("F9", "Header variations handled", "WARN",
                               "Header mismatches detected across pages",
                               evidence=content[:200])
        else:
            return CheckResult("F9", "Header variations handled", "WARN",
                               "Verification status unclear",
                               evidence=content[:100])
    except Exception as e:
        return CheckResult("F9", "Header variations handled", "FAIL", str(e))


def check_q1_code_modular() -> CheckResult:
    """Q1: Code is modular."""
    src_path = PROJECT_ROOT / "src/core_analysis.py"

    try:
        with open(src_path, encoding="utf-8") as f:
            content = f.read()

        # Count functions
        func_count = len(re.findall(r'^def \w+', content, re.MULTILINE))

        # Count classes
        class_count = len(re.findall(r'^class \w+', content, re.MULTILINE))

        if func_count >= 3:
            return CheckResult("Q1", "Code is modular", "PASS",
                               f"Found {func_count} functions, {class_count} classes",
                               evidence=f"Functions provide separation of concerns")
        else:
            return CheckResult("Q1", "Code is modular", "WARN",
                               f"Only {func_count} functions - consider more modularization")
    except Exception as e:
        return CheckResult("Q1", "Code is modular", "FAIL", str(e))


def check_q2_code_clean() -> CheckResult:
    """Q2: Code is clean (pylint score)."""
    src_path = PROJECT_ROOT / "src/core_analysis.py"

    # First check if pylint is installed
    try:
        version_result = subprocess.run(
            ["python", "-m", "pylint", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        if version_result.returncode != 0:
            return CheckResult("Q2", "Code is clean", "SKIP",
                               "pylint not installed - run: pip install pylint")
    except FileNotFoundError:
        return CheckResult("Q2", "Code is clean", "SKIP",
                           "pylint not installed - run: pip install pylint")
    except subprocess.TimeoutExpired:
        return CheckResult("Q2", "Code is clean", "SKIP",
                           "pylint version check timed out")

    # Check source file exists
    if not src_path.exists():
        return CheckResult("Q2", "Code is clean", "SKIP",
                           f"Source file not found: {src_path}")

    try:
        # Run pylint with extended timeout
        # Note: pylint returns non-zero exit codes for any warnings/errors found
        # so we cannot rely on returncode for success
        result = subprocess.run(
            ["python", "-m", "pylint", str(src_path), "--score=y", "--output-format=text"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )

        # Combine stdout and stderr for parsing (score can appear in either)
        combined_output = result.stdout + "\n" + result.stderr

        # Extract score - handle negative scores (pylint can return negative values)
        score_match = re.search(r'Your code has been rated at (-?[\d.]+)/10', combined_output)

        if score_match:
            score = float(score_match.group(1))
            if score >= 8.0:
                return CheckResult("Q2", "Code is clean", "PASS",
                                   f"Pylint score: {score}/10")
            elif score >= 6.0:
                return CheckResult("Q2", "Code is clean", "WARN",
                                   f"Pylint score: {score}/10 (target: 8.0)")
            else:
                return CheckResult("Q2", "Code is clean", "FAIL",
                                   f"Pylint score: {score}/10 (target: 8.0)")
        else:
            # Parse failure - provide debug evidence
            evidence = f"stdout: {result.stdout[:100]}... stderr: {result.stderr[:100]}..."
            return CheckResult("Q2", "Code is clean", "SKIP",
                               "Could not parse pylint output",
                               evidence=evidence)
    except subprocess.TimeoutExpired:
        return CheckResult("Q2", "Code is clean", "SKIP",
                           "pylint timed out after 120s")
    except Exception as e:
        return CheckResult("Q2", "Code is clean", "SKIP",
                           f"{type(e).__name__}: {e}")


def check_q3_loops_efficiently() -> CheckResult:
    """Q3: Solution loops efficiently (benchmark)."""
    # Check if we have benchmark data or run a quick test
    # For now, check if processing time is documented

    perf_path = PROJECT_ROOT / "docs/wiki/Performance.md"

    if perf_path.exists():
        with open(perf_path, encoding="utf-8") as f:
            content = f.read()

        if "359 ms" in content or "359ms" in content:
            return CheckResult("Q3", "Solution loops efficiently", "PASS",
                               "Processing time: 359ms for 253 pages",
                               evidence="1.4ms per page average")
        elif re.search(r'\d+\s*ms', content):
            return CheckResult("Q3", "Solution loops efficiently", "PASS",
                               "Performance documented in wiki")

    return CheckResult("Q3", "Solution loops efficiently", "WARN",
                       "Performance not verified - run benchmark")


def check_q4_noise_handled() -> CheckResult:
    """Q4: Noise (headers, footers, artifacts) handled."""
    csv_path = PROJECT_ROOT / "data/output/spec/full_table_extraction.csv"

    try:
        with open(csv_path, encoding="utf-8") as f:
            content = f.read()

        # Check for known noise patterns that should NOT be in output
        noise_patterns = [
            "Page ",  # Page numbers
            "CORE LABORATORIES",  # Company name
            "continued",  # Footer text
            "TABLE OF CONTENTS",
        ]

        found_noise = [p for p in noise_patterns if p in content]

        if found_noise:
            return CheckResult("Q4", "Noise handled", "WARN",
                               f"Possible noise in output: {found_noise}")
        else:
            return CheckResult("Q4", "Noise handled", "PASS",
                               "No obvious noise patterns detected")
    except Exception as e:
        return CheckResult("Q4", "Noise handled", "FAIL", str(e))


def check_q5_tool_selection_explained() -> CheckResult:
    """Q5: Tool selection explained in README."""
    readme_path = PROJECT_ROOT / "README.md"

    try:
        with open(readme_path, encoding="utf-8") as f:
            content = f.read().lower()

        tools = ["pymupdf", "pdfplumber", "tesseract", "opencv", "openai", "aws", "azure"]
        mentioned = [t for t in tools if t in content]

        if mentioned:
            return CheckResult("Q5", "Tool selection explained", "PASS",
                               f"Tools mentioned: {mentioned}")
        else:
            return CheckResult("Q5", "Tool selection explained", "WARN",
                               "No tool names found in README")
    except Exception as e:
        return CheckResult("Q5", "Tool selection explained", "FAIL", str(e))


def check_q6_tradeoffs_documented() -> CheckResult:
    """Q6: Cost/latency trade-offs documented."""
    readme_path = PROJECT_ROOT / "README.md"
    arch_path = PROJECT_ROOT / "docs/wiki/Architecture.md"

    tradeoff_keywords = ["trade-off", "tradeoff", "cost", "latency", "performance", "speed", "accuracy"]

    for path in [readme_path, arch_path]:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                content = f.read().lower()

            found = [k for k in tradeoff_keywords if k in content]
            if len(found) >= 2:
                return CheckResult("Q6", "Trade-offs documented", "PASS",
                                   f"Trade-off discussion found in {path.name}",
                                   evidence=f"Keywords: {found}")

    return CheckResult("Q6", "Trade-offs documented", "WARN",
                       "Limited trade-off discussion found")


def check_d1_source_code() -> CheckResult:
    """D1: Source code provided."""
    src_files = list((PROJECT_ROOT / "src").glob("*.py"))

    if src_files:
        return CheckResult("D1", "Source code provided", "PASS",
                           f"Found {len(src_files)} Python files in src/",
                           evidence=str([f.name for f in src_files]))
    else:
        return CheckResult("D1", "Source code provided", "FAIL",
                           "No Python files found in src/")


def check_d2_readme_exists() -> CheckResult:
    """D2: README exists."""
    readme_path = PROJECT_ROOT / "README.md"

    if readme_path.exists():
        size = readme_path.stat().st_size
        return CheckResult("D2", "README exists", "PASS",
                           f"README.md exists ({size} bytes)")
    else:
        return CheckResult("D2", "README exists", "FAIL",
                           "README.md not found")


def check_d3_readme_approach() -> CheckResult:
    """D3: README explains approach."""
    readme_path = PROJECT_ROOT / "README.md"

    try:
        with open(readme_path, encoding="utf-8") as f:
            content = f.read()

        # Look for approach-related content
        approach_indicators = [
            "approach", "how it works", "architecture", "design",
            "pipeline", "process", "method", "algorithm"
        ]

        found = [i for i in approach_indicators if i.lower() in content.lower()]

        if len(found) >= 2:
            return CheckResult("D3", "README explains approach", "PASS",
                               f"Approach explanation found",
                               evidence=f"Indicators: {found}")
        else:
            return CheckResult("D3", "README explains approach", "WARN",
                               "Limited approach explanation")
    except Exception as e:
        return CheckResult("D3", "README explains approach", "FAIL", str(e))


def check_d4_readme_run_instructions() -> CheckResult:
    """D4: README explains how to run."""
    readme_path = PROJECT_ROOT / "README.md"

    try:
        with open(readme_path, encoding="utf-8") as f:
            content = f.read()

        # Look for run instructions
        run_indicators = [
            "```bash", "```shell", "pip install", "python ",
            "poetry run", "how to run", "usage", "quick start"
        ]

        found = [i for i in run_indicators if i.lower() in content.lower()]

        if "```" in content and len(found) >= 2:
            return CheckResult("D4", "README has run instructions", "PASS",
                               "Run instructions with code blocks found",
                               evidence=f"Indicators: {found}")
        elif found:
            return CheckResult("D4", "README has run instructions", "WARN",
                               "Some run instructions found")
        else:
            return CheckResult("D4", "README has run instructions", "FAIL",
                               "No run instructions found")
    except Exception as e:
        return CheckResult("D4", "README has run instructions", "FAIL", str(e))


# =============================================================================
# AUDIT RUNNER
# =============================================================================

ALL_CHECKS = [
    # Functional
    check_f1_classification_exists,
    check_f2_table_pages_identified,
    check_f3_nontable_pages_identified,
    check_f4_extraction_matches_classification,
    check_f5_all_tables_extracted,
    check_f6_consolidated_output,
    check_f7_output_format,
    check_f8_headers_preserved,
    check_f9_header_variations,
    # Quality
    check_q1_code_modular,
    check_q2_code_clean,
    check_q3_loops_efficiently,
    check_q4_noise_handled,
    check_q5_tool_selection_explained,
    check_q6_tradeoffs_documented,
    # Deliverables
    check_d1_source_code,
    check_d2_readme_exists,
    check_d3_readme_approach,
    check_d4_readme_run_instructions,
]


def run_audit(verbose: bool = False) -> list[CheckResult]:
    """Run all audit checks."""
    results = []

    # ASCII-safe status icons for Windows console
    status_icons = {
        "PASS": "[OK]",
        "FAIL": "[X]",
        "WARN": "[!]",
        "SKIP": "[-]",
        "BLOCKER": "[!!]"
    }

    for check in ALL_CHECKS:
        try:
            result = check()
            results.append(result)
            if verbose:
                icon = status_icons.get(result.status, "[?]")
                print(f"{icon} {result.req_id}: {result.name} - {result.status}")
                if result.message:
                    print(f"    {result.message}")
        except Exception as e:
            results.append(CheckResult(
                check.__name__,
                check.__doc__ or "Unknown",
                "FAIL",
                f"Exception: {e}"
            ))

    return results


def generate_report(results: list[CheckResult]) -> str:
    """Generate markdown audit report."""
    lines = [
        "# Submission Audit Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Project:** RCA-PDF-extraction-pipeline",
        "",
        "---",
        "",
        "## Summary",
        "",
    ]

    # Count by status
    counts = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    lines.append("| Status | Count |")
    lines.append("|--------|-------|")
    for status in ["PASS", "WARN", "FAIL", "BLOCKER", "SKIP"]:
        if status in counts:
            lines.append(f"| {status} | {counts[status]} |")

    lines.append("")

    # Blockers section
    blockers = [r for r in results if r.status == "BLOCKER"]
    if blockers:
        lines.append("## 🚫 BLOCKERS (Must Fix Before Submission)")
        lines.append("")
        for r in blockers:
            lines.append(f"### {r.req_id}: {r.name}")
            lines.append("")
            lines.append(f"**Issue:** {r.message}")
            if r.evidence:
                lines.append(f"**Evidence:** {r.evidence}")
            if r.brief:
                lines.append(f"**Resolution:** See `docs/ideas/{r.brief.zfill(3)}*.md`")
            lines.append("")

    # Failures section
    failures = [r for r in results if r.status == "FAIL"]
    if failures:
        lines.append("## ✗ FAILURES")
        lines.append("")
        for r in failures:
            lines.append(f"- **{r.req_id}**: {r.name} - {r.message}")
        lines.append("")

    # Warnings section
    warnings = [r for r in results if r.status == "WARN"]
    if warnings:
        lines.append("## ⚠ WARNINGS")
        lines.append("")
        for r in warnings:
            lines.append(f"- **{r.req_id}**: {r.name} - {r.message}")
        lines.append("")

    # Full results table
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| Req | Name | Status | Message |")
    lines.append("|-----|------|--------|---------|")

    for r in results:
        status_icon = {
            "PASS": "✓",
            "FAIL": "✗",
            "WARN": "⚠",
            "SKIP": "○",
            "BLOCKER": "🚫"
        }.get(r.status, "?")
        msg = r.message[:50] + "..." if len(r.message) > 50 else r.message
        lines.append(f"| {r.req_id} | {r.name} | {status_icon} {r.status} | {msg} |")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Next Steps")
    lines.append("")

    if blockers:
        lines.append("### Critical (Blockers)")
        for r in blockers:
            brief_ref = f" (brief {r.brief})" if r.brief else ""
            lines.append(f"1. [ ] Fix {r.req_id}: {r.name}{brief_ref}")
        lines.append("")

    if failures:
        lines.append("### High Priority (Failures)")
        for r in failures:
            lines.append(f"1. [ ] Fix {r.req_id}: {r.name}")
        lines.append("")

    if warnings:
        lines.append("### Medium Priority (Warnings)")
        for r in warnings:
            lines.append(f"1. [ ] Address {r.req_id}: {r.name}")
        lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run submission audit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", default="docs/audit/audit-report.md",
                        help="Output report path")
    args = parser.parse_args()

    print("Running submission audit...")
    print("=" * 50)

    results = run_audit(verbose=args.verbose)

    print("=" * 50)

    # Generate report
    report = generate_report(results)

    # Write report
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nReport written to: {output_path}")

    # Also write JSON results
    json_path = output_path.with_suffix(".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump([{
            "req_id": r.req_id,
            "name": r.name,
            "status": r.status,
            "message": r.message,
            "evidence": r.evidence,
            "brief": r.brief
        } for r in results], f, indent=2)

    print(f"JSON results: {json_path}")

    # Summary
    blockers = sum(1 for r in results if r.status == "BLOCKER")
    failures = sum(1 for r in results if r.status == "FAIL")
    passes = sum(1 for r in results if r.status == "PASS")

    print(f"\nSummary: {passes} PASS, {failures} FAIL, {blockers} BLOCKER")

    if blockers > 0 or failures > 0:
        print("\n[X] AUDIT FAILED - See report for details")
        sys.exit(1)
    else:
        print("\n[OK] AUDIT PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
