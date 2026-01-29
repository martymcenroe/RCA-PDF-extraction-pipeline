"""Table extraction module using pdfplumber for structured data extraction."""

import json
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

import pandas as pd
import pdfplumber

from .models import ExtractedTable, ExtractionResult


class TableExtractor:
    """Extract structured table data from PDFs."""

    HEADER_SIMILARITY_THRESHOLD = 0.8

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

    def extract_tables(
        self,
        page_numbers: Optional[list[int]] = None,
    ) -> ExtractionResult:
        """Extract tables from specified pages or all pages."""
        result = ExtractionResult(source_file=str(self.file_path))

        with pdfplumber.open(self.file_path) as pdf:
            pages_to_process = page_numbers or list(range(1, len(pdf.pages) + 1))
            result.pages_processed = len(pages_to_process)

            for page_num in pages_to_process:
                if page_num < 1 or page_num > len(pdf.pages):
                    result.warnings.append(f"Page {page_num} out of range, skipping")
                    continue

                try:
                    page = pdf.pages[page_num - 1]  # pdfplumber uses 0-based indexing
                    tables = self._extract_page_tables(page, page_num)

                    if tables:
                        result.tables.extend(tables)
                        result.pages_with_tables += 1

                except Exception as e:
                    result.warnings.append(f"Page {page_num}: {str(e)}")

        # Consolidate tables with similar headers
        if result.tables:
            self._consolidate_tables(result)

        return result

    def _extract_page_tables(
        self,
        page: pdfplumber.page.Page,
        page_num: int,
    ) -> list[ExtractedTable]:
        """Extract all tables from a single page."""
        tables = []

        # Try to find tables using pdfplumber's table detection
        found_tables = page.find_tables()

        for idx, table in enumerate(found_tables):
            try:
                raw_data = table.extract()
                if not raw_data or len(raw_data) < 2:
                    continue

                # First row as headers, rest as data
                headers = self._clean_row(raw_data[0])
                rows = [self._clean_row(row) for row in raw_data[1:]]

                # Filter out empty rows
                rows = [row for row in rows if any(cell.strip() for cell in row)]

                if headers and rows:
                    tables.append(ExtractedTable(
                        page_number=page_num,
                        table_index=idx,
                        headers=headers,
                        rows=rows,
                    ))

            except Exception:
                continue

        # If no tables found with find_tables, try extract_tables as fallback
        if not tables:
            try:
                raw_tables = page.extract_tables()
                for idx, raw_data in enumerate(raw_tables):
                    if not raw_data or len(raw_data) < 2:
                        continue

                    headers = self._clean_row(raw_data[0])
                    rows = [self._clean_row(row) for row in raw_data[1:]]
                    rows = [row for row in rows if any(cell.strip() for cell in row)]

                    if headers and rows:
                        tables.append(ExtractedTable(
                            page_number=page_num,
                            table_index=idx,
                            headers=headers,
                            rows=rows,
                            confidence=0.7,  # Lower confidence for fallback method
                        ))

            except Exception:
                pass

        return tables

    def _clean_row(self, row: list) -> list[str]:
        """Clean a row of table data."""
        cleaned = []
        for cell in row:
            if cell is None:
                cleaned.append("")
            else:
                # Convert to string and clean
                text = str(cell).strip()
                # Replace newlines and multiple spaces
                text = " ".join(text.split())
                cleaned.append(text)
        return cleaned

    def _consolidate_tables(self, result: ExtractionResult) -> None:
        """Consolidate tables with similar headers into a single dataset."""
        if not result.tables:
            return

        # Group tables by similar headers
        header_groups: list[tuple[list[str], list[ExtractedTable]]] = []

        for table in result.tables:
            matched = False
            for canonical_headers, group in header_groups:
                if self._headers_match(canonical_headers, table.headers):
                    group.append(table)
                    matched = True
                    break

            if not matched:
                header_groups.append((table.headers, [table]))

        # Use the largest group as the consolidated output
        if header_groups:
            largest_group = max(header_groups, key=lambda g: sum(t.row_count for t in g[1]))
            result.consolidated_headers = largest_group[0]

            for table in largest_group[1]:
                # Align rows to canonical headers
                aligned_rows = self._align_rows(
                    table.headers,
                    table.rows,
                    result.consolidated_headers,
                )
                result.consolidated_rows.extend(aligned_rows)

    def _headers_match(self, headers1: list[str], headers2: list[str]) -> bool:
        """Check if two header lists are similar enough to consolidate."""
        if len(headers1) != len(headers2):
            return False

        matches = 0
        for h1, h2 in zip(headers1, headers2):
            similarity = SequenceMatcher(None, h1.lower(), h2.lower()).ratio()
            if similarity >= self.HEADER_SIMILARITY_THRESHOLD:
                matches += 1

        return matches >= len(headers1) * 0.8

    def _align_rows(
        self,
        source_headers: list[str],
        rows: list[list[str]],
        target_headers: list[str],
    ) -> list[list[str]]:
        """Align rows from source headers to target headers."""
        if source_headers == target_headers:
            return rows

        # Create mapping from source index to target index
        mapping = {}
        for src_idx, src_header in enumerate(source_headers):
            best_match_idx = None
            best_similarity = 0
            for tgt_idx, tgt_header in enumerate(target_headers):
                similarity = SequenceMatcher(
                    None, src_header.lower(), tgt_header.lower()
                ).ratio()
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match_idx = tgt_idx

            if best_match_idx is not None and best_similarity >= self.HEADER_SIMILARITY_THRESHOLD:
                mapping[src_idx] = best_match_idx

        # Apply mapping to rows
        aligned = []
        for row in rows:
            new_row = [""] * len(target_headers)
            for src_idx, value in enumerate(row):
                if src_idx in mapping:
                    new_row[mapping[src_idx]] = value
            aligned.append(new_row)

        return aligned

    def to_dataframe(self, result: ExtractionResult) -> pd.DataFrame:
        """Convert extraction result to pandas DataFrame."""
        if not result.consolidated_headers or not result.consolidated_rows:
            return pd.DataFrame()

        return pd.DataFrame(
            result.consolidated_rows,
            columns=result.consolidated_headers,
        )

    def save_csv(self, result: ExtractionResult, output_path: str) -> str:
        """Save extraction result to CSV file."""
        df = self.to_dataframe(result)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        return str(output_path)

    def save_json(self, result: ExtractionResult, output_path: str) -> str:
        """Save extraction result to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "source_file": result.source_file,
            "pages_processed": result.pages_processed,
            "pages_with_tables": result.pages_with_tables,
            "total_tables": len(result.tables),
            "total_rows": len(result.consolidated_rows),
            "headers": result.consolidated_headers,
            "data": result.consolidated_rows,
            "tables_by_page": [
                {
                    "page": t.page_number,
                    "table_index": t.table_index,
                    "headers": t.headers,
                    "row_count": t.row_count,
                    "confidence": t.confidence,
                }
                for t in result.tables
            ],
            "warnings": result.warnings,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return str(output_path)

    def get_summary(self, result: ExtractionResult) -> dict:
        """Get extraction summary."""
        return {
            "source_file": result.source_file,
            "pages_processed": result.pages_processed,
            "pages_with_tables": result.pages_with_tables,
            "total_tables_found": len(result.tables),
            "consolidated_columns": len(result.consolidated_headers),
            "consolidated_rows": len(result.consolidated_rows),
            "headers": result.consolidated_headers,
            "tables_by_page": {
                t.page_number: {
                    "table_index": t.table_index,
                    "columns": t.column_count,
                    "rows": t.row_count,
                    "confidence": t.confidence,
                }
                for t in result.tables
            },
            "warnings": result.warnings,
        }
