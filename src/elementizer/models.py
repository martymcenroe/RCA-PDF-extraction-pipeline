"""Data models for PDF element extraction."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ElementType(Enum):
    """Types of PDF elements."""
    TEXT_BLOCK = "text_block"
    TEXT_LINE = "text_line"
    TEXT_SPAN = "text_span"
    IMAGE = "image"
    LINE = "line"
    RECTANGLE = "rect"
    CURVE = "curve"
    PATH = "path"
    ANNOTATION = "annotation"


@dataclass
class BoundingBox:
    """Bounding box coordinates."""
    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_dict(self) -> dict:
        return {"x0": self.x0, "y0": self.y0, "x1": self.x1, "y1": self.y1}


@dataclass
class TextSpan:
    """A span of text with consistent formatting."""
    text: str
    bbox: BoundingBox
    font_name: Optional[str] = None
    font_size: Optional[float] = None
    color: Optional[int] = None
    flags: int = 0  # bold, italic, etc.

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "bbox": self.bbox.to_dict(),
            "font_name": self.font_name,
            "font_size": self.font_size,
            "color": self.color,
            "flags": self.flags,
        }


@dataclass
class TextLine:
    """A line of text containing spans."""
    bbox: BoundingBox
    spans: list[TextSpan] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(span.text for span in self.spans)

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "text": self.text,
            "spans": [s.to_dict() for s in self.spans],
        }


@dataclass
class TextBlock:
    """A block of text containing lines."""
    bbox: BoundingBox
    lines: list[TextLine] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "text": self.text,
            "lines": [l.to_dict() for l in self.lines],
        }


@dataclass
class ImageElement:
    """An image extracted from the PDF."""
    bbox: BoundingBox
    xref: int  # PDF internal reference
    width: int
    height: int
    colorspace: Optional[str] = None
    bpc: Optional[int] = None  # bits per component
    image_data: Optional[bytes] = None
    file_path: Optional[str] = None
    format: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "xref": self.xref,
            "width": self.width,
            "height": self.height,
            "colorspace": self.colorspace,
            "bpc": self.bpc,
            "format": self.format,
            "file_path": self.file_path,
        }


@dataclass
class LineElement:
    """A vector line."""
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    width: float = 1.0
    color: Optional[tuple] = None
    stroke_opacity: float = 1.0

    @property
    def bbox(self) -> BoundingBox:
        return BoundingBox(
            min(self.start_x, self.end_x),
            min(self.start_y, self.end_y),
            max(self.start_x, self.end_x),
            max(self.start_y, self.end_y),
        )

    @property
    def is_horizontal(self) -> bool:
        return abs(self.end_y - self.start_y) < 2

    @property
    def is_vertical(self) -> bool:
        return abs(self.end_x - self.start_x) < 2

    def to_dict(self) -> dict:
        return {
            "start": {"x": self.start_x, "y": self.start_y},
            "end": {"x": self.end_x, "y": self.end_y},
            "width": self.width,
            "color": self.color,
            "stroke_opacity": self.stroke_opacity,
            "is_horizontal": self.is_horizontal,
            "is_vertical": self.is_vertical,
        }


@dataclass
class RectElement:
    """A rectangle shape."""
    bbox: BoundingBox
    fill_color: Optional[tuple] = None
    stroke_color: Optional[tuple] = None
    stroke_width: float = 1.0
    fill_opacity: float = 1.0
    stroke_opacity: float = 1.0

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "fill_color": self.fill_color,
            "stroke_color": self.stroke_color,
            "stroke_width": self.stroke_width,
            "fill_opacity": self.fill_opacity,
            "stroke_opacity": self.stroke_opacity,
        }


@dataclass
class PathElement:
    """A complex path/curve."""
    items: list[dict]  # List of path commands
    bbox: BoundingBox
    fill_color: Optional[tuple] = None
    stroke_color: Optional[tuple] = None

    def to_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_dict(),
            "items": self.items,
            "fill_color": self.fill_color,
            "stroke_color": self.stroke_color,
        }


@dataclass
class PageElements:
    """All elements from a single page."""
    page_number: int
    width: float
    height: float
    rotation: int = 0
    text_blocks: list[TextBlock] = field(default_factory=list)
    images: list[ImageElement] = field(default_factory=list)
    lines: list[LineElement] = field(default_factory=list)
    rects: list[RectElement] = field(default_factory=list)
    paths: list[PathElement] = field(default_factory=list)

    @property
    def element_count(self) -> int:
        return (
            len(self.text_blocks) +
            len(self.images) +
            len(self.lines) +
            len(self.rects) +
            len(self.paths)
        )

    def to_dict(self) -> dict:
        return {
            "page_number": self.page_number,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "text_blocks": [tb.to_dict() for tb in self.text_blocks],
            "images": [img.to_dict() for img in self.images],
            "lines": [ln.to_dict() for ln in self.lines],
            "rects": [r.to_dict() for r in self.rects],
            "paths": [p.to_dict() for p in self.paths],
            "element_count": self.element_count,
        }


@dataclass
class DocumentElements:
    """All elements from a PDF document."""
    file_path: str
    page_count: int
    metadata: dict = field(default_factory=dict)
    pages: list[PageElements] = field(default_factory=list)

    @property
    def total_elements(self) -> int:
        return sum(p.element_count for p in self.pages)

    @property
    def total_images(self) -> int:
        return sum(len(p.images) for p in self.pages)

    @property
    def total_text_blocks(self) -> int:
        return sum(len(p.text_blocks) for p in self.pages)

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "page_count": self.page_count,
            "metadata": self.metadata,
            "total_elements": self.total_elements,
            "total_images": self.total_images,
            "total_text_blocks": self.total_text_blocks,
            "pages": [p.to_dict() for p in self.pages],
        }
