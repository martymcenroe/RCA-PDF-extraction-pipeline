"""Tests for header preservation in table extraction."""

import csv
import tempfile
from pathlib import Path

import pytest

from src.models import ExtractedTable, ExtractionResult
from src.table_extractor import TableExtractor


class TestExtractedTableDualHeaders:
    """Tests for dual-header architecture in ExtractedTable."""

    def test_original_headers_default_empty(self):
        """Original headers should default to empty list."""
        table = ExtractedTable(
            page_number=1,
            table_index=0,
            headers=["col1", "col2"],
            rows=[["a", "b"]],
        )
        assert table.original_headers == []

    def test_original_headers_set_explicitly(self):
        """Original headers can be set explicitly."""
        table = ExtractedTable(
            page_number=1,
            table_index=0,
            headers=["col1", "col2"],
            original_headers=["Column 1", "Column 2"],
            rows=[["a", "b"]],
        )
        assert table.original_headers == ["Column 1", "Column 2"]
        assert table.headers == ["col1", "col2"]

    def test_source_header_rows_default(self):
        """Source header rows should default to 1."""
        table = ExtractedTable(
            page_number=1,
            table_index=0,
            headers=["col1"],
            rows=[["a"]],
        )
        assert table.source_header_rows == 1


class TestExtractionResultDualHeaders:
    """Tests for dual-header architecture in ExtractionResult."""

    def test_original_headers_default_empty(self):
        """Original headers should default to empty list."""
        result = ExtractionResult(source_file="test.pdf")
        assert result.original_headers == []

    def test_original_headers_set_explicitly(self):
        """Original headers can be set explicitly."""
        result = ExtractionResult(
            source_file="test.pdf",
            consolidated_headers=["col1", "col2"],
            original_headers=["Column 1", "Column 2"],
        )
        assert result.original_headers == ["Column 1", "Column 2"]
        assert result.consolidated_headers == ["col1", "col2"]


class TestTableExtractorSaveCSV:
    """Tests for CSV output with original headers."""

    def test_save_csv_uses_original_headers_by_default(self):
        """save_csv should use original headers when available."""
        # Create a result with both header types
        result = ExtractionResult(
            source_file="test.pdf",
            consolidated_headers=["depth_feet", "permeability_md"],
            original_headers=["Depth (ft)", "Permeability (md)"],
            consolidated_rows=[["100.5", "0.01"], ["101.5", "0.02"]],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            # Use a minimal extractor just for save_csv
            extractor = TableExtractor.__new__(TableExtractor)
            extractor.save_csv(result, output_path, use_original_headers=True)

            # Read back and verify headers
            with open(output_path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader)

            assert headers == ["Depth (ft)", "Permeability (md)"]
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_save_csv_can_use_canonical_headers(self):
        """save_csv should use canonical headers when requested."""
        result = ExtractionResult(
            source_file="test.pdf",
            consolidated_headers=["depth_feet", "permeability_md"],
            original_headers=["Depth (ft)", "Permeability (md)"],
            consolidated_rows=[["100.5", "0.01"]],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            extractor = TableExtractor.__new__(TableExtractor)
            extractor.save_csv(result, output_path, use_original_headers=False)

            with open(output_path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader)

            assert headers == ["depth_feet", "permeability_md"]
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_save_csv_sanitizes_dangerous_headers(self):
        """save_csv should sanitize headers with formula characters."""
        result = ExtractionResult(
            source_file="test.pdf",
            consolidated_headers=["formula", "normal"],
            original_headers=["=SUM(A1)", "Normal Header"],
            consolidated_rows=[["1", "2"]],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            extractor = TableExtractor.__new__(TableExtractor)
            extractor.save_csv(result, output_path, use_original_headers=True)

            with open(output_path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                headers = next(reader)

            # Formula character should be escaped
            assert headers == ["'=SUM(A1)", "Normal Header"]
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_save_csv_includes_bom(self):
        """save_csv should include UTF-8 BOM for Excel."""
        result = ExtractionResult(
            source_file="test.pdf",
            consolidated_headers=["col1"],
            original_headers=["Column 1"],
            consolidated_rows=[["data"]],
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            extractor = TableExtractor.__new__(TableExtractor)
            extractor.save_csv(result, output_path)

            with open(output_path, "rb") as f:
                first_bytes = f.read(3)

            assert first_bytes == b"\xef\xbb\xbf"
        finally:
            Path(output_path).unlink(missing_ok=True)


class TestAlignmentInvariant:
    """Tests for header-row alignment invariant."""

    def test_alignment_invariant_holds(self):
        """All rows should have same length as headers."""
        result = ExtractionResult(
            source_file="test.pdf",
            consolidated_headers=["a", "b", "c"],
            original_headers=["A", "B", "C"],
            consolidated_rows=[
                ["1", "2", "3"],
                ["4", "5", "6"],
            ],
        )

        # Verify invariant
        assert len(result.consolidated_headers) == len(result.original_headers)
        for row in result.consolidated_rows:
            assert len(row) == len(result.consolidated_headers)
