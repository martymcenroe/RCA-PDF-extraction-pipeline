"""Data classes for PDF dissection tool."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PageType(Enum):
    """Classification of page content type."""
    COVER = "cover"
    TABLE = "table"
    NARRATIVE = "narrative"
    MIXED = "mixed"
    BLANK = "blank"
    FIGURE = "figure"
    UNKNOWN = "unknown"


@dataclass
class TextBlock:
    """Represents a text block on a page."""
    x0: float
    y0: float
    x1: float
    y1: float
    text: str

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass
class LineInfo:
    """Represents a line (rule) on a page."""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def is_horizontal(self) -> bool:
        return abs(self.y1 - self.y0) < 2

    @property
    def is_vertical(self) -> bool:
        return abs(self.x1 - self.x0) < 2

    @property
    def length(self) -> float:
        return ((self.x1 - self.x0) ** 2 + (self.y1 - self.y0) ** 2) ** 0.5


@dataclass
class ImageInfo:
    """Represents an image on a page."""
    x0: float
    y0: float
    x1: float
    y1: float
    width: int
    height: int

    @property
    def area(self) -> float:
        return (self.x1 - self.x0) * (self.y1 - self.y0)


@dataclass
class PageInfo:
    """Detailed information about a single page."""
    page_number: int
    width: float
    height: float
    text_blocks: list[TextBlock] = field(default_factory=list)
    lines: list[LineInfo] = field(default_factory=list)
    images: list[ImageInfo] = field(default_factory=list)
    text_content: str = ""
    char_count: int = 0
    word_count: int = 0

    @property
    def horizontal_lines(self) -> list[LineInfo]:
        return [line for line in self.lines if line.is_horizontal]

    @property
    def vertical_lines(self) -> list[LineInfo]:
        return [line for line in self.lines if line.is_vertical]

    @property
    def line_count(self) -> int:
        return len(self.lines)

    @property
    def image_count(self) -> int:
        return len(self.images)


@dataclass
class PageClassification:
    """Classification result for a page."""
    page_number: int
    page_type: PageType
    confidence: float
    horizontal_line_count: int
    vertical_line_count: int
    text_block_count: int
    image_coverage: float
    notes: str = ""


@dataclass
class PDFMetadata:
    """PDF document metadata."""
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None
    creation_date: Optional[str] = None
    modification_date: Optional[str] = None
    keywords: Optional[str] = None


@dataclass
class PDFStructure:
    """Complete PDF structure and metadata."""
    file_path: str
    page_count: int
    pdf_version: Optional[str] = None
    metadata: PDFMetadata = field(default_factory=PDFMetadata)
    pages: list[PageInfo] = field(default_factory=list)
    fonts: list[str] = field(default_factory=list)
    file_size_bytes: int = 0
    is_encrypted: bool = False
    has_forms: bool = False
    anomalies: list[str] = field(default_factory=list)


@dataclass
class ExtractedTable:
    """A table extracted from a page.

    Supports dual-header architecture:
    - headers: Canonical names for internal code access (e.g., "permeability_air_md")
    - original_headers: Original PDF text for CSV output (e.g., "Permeability (md) | Air")
    """
    page_number: int
    table_index: int
    headers: list[str]  # Canonical headers for code access
    rows: list[list[str]]
    confidence: float = 1.0
    original_headers: list[str] = field(default_factory=list)  # Original PDF headers for output
    source_header_rows: int = 1  # Number of header rows flattened

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.headers) if self.headers else 0


@dataclass
class ExtractionResult:
    """Result of table extraction from entire PDF.

    Supports dual-header architecture:
    - consolidated_headers: Canonical names for internal code access
    - original_headers: Original PDF text for CSV output
    """
    source_file: str
    tables: list[ExtractedTable] = field(default_factory=list)
    consolidated_headers: list[str] = field(default_factory=list)  # Canonical headers
    original_headers: list[str] = field(default_factory=list)  # Original PDF headers
    consolidated_rows: list[list[str]] = field(default_factory=list)
    pages_processed: int = 0
    pages_with_tables: int = 0
    warnings: list[str] = field(default_factory=list)
