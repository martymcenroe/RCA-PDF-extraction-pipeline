"""Tests for Issue #4: Improved Footnote Symbol Handling.

Test scenarios:
T01 - Fracture (f) in sample_number preserved
T02 - Fracture (F) in sample_number preserved
T03 - + replicated to both perm columns
T04 - <0.0001 replicated to both perm columns
T05 - ** replicated to all sat columns
T06 - No change to normal rows
T07 - Baseline row count (integration)
T08 - Original headers preserved (integration)
T10 - MAX_SAMPLE_LINES exceeded
T11 - Output path validation
"""

import pytest
from src.core_analysis import (
    CoreAnalysisExtractor,
    FRACTURE_INDICATOR_RE,
    MAX_SAMPLE_LINES,
)
from tests.fixtures.stub_samples import (
    STUB_SAMPLE_LINES_F_LOWERCASE,
    STUB_SAMPLE_LINES_F_UPPERCASE,
    STUB_SAMPLE_LINES_DETECTION_LIMIT,
    STUB_SAMPLE_LINES_NORMAL,
    STUB_SAMPLE_LINES_PLUS,
    STUB_SAMPLE_LINES_STAR_SATURATION,
    STUB_SAMPLE_LINES_TOO_LONG,
)


class TestFractureIndicatorExtraction:
    """Tests for fracture indicator extraction (T01, T02)."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance without database."""
        # Create instance without calling __init__ (no db needed for unit tests)
        ext = object.__new__(CoreAnalysisExtractor)
        return ext

    def test_t01_fracture_f_lowercase_preserved(self, extractor):
        """T01: Fracture (f) preserved in sample_number."""
        sample = extractor._parse_sample_lines(STUB_SAMPLE_LINES_F_LOWERCASE, page_num=39)

        assert sample is not None
        assert sample.sample_number == "1-9(f)"

    def test_t02_fracture_f_uppercase_preserved(self, extractor):
        """T02: Fracture (F) preserved in sample_number."""
        sample = extractor._parse_sample_lines(STUB_SAMPLE_LINES_F_UPPERCASE, page_num=39)

        assert sample is not None
        assert sample.sample_number == "1-2(F)"

    def test_fracture_indicator_regex(self):
        """Test the compiled regex matches correctly."""
        assert FRACTURE_INDICATOR_RE.search("1-9(f)")
        assert FRACTURE_INDICATOR_RE.search("1-2(F)")
        assert not FRACTURE_INDICATOR_RE.search("1-8")
        assert not FRACTURE_INDICATOR_RE.search("1-9")


class TestMergedCellExpansion:
    """Tests for merged cell indicator expansion (T03, T04, T05)."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance without database."""
        ext = object.__new__(CoreAnalysisExtractor)
        return ext

    def test_t03_plus_replicated_to_both_perm(self, extractor):
        """T03: + replicated to both permeability columns."""
        sample = extractor._parse_sample_lines(STUB_SAMPLE_LINES_PLUS, page_num=39)

        assert sample is not None
        assert sample.permeability_air_md == "+"
        assert sample.permeability_klink_md == "+"

    def test_t04_detection_limit_replicated(self, extractor):
        """T04: <0.0001 replicated to both permeability columns."""
        sample = extractor._parse_sample_lines(STUB_SAMPLE_LINES_DETECTION_LIMIT, page_num=39)

        assert sample is not None
        assert sample.permeability_air_md == "<0.0001"
        assert sample.permeability_klink_md == "<0.0001"

    def test_t05_star_replicated_to_all_sat(self, extractor):
        """T05: ** replicated to all three saturation columns."""
        sample = extractor._parse_sample_lines(STUB_SAMPLE_LINES_STAR_SATURATION, page_num=39)

        assert sample is not None
        assert sample.saturation_water_pct == "**"
        assert sample.saturation_oil_pct == "**"
        assert sample.saturation_total_pct == "**"


class TestNormalRows:
    """Tests for normal rows without special indicators (T06)."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance without database."""
        ext = object.__new__(CoreAnalysisExtractor)
        return ext

    def test_t06_normal_rows_unchanged(self, extractor):
        """T06: Normal numeric rows are parsed correctly."""
        sample = extractor._parse_sample_lines(STUB_SAMPLE_LINES_NORMAL, page_num=39)

        assert sample is not None
        assert sample.permeability_air_md == 0.0017
        assert sample.permeability_klink_md == 0.0005


class TestSafetyChecks:
    """Tests for safety constraints (T10, T11)."""

    @pytest.fixture
    def extractor(self):
        """Create extractor instance without database."""
        ext = object.__new__(CoreAnalysisExtractor)
        return ext

    def test_t10_max_sample_lines_exceeded(self, extractor):
        """T10: Returns None when MAX_SAMPLE_LINES exceeded."""
        sample = extractor._parse_sample_lines(STUB_SAMPLE_LINES_TOO_LONG, page_num=39)

        assert sample is None

    def test_t11_output_path_validation_rejects_outside(self, extractor):
        """T11: Raises ValueError for paths outside allowed directories."""
        with pytest.raises(ValueError, match="outside allowed directories"):
            extractor._validate_output_path("/etc/passwd")

    def test_output_path_validation_accepts_tmp(self, extractor):
        """Output path validation accepts /tmp."""
        # Should not raise
        result = extractor._validate_output_path("/tmp/test.csv")
        assert result is True

    def test_output_path_validation_accepts_project(self, extractor):
        """Output path validation accepts project directory."""
        result = extractor._validate_output_path(
            "/c/Users/mcwiz/Projects/RCA-PDF-extraction-pipeline/data/output/test.csv"
        )
        assert result is True
