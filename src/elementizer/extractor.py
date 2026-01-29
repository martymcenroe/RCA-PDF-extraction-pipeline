"""PDF element extraction using PyMuPDF."""

import os
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from .models import (
    BoundingBox,
    DocumentElements,
    ImageElement,
    LineElement,
    PageElements,
    PathElement,
    RectElement,
    TextBlock,
    TextLine,
    TextSpan,
)


class PDFElementExtractor:
    """Extract all elements from a PDF document."""

    def __init__(self, file_path: str, image_output_dir: Optional[str] = None):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        self.image_output_dir = Path(image_output_dir) if image_output_dir else None
        if self.image_output_dir:
            self.image_output_dir.mkdir(parents=True, exist_ok=True)

        self._doc: Optional[fitz.Document] = None

    def __enter__(self):
        self._doc = fitz.open(self.file_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._doc:
            self._doc.close()

    def extract_all(self, extract_images: bool = True) -> DocumentElements:
        """Extract all elements from the PDF."""
        if not self._doc:
            raise RuntimeError("Must use as context manager")

        doc_elements = DocumentElements(
            file_path=str(self.file_path),
            page_count=len(self._doc),
            metadata=self._extract_metadata(),
        )

        for page_num in range(len(self._doc)):
            page_elements = self._extract_page(page_num, extract_images)
            doc_elements.pages.append(page_elements)

        return doc_elements

    def _extract_metadata(self) -> dict:
        """Extract document metadata."""
        meta = self._doc.metadata or {}
        return {
            "title": meta.get("title"),
            "author": meta.get("author"),
            "subject": meta.get("subject"),
            "creator": meta.get("creator"),
            "producer": meta.get("producer"),
            "creation_date": meta.get("creationDate"),
            "modification_date": meta.get("modDate"),
            "keywords": meta.get("keywords"),
            "format": meta.get("format"),
            "encryption": meta.get("encryption"),
        }

    def _extract_page(self, page_num: int, extract_images: bool) -> PageElements:
        """Extract all elements from a single page."""
        page = self._doc[page_num]
        rect = page.rect

        page_elements = PageElements(
            page_number=page_num + 1,
            width=rect.width,
            height=rect.height,
            rotation=page.rotation,
        )

        # Extract text with full structure
        self._extract_text_blocks(page, page_elements)

        # Extract images
        if extract_images:
            self._extract_images(page, page_elements)

        # Extract vector graphics (lines, rects, paths)
        self._extract_drawings(page, page_elements)

        return page_elements

    def _extract_text_blocks(self, page: fitz.Page, page_elements: PageElements):
        """Extract text blocks with full span/line structure."""
        try:
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:  # Skip non-text blocks
                    continue

                bbox = block.get("bbox", (0, 0, 0, 0))
                text_block = TextBlock(
                    bbox=BoundingBox(bbox[0], bbox[1], bbox[2], bbox[3])
                )

                for line_data in block.get("lines", []):
                    line_bbox = line_data.get("bbox", (0, 0, 0, 0))
                    text_line = TextLine(
                        bbox=BoundingBox(line_bbox[0], line_bbox[1], line_bbox[2], line_bbox[3])
                    )

                    for span_data in line_data.get("spans", []):
                        span_bbox = span_data.get("bbox", (0, 0, 0, 0))
                        text_span = TextSpan(
                            text=span_data.get("text", ""),
                            bbox=BoundingBox(span_bbox[0], span_bbox[1], span_bbox[2], span_bbox[3]),
                            font_name=span_data.get("font"),
                            font_size=span_data.get("size"),
                            color=span_data.get("color"),
                            flags=span_data.get("flags", 0),
                        )
                        text_line.spans.append(text_span)

                    if text_line.spans:
                        text_block.lines.append(text_line)

                if text_block.lines:
                    page_elements.text_blocks.append(text_block)

        except Exception as e:
            # Log but continue
            pass

    def _extract_images(self, page: fitz.Page, page_elements: PageElements):
        """Extract images from the page."""
        try:
            image_list = page.get_images(full=True)

            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]

                    # Get image bounding box on page
                    try:
                        img_rect = page.get_image_bbox(xref)
                        bbox = BoundingBox(img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1)
                    except Exception:
                        bbox = BoundingBox(0, 0, 0, 0)

                    # Extract image data
                    base_image = self._doc.extract_image(xref)
                    if not base_image:
                        continue

                    image_element = ImageElement(
                        bbox=bbox,
                        xref=xref,
                        width=base_image.get("width", 0),
                        height=base_image.get("height", 0),
                        colorspace=base_image.get("colorspace", None),
                        bpc=base_image.get("bpc", None),
                        format=base_image.get("ext", "png"),
                        image_data=base_image.get("image"),
                    )

                    # Save image to file if output dir specified
                    if self.image_output_dir and image_element.image_data:
                        image_filename = f"page{page_elements.page_number:04d}_img{img_index:04d}.{image_element.format}"
                        image_path = self.image_output_dir / image_filename
                        with open(image_path, "wb") as f:
                            f.write(image_element.image_data)
                        image_element.file_path = str(image_path)
                        # Clear image data from memory after saving
                        image_element.image_data = None

                    page_elements.images.append(image_element)

                except Exception:
                    continue

        except Exception:
            pass

    def _extract_drawings(self, page: fitz.Page, page_elements: PageElements):
        """Extract vector drawings (lines, rectangles, paths)."""
        try:
            drawings = page.get_drawings()

            for drawing in drawings:
                fill_color = drawing.get("fill")
                stroke_color = drawing.get("color")
                stroke_width = drawing.get("width", 1.0)
                fill_opacity = drawing.get("fill_opacity", 1.0)
                stroke_opacity = drawing.get("stroke_opacity", 1.0)

                for item in drawing.get("items", []):
                    item_type = item[0]

                    if item_type == "l":  # Line
                        start_point = item[1]
                        end_point = item[2]
                        line_element = LineElement(
                            start_x=start_point.x,
                            start_y=start_point.y,
                            end_x=end_point.x,
                            end_y=end_point.y,
                            width=stroke_width,
                            color=stroke_color,
                            stroke_opacity=stroke_opacity,
                        )
                        page_elements.lines.append(line_element)

                    elif item_type == "re":  # Rectangle
                        rect = item[1]
                        rect_element = RectElement(
                            bbox=BoundingBox(rect.x0, rect.y0, rect.x1, rect.y1),
                            fill_color=fill_color,
                            stroke_color=stroke_color,
                            stroke_width=stroke_width,
                            fill_opacity=fill_opacity,
                            stroke_opacity=stroke_opacity,
                        )
                        page_elements.rects.append(rect_element)

                    elif item_type in ("c", "qu"):  # Curve or quad
                        # Store as path with items
                        path_items = [{"type": item_type, "points": [str(p) for p in item[1:]]}]
                        # Calculate bounding box from points
                        all_x = []
                        all_y = []
                        for p in item[1:]:
                            if hasattr(p, 'x'):
                                all_x.append(p.x)
                                all_y.append(p.y)
                        if all_x and all_y:
                            path_element = PathElement(
                                items=path_items,
                                bbox=BoundingBox(min(all_x), min(all_y), max(all_x), max(all_y)),
                                fill_color=fill_color,
                                stroke_color=stroke_color,
                            )
                            page_elements.paths.append(path_element)

        except Exception:
            pass

    def get_summary(self, doc_elements: DocumentElements) -> dict:
        """Get extraction summary."""
        return {
            "file_path": doc_elements.file_path,
            "page_count": doc_elements.page_count,
            "total_elements": doc_elements.total_elements,
            "total_text_blocks": doc_elements.total_text_blocks,
            "total_images": doc_elements.total_images,
            "total_lines": sum(len(p.lines) for p in doc_elements.pages),
            "total_rects": sum(len(p.rects) for p in doc_elements.pages),
            "total_paths": sum(len(p.paths) for p in doc_elements.pages),
            "pages": [
                {
                    "page": p.page_number,
                    "text_blocks": len(p.text_blocks),
                    "images": len(p.images),
                    "lines": len(p.lines),
                    "rects": len(p.rects),
                    "paths": len(p.paths),
                    "total": p.element_count,
                }
                for p in doc_elements.pages
            ],
        }
