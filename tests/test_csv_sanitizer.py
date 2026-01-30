"""Tests for CSV injection protection."""

import csv
import tempfile
from pathlib import Path

import pytest

from src.output.csv_sanitizer import sanitize_csv_value, write_csv_with_bom


class TestSanitizeCsvValue:
    """Tests for sanitize_csv_value function."""

    def test_equals_sign_escaped(self):
        """Headers starting with = should be escaped."""
        assert sanitize_csv_value("=SUM(A1)") == "'=SUM(A1)"

    def test_plus_sign_escaped(self):
        """Headers starting with + should be escaped."""
        assert sanitize_csv_value("+value") == "'+value"

    def test_minus_sign_escaped(self):
        """Headers starting with - should be escaped."""
        assert sanitize_csv_value("-negative") == "'-negative"

    def test_at_sign_escaped(self):
        """Headers starting with @ should be escaped."""
        assert sanitize_csv_value("@mention") == "'@mention"

    def test_normal_header_unchanged(self):
        """Normal headers should not be modified."""
        assert sanitize_csv_value("Depth (ft)") == "Depth (ft)"
        assert sanitize_csv_value("Permeability (md) | Air") == "Permeability (md) | Air"
        assert sanitize_csv_value("Sample Number") == "Sample Number"

    def test_empty_string_unchanged(self):
        """Empty strings should pass through."""
        assert sanitize_csv_value("") == ""

    def test_whitespace_preserved(self):
        """Whitespace should be preserved."""
        assert sanitize_csv_value("  Header  ") == "  Header  "

    def test_formula_chars_in_middle_unchanged(self):
        """Formula chars in middle of string should not be escaped."""
        assert sanitize_csv_value("A+B") == "A+B"
        assert sanitize_csv_value("A=B") == "A=B"
        assert sanitize_csv_value("A-B") == "A-B"
        assert sanitize_csv_value("user@example.com") == "user@example.com"

    def test_unicode_preserved(self):
        """Unicode characters should be preserved."""
        assert sanitize_csv_value("Porosity (%)") == "Porosity (%)"
        assert sanitize_csv_value("Température") == "Température"


class TestWriteCsvWithBom:
    """Tests for write_csv_with_bom function."""

    def test_bom_present(self):
        """Output file should start with UTF-8 BOM."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            headers = ["A", "B", "C"]
            rows = [["1", "2", "3"]]
            write_csv_with_bom(rows, output_path, headers)

            # Read raw bytes to check BOM
            with open(output_path, "rb") as f:
                first_bytes = f.read(3)

            # UTF-8 BOM is EF BB BF
            assert first_bytes == b"\xef\xbb\xbf"
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_headers_sanitized_by_default(self):
        """Headers should be sanitized by default."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            headers = ["=Formula", "Normal", "+Plus"]
            rows = [["1", "2", "3"]]
            write_csv_with_bom(rows, output_path, headers)

            with open(output_path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                written_headers = next(reader)

            assert written_headers == ["'=Formula", "Normal", "'+Plus"]
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_sanitization_can_be_disabled(self):
        """Header sanitization can be disabled."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            headers = ["=Formula", "Normal"]
            rows = [["1", "2"]]
            write_csv_with_bom(rows, output_path, headers, sanitize_headers=False)

            with open(output_path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                written_headers = next(reader)

            assert written_headers == ["=Formula", "Normal"]
        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_data_rows_written_correctly(self):
        """Data rows should be written correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            headers = ["A", "B"]
            rows = [["1", "2"], ["3", "4"], ["5", "6"]]
            write_csv_with_bom(rows, output_path, headers)

            with open(output_path, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                all_rows = list(reader)

            assert len(all_rows) == 4  # 1 header + 3 data
            assert all_rows[0] == ["A", "B"]
            assert all_rows[1] == ["1", "2"]
            assert all_rows[2] == ["3", "4"]
            assert all_rows[3] == ["5", "6"]
        finally:
            Path(output_path).unlink(missing_ok=True)
