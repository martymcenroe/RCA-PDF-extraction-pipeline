"""CLI entry point for PDF dissection tool."""

import json
import sys
from pathlib import Path

import click

from .page_classifier import PageClassifier
from .pdf_dissector import PDFDissector
from .table_extractor import TableExtractor


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PDF Dissection Tool - Safe PDF analysis and data extraction."""
    pass


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def analyze(pdf_path: str, json_output: bool):
    """Analyze PDF structure and metadata.

    Extracts page count, metadata, fonts, and per-page structure information.
    """
    try:
        with PDFDissector(pdf_path) as dissector:
            summary = dissector.get_summary()

        if json_output:
            click.echo(json.dumps(summary, indent=2))
        else:
            _print_analysis(summary)

    except Exception as e:
        click.echo(f"Error analyzing PDF: {e}", err=True)
        sys.exit(1)


def _print_analysis(summary: dict):
    """Print analysis results in human-readable format."""
    click.echo("\n" + "=" * 60)
    click.echo("PDF STRUCTURE ANALYSIS")
    click.echo("=" * 60)

    click.echo(f"\nFile: {summary['file_path']}")
    click.echo(f"Size: {summary['file_size_mb']} MB ({summary['file_size_bytes']} bytes)")
    click.echo(f"Pages: {summary['page_count']}")
    click.echo(f"PDF Version: {summary['pdf_version'] or 'Unknown'}")
    click.echo(f"Encrypted: {summary['is_encrypted']}")
    click.echo(f"Has Forms: {summary['has_forms']}")

    click.echo("\n--- Metadata ---")
    meta = summary["metadata"]
    for key, value in meta.items():
        if value:
            click.echo(f"  {key}: {value}")

    if summary["fonts"]:
        click.echo(f"\n--- Fonts ({len(summary['fonts'])}) ---")
        for font in summary["fonts"][:10]:  # Limit to 10
            click.echo(f"  - {font}")
        if len(summary["fonts"]) > 10:
            click.echo(f"  ... and {len(summary['fonts']) - 10} more")

    if summary["anomalies"]:
        click.echo("\n--- Anomalies ---")
        for anomaly in summary["anomalies"]:
            click.echo(f"  ! {anomaly}")

    click.echo("\n--- Page Summary ---")
    click.echo(f"{'Page':<6}{'Size':<15}{'Blocks':<8}{'Lines':<8}{'Images':<8}{'Words':<8}")
    click.echo("-" * 53)
    for page in summary["pages"]:
        size = f"{page['width']}x{page['height']}"
        click.echo(
            f"{page['page']:<6}{size:<15}{page['text_blocks']:<8}"
            f"{page['lines']:<8}{page['images']:<8}{page['word_count']:<8}"
        )


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def classify(pdf_path: str, json_output: bool):
    """Classify pages by content type.

    Determines which pages contain tables, narrative text, figures, etc.
    """
    try:
        with PDFDissector(pdf_path) as dissector:
            structure = dissector.analyze()

        classifier = PageClassifier()
        classifications = classifier.classify_structure(structure)
        summary = classifier.get_summary(classifications)

        if json_output:
            click.echo(json.dumps(summary, indent=2))
        else:
            _print_classification(summary)

    except Exception as e:
        click.echo(f"Error classifying PDF: {e}", err=True)
        sys.exit(1)


def _print_classification(summary: dict):
    """Print classification results in human-readable format."""
    click.echo("\n" + "=" * 60)
    click.echo("PAGE CLASSIFICATION")
    click.echo("=" * 60)

    click.echo(f"\nTotal Pages: {summary['total_pages']}")

    click.echo("\n--- By Type ---")
    for page_type, pages in summary["by_type"].items():
        click.echo(f"  {page_type}: pages {pages}")

    if summary["table_pages"]:
        click.echo(f"\n  TABLE PAGES: {summary['table_pages']}")

    click.echo("\n--- Page Details ---")
    click.echo(f"{'Page':<6}{'Type':<12}{'Conf':<8}{'H-Lines':<8}{'V-Lines':<8}{'Notes'}")
    click.echo("-" * 70)
    for page_num, details in summary["details"].items():
        click.echo(
            f"{page_num:<6}{details['type']:<12}{details['confidence']:<8.2f}"
            f"{details['h_lines']:<8}{details['v_lines']:<8}{details['notes'][:30]}"
        )


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="data/output",
    help="Output directory for extracted data",
)
@click.option("--pages", "-p", help="Comma-separated page numbers to extract (e.g., '2,3,4')")
@click.option("--all-pages", "-a", is_flag=True, help="Extract from all pages, not just classified tables")
@click.option("--json-output", "-j", is_flag=True, help="Output summary as JSON")
def extract(pdf_path: str, output: str, pages: str, all_pages: bool, json_output: bool):
    """Extract table data to CSV and JSON.

    By default, extracts from pages classified as tables.
    Use --pages to specify exact pages, or --all-pages for all pages.
    """
    try:
        # Determine which pages to extract from
        page_numbers = None

        if pages:
            page_numbers = [int(p.strip()) for p in pages.split(",")]
        elif not all_pages:
            # Get table pages from classifier
            with PDFDissector(pdf_path) as dissector:
                structure = dissector.analyze()
            classifier = PageClassifier()
            classifications = classifier.classify_structure(structure)
            page_numbers = classifier.get_table_pages(classifications)

            if not page_numbers:
                click.echo("No table pages detected. Use --all-pages to extract from all pages.")
                return

        # Extract tables
        extractor = TableExtractor(pdf_path)
        result = extractor.extract_tables(page_numbers)

        if not result.tables:
            click.echo("No tables found in specified pages.")
            return

        # Save output
        output_dir = Path(output)
        pdf_name = Path(pdf_path).stem

        csv_path = extractor.save_csv(result, output_dir / f"{pdf_name}_tables.csv")
        json_path = extractor.save_json(result, output_dir / f"{pdf_name}_tables.json")

        summary = extractor.get_summary(result)

        if json_output:
            summary["csv_output"] = csv_path
            summary["json_output"] = json_path
            click.echo(json.dumps(summary, indent=2))
        else:
            _print_extraction(summary, csv_path, json_path)

    except Exception as e:
        click.echo(f"Error extracting tables: {e}", err=True)
        sys.exit(1)


def _print_extraction(summary: dict, csv_path: str, json_path: str):
    """Print extraction results in human-readable format."""
    click.echo("\n" + "=" * 60)
    click.echo("TABLE EXTRACTION RESULTS")
    click.echo("=" * 60)

    click.echo(f"\nSource: {summary['source_file']}")
    click.echo(f"Pages Processed: {summary['pages_processed']}")
    click.echo(f"Pages with Tables: {summary['pages_with_tables']}")
    click.echo(f"Tables Found: {summary['total_tables_found']}")

    click.echo("\n--- Consolidated Data ---")
    click.echo(f"Columns: {summary['consolidated_columns']}")
    click.echo(f"Rows: {summary['consolidated_rows']}")

    if summary["headers"]:
        click.echo(f"\nHeaders: {summary['headers']}")

    click.echo("\n--- Output Files ---")
    click.echo(f"  CSV: {csv_path}")
    click.echo(f"  JSON: {json_path}")

    if summary["warnings"]:
        click.echo("\n--- Warnings ---")
        for warning in summary["warnings"]:
            click.echo(f"  ! {warning}")


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="data/output",
    help="Output directory for extracted data",
)
@click.option("--json-output", "-j", is_flag=True, help="Output all results as JSON")
def full(pdf_path: str, output: str, json_output: bool):
    """Run full pipeline: analyze, classify, and extract.

    Performs complete PDF dissection and saves extracted table data.
    """
    results = {}

    try:
        # Step 1: Analyze
        click.echo("Step 1/3: Analyzing PDF structure...")
        with PDFDissector(pdf_path) as dissector:
            structure = dissector.analyze()
            results["analysis"] = dissector.get_summary()

        # Step 2: Classify
        click.echo("Step 2/3: Classifying pages...")
        classifier = PageClassifier()
        classifications = classifier.classify_structure(structure)
        results["classification"] = classifier.get_summary(classifications)
        table_pages = classifier.get_table_pages(classifications)

        # Step 3: Extract
        click.echo("Step 3/3: Extracting tables...")
        if table_pages:
            extractor = TableExtractor(pdf_path)
            extraction_result = extractor.extract_tables(table_pages)
            results["extraction"] = extractor.get_summary(extraction_result)

            if extraction_result.tables:
                output_dir = Path(output)
                pdf_name = Path(pdf_path).stem
                csv_path = extractor.save_csv(extraction_result, output_dir / f"{pdf_name}_tables.csv")
                json_path = extractor.save_json(extraction_result, output_dir / f"{pdf_name}_tables.json")
                results["extraction"]["csv_output"] = csv_path
                results["extraction"]["json_output"] = json_path
        else:
            results["extraction"] = {"message": "No table pages detected"}

        if json_output:
            click.echo(json.dumps(results, indent=2))
        else:
            _print_full_results(results)

    except Exception as e:
        click.echo(f"Error in full pipeline: {e}", err=True)
        sys.exit(1)


def _print_full_results(results: dict):
    """Print full pipeline results."""
    click.echo("\n" + "=" * 60)
    click.echo("FULL PDF DISSECTION COMPLETE")
    click.echo("=" * 60)

    analysis = results["analysis"]
    click.echo(f"\n[ANALYSIS]")
    click.echo(f"  File: {analysis['file_path']}")
    click.echo(f"  Size: {analysis['file_size_mb']} MB")
    click.echo(f"  Pages: {analysis['page_count']}")

    classification = results["classification"]
    click.echo(f"\n[CLASSIFICATION]")
    click.echo(f"  Table pages: {classification['table_pages']}")
    for ptype, pages in classification["by_type"].items():
        click.echo(f"  {ptype}: {len(pages)} pages")

    extraction = results["extraction"]
    click.echo(f"\n[EXTRACTION]")
    if "message" in extraction:
        click.echo(f"  {extraction['message']}")
    else:
        click.echo(f"  Tables found: {extraction['total_tables_found']}")
        click.echo(f"  Rows extracted: {extraction['consolidated_rows']}")
        if "csv_output" in extraction:
            click.echo(f"  CSV: {extraction['csv_output']}")
            click.echo(f"  JSON: {extraction['json_output']}")


if __name__ == "__main__":
    cli()
