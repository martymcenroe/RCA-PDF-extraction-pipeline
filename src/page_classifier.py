"""Page classification module for determining page content types."""

from .models import PageClassification, PageInfo, PageType, PDFStructure


class PageClassifier:
    """Classifies pages based on structural heuristics."""

    # Thresholds for classification
    MIN_LINES_FOR_TABLE = 5
    MIN_GRID_LINES = 3
    TEXT_SPARSE_THRESHOLD = 100  # chars
    IMAGE_COVERAGE_THRESHOLD = 0.5  # 50% of page
    BLANK_THRESHOLD = 10  # chars

    def classify_structure(self, structure: PDFStructure) -> dict[int, PageClassification]:
        """Classify all pages in a PDF structure."""
        classifications = {}
        for page_info in structure.pages:
            classifications[page_info.page_number] = self.classify_page(page_info)
        return classifications

    def classify_page(self, page_info: PageInfo) -> PageClassification:
        """Classify a single page based on its structure."""
        h_lines = len(page_info.horizontal_lines)
        v_lines = len(page_info.vertical_lines)
        text_blocks = len(page_info.text_blocks)
        char_count = page_info.char_count

        # Calculate image coverage
        page_area = page_info.width * page_info.height
        image_area = sum(img.area for img in page_info.images)
        image_coverage = image_area / page_area if page_area > 0 else 0

        # Classification logic
        page_type, confidence, notes = self._determine_type(
            h_lines, v_lines, text_blocks, char_count, image_coverage, page_info
        )

        return PageClassification(
            page_number=page_info.page_number,
            page_type=page_type,
            confidence=confidence,
            horizontal_line_count=h_lines,
            vertical_line_count=v_lines,
            text_block_count=text_blocks,
            image_coverage=round(image_coverage, 3),
            notes=notes,
        )

    def _determine_type(
        self,
        h_lines: int,
        v_lines: int,
        text_blocks: int,
        char_count: int,
        image_coverage: float,
        page_info: PageInfo,
    ) -> tuple[PageType, float, str]:
        """Determine page type using heuristics."""

        # Blank page
        if char_count < self.BLANK_THRESHOLD and image_coverage < 0.1:
            return PageType.BLANK, 0.95, "Minimal content detected"

        # Cover page heuristics (first page, limited text, possibly logo image)
        if page_info.page_number == 1:
            if char_count < 500 and image_coverage > 0.1:
                return PageType.COVER, 0.7, "First page with image, likely cover"
            if text_blocks < 5 and char_count < 300:
                return PageType.COVER, 0.6, "First page with sparse text, likely cover"

        # Figure/image-dominated page
        if image_coverage > self.IMAGE_COVERAGE_THRESHOLD:
            return PageType.FIGURE, 0.85, f"Image coverage {image_coverage:.1%}"

        # Table detection heuristics
        has_grid = h_lines >= self.MIN_GRID_LINES and v_lines >= self.MIN_GRID_LINES
        has_many_lines = (h_lines + v_lines) >= self.MIN_LINES_FOR_TABLE
        has_structured_text = text_blocks >= 3

        if has_grid:
            return PageType.TABLE, 0.9, f"Grid structure: {h_lines}H x {v_lines}V lines"

        if has_many_lines and has_structured_text:
            # Check for line regularity suggesting table structure
            if self._check_line_regularity(page_info):
                return PageType.TABLE, 0.75, f"Regular line pattern with {text_blocks} text blocks"
            return PageType.MIXED, 0.6, "Lines present but irregular pattern"

        # Narrative text (lots of text, few lines)
        if char_count > 500 and (h_lines + v_lines) < 5:
            return PageType.NARRATIVE, 0.8, "Dense text, few structural lines"

        # Mixed or unknown
        if has_structured_text:
            return PageType.MIXED, 0.5, "Structured text without clear table markers"

        return PageType.UNKNOWN, 0.3, "Unable to determine page type"

    def _check_line_regularity(self, page_info: PageInfo) -> bool:
        """Check if lines show regular spacing suggesting table structure."""
        h_lines = page_info.horizontal_lines
        if len(h_lines) < 3:
            return False

        # Sort horizontal lines by y position
        y_positions = sorted([line.y0 for line in h_lines])

        # Calculate gaps between consecutive lines
        gaps = [y_positions[i + 1] - y_positions[i] for i in range(len(y_positions) - 1)]

        if not gaps:
            return False

        # Check for regularity (similar gap sizes)
        avg_gap = sum(gaps) / len(gaps)
        if avg_gap < 5:  # Lines too close together
            return False

        # Count how many gaps are within 50% of the average
        regular_gaps = sum(1 for g in gaps if 0.5 * avg_gap <= g <= 1.5 * avg_gap)
        regularity_ratio = regular_gaps / len(gaps)

        return regularity_ratio > 0.6

    def get_table_pages(self, classifications: dict[int, PageClassification]) -> list[int]:
        """Get list of page numbers classified as tables."""
        return [
            page_num
            for page_num, classification in classifications.items()
            if classification.page_type == PageType.TABLE
        ]

    def get_summary(self, classifications: dict[int, PageClassification]) -> dict:
        """Get classification summary."""
        by_type = {}
        for classification in classifications.values():
            type_name = classification.page_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(classification.page_number)

        return {
            "total_pages": len(classifications),
            "by_type": by_type,
            "table_pages": self.get_table_pages(classifications),
            "details": {
                page_num: {
                    "type": c.page_type.value,
                    "confidence": c.confidence,
                    "h_lines": c.horizontal_line_count,
                    "v_lines": c.vertical_line_count,
                    "text_blocks": c.text_block_count,
                    "image_coverage": c.image_coverage,
                    "notes": c.notes,
                }
                for page_num, c in sorted(classifications.items())
            },
        }
