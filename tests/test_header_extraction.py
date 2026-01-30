"""Tests for Issue #13: Extract Headers from PDF."""

import pytest
from src.core_analysis import CoreAnalysisExtractor


class TestHeaderExtraction:
    """Tests for dynamic header extraction from PDF."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with test database."""
        db_path = "data/output/extended/W20552_elements.db"
        return CoreAnalysisExtractor(db_path)

    def test_extracts_11_headers_plus_page_number(self, extractor):
        """T01: Extracts 11 PDF headers plus Page Number."""
        headers = extractor.get_extracted_headers()
        assert len(headers) == 12

    def test_first_header_is_core_number(self, extractor):
        """T02: First header is 'Core Number'."""
        headers = extractor.get_extracted_headers()
        assert headers[0] == "Core Number"

    def test_permeability_air_full_text(self, extractor):
        """T03: Permeability Air header has full text."""
        headers = extractor.get_extracted_headers()
        assert headers[3] == "Permeability, millidarcys to Air"

    def test_permeability_klinkenberg_spelled_out(self, extractor):
        """T04: Klinkenberg is spelled out, not abbreviated."""
        headers = extractor.get_extracted_headers()
        assert "Klinkenberg" in headers[4]
        assert "Klink" not in headers[4] or "Klinkenberg" in headers[4]

    def test_porosity_uses_percent_not_symbol(self, extractor):
        """T05: Porosity headers use 'percent' not '%'."""
        headers = extractor.get_extracted_headers()
        assert "percent" in headers[5]  # Porosity Ambient
        assert "%" not in headers[5]

    def test_depth_header_correct(self, extractor):
        """T06: Depth header is 'Depth, feet' not 'Depth (ft)'."""
        headers = extractor.get_extracted_headers()
        assert headers[2] == "Depth, feet"

    def test_grain_density_units(self, extractor):
        """T07: Grain Density uses 'gm/cc' not 'g/cc'."""
        headers = extractor.get_extracted_headers()
        assert "gm/cc" in headers[7]

    def test_fluid_saturations_headers(self, extractor):
        """T08: Fluid Saturations headers have full prefix."""
        headers = extractor.get_extracted_headers()
        assert headers[8] == "Fluid Saturations, percent Water"
        assert headers[9] == "Fluid Saturations, percent Oil"
        assert headers[10] == "Fluid Saturations, percent Total"

    def test_last_header_is_page_number(self, extractor):
        """T09: Last header is 'Page Number' (added by extraction)."""
        headers = extractor.get_extracted_headers()
        assert headers[-1] == "Page Number"

    def test_headers_cached(self, extractor):
        """T10: Headers are cached after first extraction."""
        headers1 = extractor.get_extracted_headers()
        headers2 = extractor.get_extracted_headers()
        assert headers1 is headers2  # Same object, not re-extracted
