"""
Pytest configuration and shared fixtures.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tests.fixtures.sample_text_blocks import (
    TABLE_PAGE_TEXT,
    PLOT_PAGE_TEXT,
    COVER_PAGE_TEXT,
    TEXT_PAGE_TEXT,
    OTHER_PAGE_TEXT,
    SAMPLE_NORMAL,
    SAMPLE_FRACTURE,
    SAMPLE_BELOW_DETECTION,
    SAMPLE_NO_SATURATION,
    MULTI_SAMPLE_TEXT,
)


@pytest.fixture
def table_page_text():
    """Text from a table page (should classify as 'table')."""
    return TABLE_PAGE_TEXT


@pytest.fixture
def plot_page_text():
    """Text from a plot page (should classify as 'plot')."""
    return PLOT_PAGE_TEXT


@pytest.fixture
def cover_page_text():
    """Text from a cover page (should classify as 'cover')."""
    return COVER_PAGE_TEXT


@pytest.fixture
def text_page_text():
    """Text from a narrative page (should classify as 'text')."""
    return TEXT_PAGE_TEXT


@pytest.fixture
def other_page_text():
    """Minimal text page (should classify as 'other')."""
    return OTHER_PAGE_TEXT


@pytest.fixture
def sample_normal():
    """Normal sample with all fields populated."""
    return SAMPLE_NORMAL


@pytest.fixture
def sample_fracture():
    """Fracture sample with + for permeability."""
    return SAMPLE_FRACTURE


@pytest.fixture
def sample_below_detection():
    """Sample with permeability below detection limit."""
    return SAMPLE_BELOW_DETECTION


@pytest.fixture
def sample_no_saturation():
    """Sample with ** for saturation values."""
    return SAMPLE_NO_SATURATION


@pytest.fixture
def multi_sample_text():
    """Multiple samples for extraction testing."""
    return MULTI_SAMPLE_TEXT
