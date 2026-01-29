"""Core PDF analysis module using PyMuPDF for safe structure extraction."""

import os
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from .models import (
    ImageInfo,
    LineInfo,
    PageInfo,
    PDFMetadata,
    PDFStructure,
    TextBlock,
)


class PDFDissector:
    """Safe PDF analysis without rendering content."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        self._doc: Optional[fitz.Document] = None

    def __enter__(self):
        self._doc = fitz.open(self.file_path)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._doc:
            self._doc.close()

    def analyze(self) -> PDFStructure:
        """Perform full PDF structure analysis."""
        if not self._doc:
            raise RuntimeError("PDFDissector must be used as context manager")

        structure = PDFStructure(
            file_path=str(self.file_path),
            page_count=len(self._doc),
            file_size_bytes=os.path.getsize(self.file_path),
        )

        # Extract metadata
        structure.metadata = self._extract_metadata()
        structure.pdf_version = self._get_pdf_version()
        structure.is_encrypted = self._doc.is_encrypted
        structure.fonts = self._extract_fonts()

        # Check for forms
        try:
            structure.has_forms = self._doc.is_form_pdf
        except Exception:
            structure.has_forms = False

        # Analyze each page
        for page_num in range(len(self._doc)):
            try:
                page_info = self._analyze_page(page_num)
                structure.pages.append(page_info)
            except Exception as e:
                structure.anomalies.append(f"Page {page_num + 1}: {str(e)}")
                # Create minimal page info for failed page
                structure.pages.append(PageInfo(
                    page_number=page_num + 1,
                    width=0,
                    height=0,
                ))

        return structure

    def _extract_metadata(self) -> PDFMetadata:
        """Extract PDF metadata."""
        meta = self._doc.metadata or {}
        return PDFMetadata(
            title=meta.get("title"),
            author=meta.get("author"),
            subject=meta.get("subject"),
            creator=meta.get("creator"),
            producer=meta.get("producer"),
            creation_date=meta.get("creationDate"),
            modification_date=meta.get("modDate"),
            keywords=meta.get("keywords"),
        )

    def _get_pdf_version(self) -> Optional[str]:
        """Get PDF version string."""
        try:
            # Read first bytes to get PDF version
            with open(self.file_path, "rb") as f:
                header = f.read(20).decode("latin-1")
                if header.startswith("%PDF-"):
                    return header[5:8]
        except Exception:
            pass
        return None

    def _extract_fonts(self) -> list[str]:
        """Extract list of fonts used in the document."""
        fonts = set()
        for page_num in range(len(self._doc)):
            try:
                page = self._doc[page_num]
                font_list = page.get_fonts()
                for font in font_list:
                    # font[3] is the font name
                    if font[3]:
                        fonts.add(font[3])
            except Exception:
                continue
        return sorted(fonts)

    def _analyze_page(self, page_num: int) -> PageInfo:
        """Analyze a single page."""
        page = self._doc[page_num]
        rect = page.rect

        page_info = PageInfo(
            page_number=page_num + 1,
            width=rect.width,
            height=rect.height,
        )

        # Extract text blocks
        try:
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            for block in text_dict.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    bbox = block.get("bbox", (0, 0, 0, 0))
                    text = ""
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text += span.get("text", "")
                        text += "\n"
                    page_info.text_blocks.append(TextBlock(
                        x0=bbox[0],
                        y0=bbox[1],
                        x1=bbox[2],
                        y1=bbox[3],
                        text=text.strip(),
                    ))
        except Exception:
            pass

        # Extract full text content
        try:
            page_info.text_content = page.get_text()
            page_info.char_count = len(page_info.text_content)
            page_info.word_count = len(page_info.text_content.split())
        except Exception:
            pass

        # Extract drawings/lines
        try:
            drawings = page.get_drawings()
            for drawing in drawings:
                for item in drawing.get("items", []):
                    if item[0] == "l":  # Line
                        page_info.lines.append(LineInfo(
                            x0=item[1].x,
                            y0=item[1].y,
                            x1=item[2].x,
                            y1=item[2].y,
                        ))
                    elif item[0] == "re":  # Rectangle
                        rect = item[1]
                        # Add rectangle as 4 lines
                        page_info.lines.extend([
                            LineInfo(rect.x0, rect.y0, rect.x1, rect.y0),  # Top
                            LineInfo(rect.x0, rect.y1, rect.x1, rect.y1),  # Bottom
                            LineInfo(rect.x0, rect.y0, rect.x0, rect.y1),  # Left
                            LineInfo(rect.x1, rect.y0, rect.x1, rect.y1),  # Right
                        ])
        except Exception:
            pass

        # Extract images
        try:
            image_list = page.get_images()
            for img in image_list:
                try:
                    xref = img[0]
                    img_rect = page.get_image_bbox(xref)
                    page_info.images.append(ImageInfo(
                        x0=img_rect.x0,
                        y0=img_rect.y0,
                        x1=img_rect.x1,
                        y1=img_rect.y1,
                        width=img[2],
                        height=img[3],
                    ))
                except Exception:
                    continue
        except Exception:
            pass

        return page_info

    def get_summary(self) -> dict:
        """Get a summary dict of the PDF structure."""
        structure = self.analyze()
        return {
            "file_path": structure.file_path,
            "file_size_bytes": structure.file_size_bytes,
            "file_size_mb": round(structure.file_size_bytes / (1024 * 1024), 2),
            "page_count": structure.page_count,
            "pdf_version": structure.pdf_version,
            "is_encrypted": structure.is_encrypted,
            "has_forms": structure.has_forms,
            "metadata": {
                "title": structure.metadata.title,
                "author": structure.metadata.author,
                "creator": structure.metadata.creator,
                "producer": structure.metadata.producer,
                "creation_date": structure.metadata.creation_date,
            },
            "fonts": structure.fonts,
            "anomalies": structure.anomalies,
            "pages": [
                {
                    "page": p.page_number,
                    "width": round(p.width, 1),
                    "height": round(p.height, 1),
                    "text_blocks": len(p.text_blocks),
                    "lines": p.line_count,
                    "horizontal_lines": len(p.horizontal_lines),
                    "vertical_lines": len(p.vertical_lines),
                    "images": p.image_count,
                    "char_count": p.char_count,
                    "word_count": p.word_count,
                }
                for p in structure.pages
            ],
        }
