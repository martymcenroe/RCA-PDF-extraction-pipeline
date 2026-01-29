"""CLI entry point for PDF Elementizer."""

import json
import sys
from pathlib import Path

import click

from .database import ElementDatabase
from .extractor import PDFElementExtractor


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """PDF Elementizer - Extract every PDF element to database."""
    pass


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), default="data/output",
              help="Output directory for database, JSON, and images")
@click.option("--extract-images/--no-images", default=True,
              help="Extract images to files (default: yes)")
@click.option("--store-image-blobs/--no-blobs", default=False,
              help="Store image data as blobs in database (default: no)")
@click.option("--json-only", is_flag=True,
              help="Output JSON only, skip database")
@click.option("--db-only", is_flag=True,
              help="Output database only, skip JSON")
def extract(
    pdf_path: str,
    output: str,
    extract_images: bool,
    store_image_blobs: bool,
    json_only: bool,
    db_only: bool,
):
    """Extract all elements from a PDF to database and JSON.

    Extracts text blocks, images, lines, rectangles, and paths.
    Stores everything in SQLite database and/or JSON file.
    """
    try:
        output_dir = Path(output)
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(pdf_path).stem
        image_dir = output_dir / f"{pdf_name}_images" if extract_images else None

        click.echo(f"Extracting elements from: {pdf_path}")

        # Extract elements
        with PDFElementExtractor(pdf_path, image_output_dir=image_dir) as extractor:
            doc_elements = extractor.extract_all(extract_images=extract_images)
            summary = extractor.get_summary(doc_elements)

        click.echo(f"  Pages: {doc_elements.page_count}")
        click.echo(f"  Total elements: {doc_elements.total_elements}")
        click.echo(f"  Text blocks: {doc_elements.total_text_blocks}")
        click.echo(f"  Images: {doc_elements.total_images}")

        # Save to JSON
        if not db_only:
            json_path = output_dir / f"{pdf_name}_elements.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(doc_elements.to_dict(), f, indent=2, ensure_ascii=False)
            click.echo(f"  JSON: {json_path}")

        # Save to database
        if not json_only:
            db_path = output_dir / f"{pdf_name}_elements.db"
            with ElementDatabase(db_path) as db:
                doc_id = db.store_document(doc_elements, store_image_data=store_image_blobs)
                stats = db.get_stats()
            click.echo(f"  Database: {db_path}")
            click.echo(f"    Document ID: {doc_id}")
            click.echo(f"    Records: {sum(stats.values())}")

        if image_dir and extract_images:
            image_count = len(list(image_dir.glob("*"))) if image_dir.exists() else 0
            click.echo(f"  Images saved: {image_count} files in {image_dir}")

        click.echo("\nDone.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def summary(pdf_path: str, json_output: bool):
    """Show element counts without full extraction.

    Quick summary of what the PDF contains.
    """
    try:
        with PDFElementExtractor(pdf_path) as extractor:
            doc_elements = extractor.extract_all(extract_images=False)
            summary_data = extractor.get_summary(doc_elements)

        if json_output:
            click.echo(json.dumps(summary_data, indent=2))
        else:
            _print_summary(summary_data)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _print_summary(summary: dict):
    """Print element summary."""
    click.echo("\n" + "=" * 60)
    click.echo("PDF ELEMENT SUMMARY")
    click.echo("=" * 60)

    click.echo(f"\nFile: {summary['file_path']}")
    click.echo(f"Pages: {summary['page_count']}")
    click.echo(f"\nTotal Elements: {summary['total_elements']}")
    click.echo(f"  Text blocks: {summary['total_text_blocks']}")
    click.echo(f"  Images: {summary['total_images']}")
    click.echo(f"  Lines: {summary['total_lines']}")
    click.echo(f"  Rectangles: {summary['total_rects']}")
    click.echo(f"  Paths: {summary['total_paths']}")

    click.echo("\n--- Per Page ---")
    click.echo(f"{'Page':<6}{'Blocks':<8}{'Images':<8}{'Lines':<8}{'Rects':<8}{'Paths':<8}{'Total':<8}")
    click.echo("-" * 54)

    for page in summary["pages"][:50]:  # Limit display
        click.echo(
            f"{page['page']:<6}{page['text_blocks']:<8}{page['images']:<8}"
            f"{page['lines']:<8}{page['rects']:<8}{page['paths']:<8}{page['total']:<8}"
        )

    if len(summary["pages"]) > 50:
        click.echo(f"... and {len(summary['pages']) - 50} more pages")


@cli.command()
@click.argument("db_path", type=click.Path(exists=True))
def stats(db_path: str):
    """Show database statistics."""
    try:
        with ElementDatabase(db_path) as db:
            stats = db.get_stats()

        click.echo("\n" + "=" * 40)
        click.echo("DATABASE STATISTICS")
        click.echo("=" * 40)

        for table, count in stats.items():
            click.echo(f"  {table}: {count:,}")

        click.echo(f"\n  Total records: {sum(stats.values()):,}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("db_path", type=click.Path(exists=True))
@click.argument("query")
@click.option("--limit", "-n", default=20, help="Maximum results to show")
def search(db_path: str, query: str, limit: int):
    """Search for text in the database."""
    try:
        with ElementDatabase(db_path) as db:
            results = db.search_text(query)

        if not results:
            click.echo(f"No results for: {query}")
            return

        click.echo(f"\nFound {len(results)} matches for: {query}")
        click.echo("-" * 60)

        for i, result in enumerate(results[:limit]):
            click.echo(
                f"Page {result['page_number']}: \"{result['text']}\" "
                f"({result['font_name']}, {result['font_size']}pt)"
            )

        if len(results) > limit:
            click.echo(f"... and {len(results) - limit} more results")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("db_path", type=click.Path(exists=True))
@click.argument("page_number", type=int)
@click.option("--json-output", "-j", is_flag=True, help="Output as JSON")
def page(db_path: str, page_number: int, json_output: bool):
    """Show all elements on a specific page."""
    try:
        with ElementDatabase(db_path) as db:
            # Get document ID (assuming single document per DB for now)
            cursor = db._conn.cursor()
            cursor.execute("SELECT id FROM documents LIMIT 1")
            row = cursor.fetchone()
            if not row:
                click.echo("No documents in database")
                return

            doc_id = row[0]
            elements = db.get_page_elements(doc_id, page_number)

        if not elements:
            click.echo(f"Page {page_number} not found")
            return

        if json_output:
            click.echo(json.dumps(elements, indent=2, default=str))
        else:
            _print_page_elements(elements, page_number)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def _print_page_elements(elements: dict, page_number: int):
    """Print page elements summary."""
    click.echo(f"\n=== Page {page_number} ===")

    if elements.get("text_blocks"):
        click.echo(f"\nText Blocks ({len(elements['text_blocks'])}):")
        for block in elements["text_blocks"][:5]:
            text_preview = block["full_text"][:60].replace("\n", " ")
            click.echo(f"  - \"{text_preview}...\"")
        if len(elements["text_blocks"]) > 5:
            click.echo(f"  ... and {len(elements['text_blocks']) - 5} more")

    if elements.get("images"):
        click.echo(f"\nImages ({len(elements['images'])}):")
        for img in elements["images"][:5]:
            click.echo(f"  - {img['width']}x{img['height']} {img['format']} at ({img['x0']:.0f}, {img['y0']:.0f})")

    if elements.get("lines"):
        click.echo(f"\nLines: {len(elements['lines'])}")

    if elements.get("rects"):
        click.echo(f"Rectangles: {len(elements['rects'])}")

    if elements.get("paths"):
        click.echo(f"Paths: {len(elements['paths'])}")


@cli.command()
@click.argument("db_path", type=click.Path(exists=True))
@click.option("--images", "-i", type=click.Path(exists=True), help="Images directory")
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind to")
@click.option("--port", "-p", default=5000, type=int, help="Port to bind to")
def view(db_path: str, images: str, host: str, port: int):
    """Launch web viewer to explore extracted elements.

    Opens a browser-based UI to navigate pages, view images, and search text.
    """
    try:
        from .viewer import run_viewer
        run_viewer(db_path, images_dir=images, host=host, port=port)
    except ImportError as e:
        click.echo(f"Error: Flask is required for the viewer. Install with: pip install flask", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
