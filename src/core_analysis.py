"""Core Analysis extraction pipeline for RCA documents.

This module extracts Routine Core Analysis data from the parsed PDF database,
classifies pages, and consolidates table data into CSV/JSON output.
"""

import csv
import json
import logging
import os
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .output.csv_sanitizer import sanitize_csv_value

# Configure logging for audit trail
logger = logging.getLogger(__name__)

# Compiled regex for fracture indicator extraction (Tier 3 optimization)
FRACTURE_INDICATOR_RE = re.compile(r'\((f|F)\)$')

# Safety limits to prevent resource exhaustion on malformed input
MAX_SAMPLE_LINES = 20  # Maximum lines per sample before aborting parse

# Column groups for merged cell expansion
COLUMN_GROUPS = {
    'permeability': ['permeability_air_md', 'permeability_klink_md'],
    'saturation': ['saturation_water_pct', 'saturation_oil_pct', 'saturation_total_pct'],
}

# Expected column counts for fail-safe validation
EXPECTED_COLUMN_COUNTS = {
    'permeability': 2,
    'saturation': 3,
}

# Merged cell indicators that should be replicated across column groups
MERGED_INDICATORS = ['+', '**', '<0.0001', '<']

# Allowed output directories for security
ALLOWED_OUTPUT_ROOTS = [
    '/c/Users/mcwiz/Projects/RCA-PDF-extraction-pipeline',
    '/tmp/',
    'C:\\Users\\mcwiz\\Projects\\RCA-PDF-extraction-pipeline',
    'C:\\Users\\mcwiz\\AppData\\Local\\Temp',  # Windows temp
    '/c/Users/mcwiz/AppData/Local/Temp',  # Unix-style Windows temp
]


@dataclass
class CoreSample:
    """A single core sample measurement."""
    core_number: str
    sample_number: str
    depth_feet: Optional[float]
    permeability_air_md: Optional[float | str]  # Can be float or merged indicator
    permeability_klink_md: Optional[float | str]  # Can be float or merged indicator
    porosity_ambient_pct: Optional[float]
    porosity_ncs_pct: Optional[float]
    grain_density_gcc: Optional[float]
    saturation_water_pct: Optional[float | str]  # Can be float or "**"
    saturation_oil_pct: Optional[float | str]  # Can be float or "**"
    saturation_total_pct: Optional[float | str]  # Can be float or "**"
    page_number: int = 0

    def to_dict(self) -> dict:
        return {
            "core_number": self.core_number,
            "sample_number": self.sample_number,
            "depth_feet": self.depth_feet,
            "permeability_air_md": self.permeability_air_md,
            "permeability_klink_md": self.permeability_klink_md,
            "porosity_ambient_pct": self.porosity_ambient_pct,
            "porosity_ncs_pct": self.porosity_ncs_pct,
            "grain_density_gcc": self.grain_density_gcc,
            "saturation_water_pct": self.saturation_water_pct,
            "saturation_oil_pct": self.saturation_oil_pct,
            "saturation_total_pct": self.saturation_total_pct,
            "page_number": self.page_number,
        }


@dataclass
class PageClassification:
    """Classification result for a page."""
    page_number: int
    page_type: str  # 'table', 'cover', 'plot', 'text', 'other'
    confidence: float
    reason: str


@dataclass
class ExtractionResult:
    """Result of the extraction pipeline."""
    classifications: list[PageClassification] = field(default_factory=list)
    samples: list[CoreSample] = field(default_factory=list)
    table_pages: list[int] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class CoreAnalysisExtractor:
    """Extract Core Analysis data from parsed PDF database."""

    # Canonical headers (for internal use and backwards compatibility)
    CANONICAL_HEADERS = [
        "core_number", "sample_number", "depth_feet",
        "permeability_air_md", "permeability_klink_md",
        "porosity_ambient_pct", "porosity_ncs_pct",
        "grain_density_gcc",
        "saturation_water_pct", "saturation_oil_pct", "saturation_total_pct",
        "page_number"
    ]

    # Original PDF headers (matching the actual table headers in the PDF)
    ORIGINAL_HEADERS = [
        "Core Number", "Sample Number", "Depth (ft)",
        "Permeability (md) | Air", "Permeability (md) | Klink",
        "Porosity (%) | Ambient", "Porosity (%) | NCS",
        "Grain Density (g/cc)",
        "Fluid Saturations (%) | Water", "Fluid Saturations (%) | Oil",
        "Fluid Saturations (%) | Total",
        "Page Number"
    ]

    # Keywords for classification
    TABLE_KEYWORDS = [
        "SUMMARY OF ROUTINE CORE ANALYSES",
        "ROUTINE CORE ANALYSIS",
        "Core Number",
        "Sample Number",
        "Permeability",
        "Porosity",
    ]

    PLOT_KEYWORDS = [
        "PROFILE PLOT",
        "VERSUS POROSITY",
        "CROSS PLOT",
    ]

    COVER_KEYWORDS = [
        "CORE ANALYSIS REPORT",
        "TABLE OF CONTENTS",
    ]

    # Y-range for header rows on first table page
    HEADER_Y_MIN = 170
    HEADER_Y_MAX = 230

    # Column boundaries for the RCA table (x-coordinate ranges)
    # Each tuple is (x_min, x_max) defining a column's horizontal extent
    COLUMN_BOUNDARIES = [
        (40, 85),    # 0: Core Number
        (85, 135),   # 1: Sample Number
        (135, 200),  # 2: Depth
        (200, 260),  # 3: Permeability Air
        (260, 325),  # 4: Permeability Klinkenberg
        (325, 375),  # 5: Porosity Ambient
        (375, 410),  # 6: Porosity NCS
        (410, 450),  # 7: Grain Density
        (450, 490),  # 8: Saturations Water
        (490, 530),  # 9: Saturations Oil
        (530, 570),  # 10: Saturations Total
    ]

    # Parent headers that span multiple columns
    # Maps (y_approx, x_center_approx) to list of column indices
    SPANNING_HEADERS = {
        # "Permeability," and "millidarcys" span columns 3-4
        (193, 259): [3, 4],
        (204, 259): [3, 4],
        # "Porosity," and "percent" span columns 5-6
        (193, 367): [5, 6],
        (204, 367): [5, 6],
        # "Fluid", "Saturations,", "percent" span columns 8-10
        (181, 506): [8, 9, 10],
        (193, 506): [8, 9, 10],
        (204, 506): [8, 9, 10],
    }

    # Headers to exclude (misaligned or not actual column headers)
    EXCLUDED_HEADERS = []  # None currently - "Sample" at y=193 IS part of Depth header

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        self._extracted_headers: list[str] | None = None

    def _extract_headers_from_db(self, conn: sqlite3.Connection, page_num: int = 39) -> list[str]:
        """
        Extract and flatten multi-row table headers from the database.

        The PDF has a 4-row header structure where parent categories span
        multiple columns. This method:
        1. Assigns text spans to columns based on predefined boundaries
        2. Handles spanning headers that apply to multiple columns
        3. Excludes misaligned headers

        Args:
            conn: Database connection.
            page_num: Page number containing the table headers (default: 39).

        Returns:
            List of flattened header strings in column order.
        """
        cursor = conn.cursor()

        # Query text spans in the header region
        cursor.execute("""
            SELECT ts.x0, ts.x1, ts.y0, ts.text
            FROM text_spans ts
            JOIN pages p ON ts.page_id = p.id
            WHERE p.page_number = ? AND ts.y0 >= ? AND ts.y0 <= ?
            ORDER BY ts.y0, ts.x0
        """, (page_num, self.HEADER_Y_MIN, self.HEADER_Y_MAX))

        spans = [(row["x0"], row["x1"], row["y0"], row["text"].strip())
                 for row in cursor.fetchall()]

        if not spans:
            logger.warning(f"No header spans found on page {page_num}, using fallback headers")
            return self.ORIGINAL_HEADERS[:-1]  # Exclude "Page Number"

        # Initialize columns with empty text lists
        columns = [[] for _ in self.COLUMN_BOUNDARIES]

        # Helper to find spanning header match
        def find_spanning_match(y: float, center: float) -> list[int] | None:
            for (y_approx, x_approx), col_indices in self.SPANNING_HEADERS.items():
                if abs(y - y_approx) < 5 and abs(center - x_approx) < 20:
                    return col_indices
            return None

        # Helper to check if header should be excluded
        def is_excluded(y: float, center: float) -> bool:
            for (y_approx, x_approx) in self.EXCLUDED_HEADERS:
                if abs(y - y_approx) < 5 and abs(center - x_approx) < 20:
                    return True
            return False

        # Assign each span to column(s)
        for x0, x1, y, text in spans:
            center = (x0 + x1) / 2

            # Check if excluded
            if is_excluded(y, center):
                continue

            # Check if this is a spanning header
            span_cols = find_spanning_match(y, center)
            if span_cols:
                # Add to all spanned columns
                for col_idx in span_cols:
                    columns[col_idx].append((y, text))
            else:
                # Assign to single column based on center
                for i, (col_min, col_max) in enumerate(self.COLUMN_BOUNDARIES):
                    if col_min <= center <= col_max:
                        columns[i].append((y, text))
                        break

        # Build header strings by joining text from top to bottom
        headers = []
        for col_texts in columns:
            if col_texts:
                # Sort by y-position (top to bottom)
                col_texts.sort(key=lambda t: t[0])
                header_text = " ".join(text for _, text in col_texts)
                # Clean up: remove trailing commas, normalize spaces
                header_text = " ".join(header_text.split()).rstrip(",")
                headers.append(header_text)
            else:
                headers.append("")

        logger.debug(f"Extracted {len(headers)} headers from page {page_num}")
        return headers

    def get_extracted_headers(self) -> list[str]:
        """
        Get headers extracted from the PDF, plus 'Page Number'.

        Returns cached headers or extracts them from the database.
        """
        if self._extracted_headers is None:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                pdf_headers = self._extract_headers_from_db(conn)
                # Append "Page Number" which is not in the PDF
                self._extracted_headers = pdf_headers + ["Page Number"]
        return self._extracted_headers

    def verify_headers_across_pages(
        self, table_pages: list[int] | None = None
    ) -> dict:
        """
        Verify headers are consistent across all table pages.

        Extracts headers from each table page and compares them to ensure
        consistency. This addresses the assignment requirement to "handle
        any potential header variations across pages."

        Args:
            table_pages: List of table page numbers to check. If None, will
                        run extraction to discover table pages.

        Returns:
            dict with keys:
            - 'verified': bool - True if all pages match
            - 'reference_page': int - Page used as reference (first table page)
            - 'reference_headers': list[str] - Headers from reference page
            - 'pages_checked': list[int] - All pages that were checked
            - 'mismatches': list[dict] - Details of any mismatches found
                Each mismatch has: page, differences (list of diffs)
        """
        if table_pages is None:
            # Run extraction to get table pages
            result = self.extract()
            table_pages = result.table_pages

        if not table_pages:
            return {
                'verified': False,
                'reference_page': None,
                'reference_headers': [],
                'pages_checked': [],
                'mismatches': [],
            }

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Extract headers from each table page
            headers_by_page: dict[int, list[str]] = {}
            for page_num in table_pages:
                headers_by_page[page_num] = self._extract_headers_from_db(
                    conn, page_num
                )

        # Use first table page as reference
        reference_page = table_pages[0]
        reference_headers = headers_by_page[reference_page]

        # Compare all pages to reference
        mismatches = []
        for page_num in table_pages[1:]:
            page_headers = headers_by_page[page_num]
            differences = []

            # Check header count
            if len(page_headers) != len(reference_headers):
                differences.append(
                    f"Column count differs: {len(page_headers)} vs "
                    f"{len(reference_headers)} (reference)"
                )

            # Check each header
            for i, (ref_h, page_h) in enumerate(
                zip(reference_headers, page_headers)
            ):
                if ref_h != page_h:
                    differences.append(
                        f"Column {i}: '{page_h}' vs '{ref_h}' (reference)"
                    )

            if differences:
                mismatches.append({
                    'page': page_num,
                    'differences': differences,
                })
                logger.warning(
                    f"Header mismatch on page {page_num}: {differences}"
                )

        verified = len(mismatches) == 0

        if verified:
            logger.info(
                f"Headers verified: all {len(table_pages)} pages match"
            )
        else:
            logger.warning(
                f"Header verification failed: {len(mismatches)} pages "
                "have different headers"
            )

        return {
            'verified': verified,
            'reference_page': reference_page,
            'reference_headers': reference_headers,
            'pages_checked': table_pages,
            'mismatches': mismatches,
        }

    def extract(self) -> ExtractionResult:
        """Run the full extraction pipeline."""
        result = ExtractionResult()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Step 1: Classify all pages
            result.classifications = self._classify_pages(conn)
            result.table_pages = [
                c.page_number for c in result.classifications
                if c.page_type == "table"
            ]

            # Step 2: Extract data from table pages
            for page_num in result.table_pages:
                try:
                    samples = self._extract_page_data(conn, page_num)
                    result.samples.extend(samples)
                except Exception as e:
                    result.warnings.append(f"Page {page_num}: {str(e)}")

        return result

    def _classify_pages(self, conn: sqlite3.Connection) -> list[PageClassification]:
        """Classify all pages in the document."""
        cursor = conn.cursor()

        # Get all pages
        cursor.execute("SELECT page_number FROM pages ORDER BY page_number")
        pages = [row["page_number"] for row in cursor.fetchall()]

        classifications = []
        for page_num in pages:
            classification = self._classify_page(conn, page_num)
            classifications.append(classification)

        return classifications

    def _classify_page(self, conn: sqlite3.Connection, page_num: int) -> PageClassification:
        """Classify a single page based on its content."""
        cursor = conn.cursor()

        # Get all text from the page
        cursor.execute("""
            SELECT GROUP_CONCAT(text, ' ') as all_text
            FROM text_spans ts
            JOIN pages p ON ts.page_id = p.id
            WHERE p.page_number = ?
        """, (page_num,))

        row = cursor.fetchone()
        text = row["all_text"] or "" if row else ""
        text_upper = text.upper()

        # Check for summary table (highest priority)
        if "SUMMARY OF ROUTINE CORE ANALYSES" in text_upper:
            return PageClassification(
                page_number=page_num,
                page_type="table",
                confidence=0.95,
                reason="Contains 'SUMMARY OF ROUTINE CORE ANALYSES'"
            )

        # Check for plots
        for keyword in self.PLOT_KEYWORDS:
            if keyword in text_upper:
                return PageClassification(
                    page_number=page_num,
                    page_type="plot",
                    confidence=0.85,
                    reason=f"Contains plot keyword: {keyword}"
                )

        # Check for cover/TOC pages
        for keyword in self.COVER_KEYWORDS:
            if keyword in text_upper:
                return PageClassification(
                    page_number=page_num,
                    page_type="cover",
                    confidence=0.80,
                    reason=f"Contains cover keyword: {keyword}"
                )

        # Check for other table indicators
        table_score = sum(1 for kw in self.TABLE_KEYWORDS if kw.upper() in text_upper)
        if table_score >= 3:
            return PageClassification(
                page_number=page_num,
                page_type="table",
                confidence=0.70,
                reason=f"Contains {table_score} table keywords"
            )

        # Check if page has minimal text (likely scanned image or blank)
        if len(text) < 50:
            return PageClassification(
                page_number=page_num,
                page_type="other",
                confidence=0.60,
                reason="Minimal extractable text"
            )

        # Check for narrative text (dense text without table markers)
        if len(text) > 500 and table_score == 0:
            return PageClassification(
                page_number=page_num,
                page_type="text",
                confidence=0.65,
                reason="Dense text without table markers"
            )

        return PageClassification(
            page_number=page_num,
            page_type="other",
            confidence=0.50,
            reason="Unable to classify"
        )

    def _extract_page_data(self, conn: sqlite3.Connection, page_num: int) -> list[CoreSample]:
        """Extract core sample data from a table page."""
        cursor = conn.cursor()

        # Get text blocks ordered by position
        cursor.execute("""
            SELECT full_text, x0, y0, x1, y1
            FROM text_blocks tb
            JOIN pages p ON tb.page_id = p.id
            WHERE p.page_number = ?
            ORDER BY y0, x0
        """, (page_num,))

        blocks = cursor.fetchall()

        # Find the data block (largest block with numeric data)
        data_block = None
        for block in blocks:
            text = block["full_text"]
            # Look for block with depth values (e.g., "9,580.50" or "9580.50")
            if re.search(r'\d{1,2},?\d{3}\.\d{2}', text):
                if data_block is None or len(text) > len(data_block["full_text"]):
                    data_block = block

        if not data_block:
            return []

        return self._parse_data_block(data_block["full_text"], page_num)

    def _parse_data_block(self, text: str, page_num: int) -> list[CoreSample]:
        """Parse the data block into CoreSample objects."""
        samples = []

        # Split into lines and filter empty
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Find sample boundaries by looking for core number followed by sample number
        sample_starts = []
        for i in range(len(lines) - 2):
            # Core number is single digit
            if re.match(r'^\d{1,2}$', lines[i]):
                # Sample number follows (e.g., "1-1", "1-2(F)", "1-10(f)")
                if re.match(r'^\d+-\d+', lines[i + 1]):
                    # Depth follows (e.g., "9,580.50")
                    if re.match(r'^\d{1,2},?\d{3}\.\d{2}$', lines[i + 2]):
                        sample_starts.append(i)

        # Parse each sample
        for idx, start in enumerate(sample_starts):
            # Determine end of this sample (start of next, or end of data)
            if idx + 1 < len(sample_starts):
                end = sample_starts[idx + 1]
            else:
                end = len(lines)

            sample_lines = lines[start:end]
            sample = self._parse_sample_lines(sample_lines, page_num)
            if sample:
                samples.append(sample)

        return samples

    def _parse_sample_lines(self, lines: list[str], page_num: int) -> Optional[CoreSample]:
        """Parse a sample's lines into a CoreSample object.

        Issue #4 changes:
        1. Replicate merged indicators (+, <0.0001) to both permeability columns
        2. Replicate ** to all three saturation columns
        3. Fix + handling: means "below detection", not "fracture"
        """
        try:
            # SAFETY: Prevent unbounded loop on malformed input
            if len(lines) > MAX_SAMPLE_LINES:
                logger.warning(f"Page {page_num}: Sample exceeds {MAX_SAMPLE_LINES} lines, skipping")
                return None

            if len(lines) < 5:
                return None

            core_num = lines[0]
            sample_num = lines[1]
            depth = self._parse_depth(lines[2])

            if depth is None:
                return None

            # Remaining values after core, sample, depth
            values = lines[3:]

            perm_air = None
            perm_klink = None
            porosity_amb = None
            porosity_ncs = None
            grain_density = None
            sat_water = None
            sat_oil = None
            sat_total = None

            idx = 0

            # Permeability to Air (can be number, "<X", or "+")
            if idx < len(values):
                val = values[idx]
                if val == '+':
                    # ISSUE #4 FIX: + means "below detection", replicate to BOTH columns
                    perm_air = '+'
                    perm_klink = '+'
                    logger.debug(f"Expanded '+' to both permeability columns")
                    idx += 1
                    # For + values, skip to porosity (single value for these samples)
                    if idx < len(values):
                        porosity_amb = self._parse_float(values[idx])
                        idx += 1
                    # Grain density
                    if idx < len(values):
                        grain_density = self._parse_float(values[idx])
                        idx += 1
                elif val.startswith('<'):
                    # ISSUE #4 FIX: Replicate to BOTH permeability columns
                    perm_air = val
                    perm_klink = val  # Replicate to klink
                    logger.debug(f"Expanded '{val}' to both permeability columns")
                    idx += 1
                    # For <X values, skip klinkenberg (it's merged), go to porosity
                    if idx < len(values):
                        porosity_amb = self._parse_float(values[idx])
                        idx += 1
                    if idx < len(values):
                        porosity_ncs = self._parse_float(values[idx])
                        idx += 1
                    if idx < len(values):
                        grain_density = self._parse_float(values[idx])
                        idx += 1
                else:
                    # Normal numeric permeability
                    perm_air = self._parse_float(val)
                    idx += 1

                    # Klinkenberg permeability
                    if idx < len(values):
                        perm_klink = self._parse_float(values[idx])
                        idx += 1

                    # Porosity Ambient
                    if idx < len(values):
                        porosity_amb = self._parse_float(values[idx])
                        idx += 1

                    # Porosity NCS
                    if idx < len(values):
                        porosity_ncs = self._parse_float(values[idx])
                        idx += 1

                    # Grain Density
                    if idx < len(values):
                        grain_density = self._parse_float(values[idx])
                        idx += 1

            # Fluid Saturations (remaining values, or ** for none)
            if idx < len(values):
                val = values[idx]
                if val == '**':
                    # ISSUE #4 FIX: Replicate ** to ALL THREE saturation columns
                    sat_water = '**'
                    sat_oil = '**'
                    sat_total = '**'
                    logger.debug("Expanded '**' to all saturation columns")
                else:
                    sat_water = self._parse_float(val)
                    idx += 1

                    if idx < len(values):
                        sat_oil = self._parse_float(values[idx])
                        idx += 1

                    if idx < len(values):
                        sat_total = self._parse_float(values[idx])

            return CoreSample(
                core_number=core_num,
                sample_number=sample_num,
                depth_feet=depth,
                permeability_air_md=perm_air,
                permeability_klink_md=perm_klink,
                porosity_ambient_pct=porosity_amb,
                porosity_ncs_pct=porosity_ncs,
                grain_density_gcc=grain_density,
                saturation_water_pct=sat_water,
                saturation_oil_pct=sat_oil,
                saturation_total_pct=sat_total,
                page_number=page_num,
            )

        except Exception:
            return None

    def _parse_depth(self, value: str) -> Optional[float]:
        """Parse a depth value like '9,580.50'."""
        try:
            # Remove commas and parse
            cleaned = value.replace(',', '')
            return float(cleaned)
        except ValueError:
            return None

    def _parse_float(self, value: str) -> Optional[float]:
        """Parse a float value, handling special cases."""
        try:
            if not value or value in ('**', '+', '-'):
                return None
            cleaned = value.replace(',', '')
            return float(cleaned)
        except ValueError:
            return None

    def _extract_fracture_indicator(self, sample_number: str) -> Optional[str]:
        """Extract case-sensitive fracture indicator from sample number.

        Args:
            sample_number: Sample number like "1-9(f)" or "1-2(F)"

        Returns:
            "(f)" or "(F)" if present, None otherwise.
        """
        # Strip whitespace to handle PDF extraction artifacts
        sample_clean = sample_number.strip()
        match = FRACTURE_INDICATOR_RE.search(sample_clean)
        if match:
            indicator = f"({match.group(1)})"
            logger.debug(f"Extracted fracture indicator: {indicator} from {sample_number}")
            return indicator
        return None

    def _validate_output_path(self, output_path: str) -> bool:
        """Ensure output path is within allowed directories.

        Args:
            output_path: Path to validate

        Returns:
            True if valid

        Raises:
            ValueError: If path is outside allowed directories
        """
        abs_path = os.path.abspath(output_path)
        for allowed_root in ALLOWED_OUTPUT_ROOTS:
            allowed_abs = os.path.abspath(allowed_root)
            if abs_path.startswith(allowed_abs):
                return True
        raise ValueError(f"Output path '{output_path}' outside allowed directories")

    def get_classification_dict(self, result: ExtractionResult) -> dict[str, str]:
        """Get classification as a simple dictionary for the assignment."""
        return {
            f"page_{c.page_number}": c.page_type
            for c in result.classifications
        }

    def save_csv(
        self,
        result: ExtractionResult,
        output_path: str,
        use_original_headers: bool = False,
    ) -> str:
        """Save extracted samples to CSV.

        Args:
            result: Extraction result containing samples.
            output_path: Path to save CSV file.
            use_original_headers: If True, use original PDF headers (e.g., "Depth (ft)")
                                  instead of canonical headers (e.g., "depth_feet").
                                  Original headers are sanitized for CSV injection protection.

        Returns:
            Path to saved file.

        Raises:
            ValueError: If output_path is outside allowed directories.
        """
        # ISSUE #4: Validate output path for security
        self._validate_output_path(str(output_path))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Choose header style
        if use_original_headers:
            # ISSUE #13: Use headers extracted from PDF, not hardcoded
            # Sanitize for CSV injection protection
            display_headers = [sanitize_csv_value(h) for h in self.get_extracted_headers()]
        else:
            display_headers = self.CANONICAL_HEADERS

        # Helper to format and sanitize cell values
        def format_value(val):
            if val is None:
                return ""
            # ISSUE #4: Sanitize string values that may contain CSV injection chars
            # This handles replicated merged indicators like +, **, <0.0001
            if isinstance(val, str):
                return sanitize_csv_value(val)
            return val

        # Write with UTF-8 BOM for Excel compatibility
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(display_headers)

            for sample in result.samples:
                # Get values in the same order as headers
                row = [
                    sample.core_number,
                    sample.sample_number,
                    sample.depth_feet if sample.depth_feet is not None else "",
                    format_value(sample.permeability_air_md),
                    format_value(sample.permeability_klink_md),
                    sample.porosity_ambient_pct if sample.porosity_ambient_pct is not None else "",
                    sample.porosity_ncs_pct if sample.porosity_ncs_pct is not None else "",
                    sample.grain_density_gcc if sample.grain_density_gcc is not None else "",
                    format_value(sample.saturation_water_pct),
                    format_value(sample.saturation_oil_pct),
                    format_value(sample.saturation_total_pct),
                    sample.page_number,
                ]
                writer.writerow(row)

        return str(output_path)

    def save_classification(self, result: ExtractionResult, output_path: str) -> str:
        """Save page classification to JSON (Part 1 of assignment).

        Outputs a flat dictionary: {"page_1": "other", "page_39": "table", ...}

        Raises:
            ValueError: If output_path is outside allowed directories.
        """
        # LLD-015: Validate output path for security
        self._validate_output_path(str(output_path))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Output flat classification dict only (not nested)
        data = self.get_classification_dict(result)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return str(output_path)

    def save_header_verification(
        self,
        output_path: str,
        table_pages: list[int] | None = None,
    ) -> str:
        """
        Verify headers across table pages and save results to a text file.

        This addresses the assignment requirement to "handle any potential
        header variations across pages" by verifying all table pages have
        consistent headers.

        Args:
            output_path: Path to save the verification report.
            table_pages: List of table page numbers. If None, will discover
                        them via extraction.

        Returns:
            Path to saved file.

        Raises:
            ValueError: If output_path is outside allowed directories.
        """
        self._validate_output_path(str(output_path))

        # Run header verification
        verification = self.verify_headers_across_pages(table_pages)

        # Format as human-readable report
        lines = [
            "Header Verification Report",
            "=" * 26,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        if verification['reference_page'] is not None:
            lines.append(f"Reference Page: {verification['reference_page']}")
            pages_str = ", ".join(str(p) for p in verification['pages_checked'])
            lines.append(f"Pages Checked: {pages_str}")
            lines.append("")

            if verification['verified']:
                lines.append(
                    "Status: VERIFIED - All headers match across pages"
                )
            else:
                lines.append(
                    f"Status: MISMATCH - {len(verification['mismatches'])} "
                    "page(s) have different headers"
                )
                lines.append("")
                lines.append("Mismatches:")
                for mismatch in verification['mismatches']:
                    lines.append(f"  Page {mismatch['page']}:")
                    for diff in mismatch['differences']:
                        lines.append(f"    - {diff}")

            lines.append("")
            lines.append(f"Headers ({len(verification['reference_headers'])} columns):")
            for i, header in enumerate(verification['reference_headers'], 1):
                lines.append(f"  {i}. {header}")
        else:
            lines.append("Status: NO TABLE PAGES FOUND")
            lines.append("")
            lines.append("No table pages were identified in the document.")

        # Write to file
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

        return str(output_path)

    def save_json(self, result: ExtractionResult, output_path: str) -> str:
        """Save extraction result to JSON (legacy bundled format).

        Note: For assignment deliverables, use save_classification() instead.

        Raises:
            ValueError: If output_path is outside allowed directories.
        """
        # ISSUE #4: Validate output path for security
        self._validate_output_path(str(output_path))

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "classification": self.get_classification_dict(result),
            "table_pages": result.table_pages,
            "sample_count": len(result.samples),
            "samples": [s.to_dict() for s in result.samples],
            "warnings": result.warnings,
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

        return str(output_path)

    def print_summary(self, result: ExtractionResult):
        """Print extraction summary."""
        print("\n" + "=" * 60)
        print("CORE ANALYSIS EXTRACTION RESULTS")
        print("=" * 60)

        # Classification summary
        type_counts = {}
        for c in result.classifications:
            type_counts[c.page_type] = type_counts.get(c.page_type, 0) + 1

        print(f"\nPage Classification:")
        for ptype, count in sorted(type_counts.items()):
            print(f"  {ptype}: {count} pages")

        print(f"\nTable pages: {result.table_pages}")
        print(f"Samples extracted: {len(result.samples)}")

        if result.samples:
            print(f"\nSample depth range: {min(s.depth_feet for s in result.samples if s.depth_feet):.2f} - {max(s.depth_feet for s in result.samples if s.depth_feet):.2f} feet")

        if result.warnings:
            print(f"\nWarnings ({len(result.warnings)}):")
            for w in result.warnings[:5]:
                print(f"  - {w}")
            if len(result.warnings) > 5:
                print(f"  ... and {len(result.warnings) - 5} more")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract Core Analysis data from parsed PDF database"
    )
    parser.add_argument("database", help="Path to the SQLite database from elementizer")
    parser.add_argument(
        "--output", "-o",
        default="data/output",
        help="Output directory for CSV and JSON files"
    )
    parser.add_argument(
        "--classify-only",
        action="store_true",
        help="Only run page classification, skip data extraction"
    )
    parser.add_argument(
        "--json-output", "-j",
        action="store_true",
        help="Output classification dict to stdout as JSON"
    )
    parser.add_argument(
        "--original-headers",
        action="store_true",
        help="Use original PDF headers instead of canonical names"
    )

    args = parser.parse_args()

    extractor = CoreAnalysisExtractor(args.database)
    result = extractor.extract()

    if args.json_output:
        print(json.dumps(extractor.get_classification_dict(result), indent=2))
        return

    extractor.print_summary(result)

    if not args.classify_only:
        # LLD-015: New output filenames matching assignment terminology
        csv_path = extractor.save_csv(
            result,
            f"{args.output}/full_table_extraction.csv",
            use_original_headers=args.original_headers,
        )
        classification_path = extractor.save_classification(
            result,
            f"{args.output}/page_classification.json"
        )
        # Issue #16: Header verification across table pages
        verification_path = extractor.save_header_verification(
            f"{args.output}/header_verification.txt",
            table_pages=result.table_pages,
        )

        print(f"\nOutput files:")
        print(f"  Page Classification (Part 1): {classification_path}")
        print(f"  Full Table Extraction (Part 2): {csv_path}")
        print(f"  Header Verification: {verification_path}")


if __name__ == "__main__":
    main()
