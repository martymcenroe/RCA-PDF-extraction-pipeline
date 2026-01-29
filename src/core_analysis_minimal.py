#!/usr/bin/env python3
"""
Minimal Core Analysis Extraction Pipeline

Single-pass PDF → CSV/JSON extraction without intermediate database.
This is the "small pipeline" version.

Usage:
    python src/core_analysis_minimal.py docs/context/init/W20552.pdf --output data/output/
    python src/core_analysis_minimal.py docs/context/init/W20552.pdf --json-output
"""

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF


@dataclass
class Sample:
    """Single core analysis sample record."""
    core_number: str = ""
    sample_number: str = ""
    depth_feet: str = ""
    permeability_air_md: str = ""
    permeability_klink_md: str = ""
    porosity_ambient_pct: str = ""
    porosity_ncs_pct: str = ""
    grain_density_gcc: str = ""
    saturation_water_pct: str = ""
    saturation_oil_pct: str = ""
    saturation_total_pct: str = ""
    page_number: int = 0
    notes: str = ""


@dataclass
class ExtractionResult:
    """Complete extraction result."""
    classifications: dict = field(default_factory=dict)
    samples: list = field(default_factory=list)
    table_pages: list = field(default_factory=list)
    timing_ms: float = 0.0

    @property
    def stats(self) -> dict:
        class_counts = {}
        for cls in self.classifications.values():
            class_counts[cls] = class_counts.get(cls, 0) + 1
        return {
            "total_pages": len(self.classifications),
            "table_pages": len(self.table_pages),
            "samples_extracted": len(self.samples),
            "classification_counts": class_counts,
            "timing_ms": self.timing_ms
        }


class CoreAnalysisMinimal:
    """Minimal single-pass Core Analysis extractor."""

    TABLE_KEYWORDS = [
        "SUMMARY OF ROUTINE CORE ANALYSES",
        "ROUTINE CORE ANALYSIS",
        "CORE ANALYSIS DATA",
    ]

    PLOT_KEYWORDS = [
        "PROFILE PLOT",
        "VERSUS POROSITY",
        "VS POROSITY",
        "POROSITY VS",
    ]

    COVER_KEYWORDS = [
        "TABLE OF CONTENTS",
        "CORE LABORATORIES",
    ]

    CSV_HEADERS = [
        "core_number", "sample_number", "depth_feet",
        "permeability_air_md", "permeability_klink_md",
        "porosity_ambient_pct", "porosity_ncs_pct",
        "grain_density_gcc", "saturation_water_pct",
        "saturation_oil_pct", "saturation_total_pct",
        "page_number", "notes"
    ]

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

    def extract(self) -> ExtractionResult:
        """Single-pass extraction: classify pages and extract data."""
        start_time = time.perf_counter()
        result = ExtractionResult()

        doc = fitz.open(self.pdf_path)
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                text_upper = text.upper()

                # Classify page
                classification = self._classify_page(text_upper, page)
                result.classifications[f"page_{page_num + 1}"] = classification

                # Extract data from table pages
                if classification == "table":
                    result.table_pages.append(page_num + 1)
                    samples = self._extract_samples(text, page_num + 1)
                    result.samples.extend(samples)
        finally:
            doc.close()

        result.timing_ms = (time.perf_counter() - start_time) * 1000
        return result

    def _classify_page(self, text_upper: str, page) -> str:
        """Classify a single page by content."""
        # Check for table keywords
        for keyword in self.TABLE_KEYWORDS:
            if keyword in text_upper:
                return "table"

        # Check for plot keywords
        for keyword in self.PLOT_KEYWORDS:
            if keyword in text_upper:
                return "plot"

        # Check for cover keywords
        for keyword in self.COVER_KEYWORDS:
            if keyword in text_upper:
                return "cover"

        # Check if page has substantial text
        word_count = len(text_upper.split())
        if word_count > 100:
            return "text"

        return "other"

    def _extract_samples(self, text: str, page_number: int) -> list:
        """Extract sample records from table page text.

        Note: PyMuPDF extracts text vertically - each value is on its own line.
        Sample format in extracted text:
            1           <- core number
            1-1         <- sample number
            9,580.50    <- depth
            0.0011      <- permeability air
            0.0003      <- permeability klink
            ...
        """
        samples = []
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Find sample boundaries: core number (1-2 digits) + sample number (X-Y) + depth
        sample_starts = []
        for i in range(len(lines) - 2):
            # Core number is 1-2 digits alone
            if re.match(r'^\d{1,2}$', lines[i]):
                # Sample number follows (e.g., "1-1", "1-2(F)")
                if re.match(r'^\d+-\d+', lines[i + 1]):
                    # Depth follows (e.g., "9,580.50")
                    if re.match(r'^\d{1,2},?\d{3}\.\d{2}$', lines[i + 2]):
                        sample_starts.append(i)

        # Parse each sample
        for idx, start in enumerate(sample_starts):
            end = sample_starts[idx + 1] if idx + 1 < len(sample_starts) else len(lines)
            sample_lines = lines[start:end]
            sample = self._parse_sample_lines(sample_lines, page_number)
            if sample:
                samples.append(sample)

        return samples

    def _parse_sample_lines(self, lines: list, page_number: int) -> Optional[Sample]:
        """Parse vertical sample lines into a Sample object.

        Logic ported from core_analysis.py to ensure correct field alignment.
        """
        try:
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
            notes = ""

            idx = 0

            # Permeability to Air (can be number, "<X", or "+")
            if idx < len(values):
                val = values[idx]
                if val == '+':
                    # Fracture sample: no permeability measurement
                    notes = "fracture"
                    idx += 1
                    # For fractures: porosity, grain_density, then saturations
                    if idx < len(values):
                        porosity_amb = self._parse_float(values[idx])
                        idx += 1
                    if idx < len(values):
                        grain_density = self._parse_float(values[idx])
                        idx += 1
                elif val.startswith('<'):
                    # Below detection limit
                    perm_air = val  # Keep as string to preserve "<"
                    notes = f"perm{val}"
                    idx += 1
                    # For <X: porosity_amb, porosity_ncs, grain_density, then saturations
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
                    notes = (notes + "; no_saturations").strip("; ")
                else:
                    sat_water = self._parse_float(val)
                    idx += 1
                    if idx < len(values):
                        sat_oil = self._parse_float(values[idx])
                        idx += 1
                    if idx < len(values):
                        sat_total = self._parse_float(values[idx])

            return Sample(
                core_number=core_num,
                sample_number=sample_num,
                depth_feet=str(depth) if depth else "",
                permeability_air_md=str(perm_air) if perm_air is not None else "",
                permeability_klink_md=str(perm_klink) if perm_klink is not None else "",
                porosity_ambient_pct=str(porosity_amb) if porosity_amb is not None else "",
                porosity_ncs_pct=str(porosity_ncs) if porosity_ncs is not None else "",
                grain_density_gcc=str(grain_density) if grain_density is not None else "",
                saturation_water_pct=str(sat_water) if sat_water is not None else "",
                saturation_oil_pct=str(sat_oil) if sat_oil is not None else "",
                saturation_total_pct=str(sat_total) if sat_total is not None else "",
                page_number=page_number,
                notes=notes,
            )
        except Exception:
            return None

    def _parse_depth(self, value: str) -> Optional[float]:
        """Parse a depth value like '9,580.50'."""
        try:
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

    def save_csv(self, result: ExtractionResult, output_path: Path):
        """Save samples to CSV."""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADERS)
            writer.writeheader()
            for sample in result.samples:
                writer.writerow(asdict(sample))

    def save_json(self, result: ExtractionResult, output_path: Path):
        """Save full result to JSON."""
        output = {
            "source_file": str(self.pdf_path),
            "stats": result.stats,
            "classifications": result.classifications,
            "samples": [asdict(s) for s in result.samples]
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Minimal Core Analysis extraction (single-pass, no database)"
    )
    parser.add_argument("pdf_file", help="Path to PDF file")
    parser.add_argument("--output", "-o", help="Output directory")
    parser.add_argument("--json-output", action="store_true",
                        help="Print JSON to stdout")
    parser.add_argument("--classify-only", action="store_true",
                        help="Only classify pages, don't extract data")

    args = parser.parse_args()

    extractor = CoreAnalysisMinimal(args.pdf_file)
    result = extractor.extract()

    print(f"\n=== Core Analysis Extraction (Minimal) ===")
    print(f"Source: {args.pdf_file}")
    print(f"Processing time: {result.timing_ms:.1f} ms")
    print(f"\nClassification Summary:")
    for cls, count in result.stats["classification_counts"].items():
        print(f"  {cls}: {count} pages")

    if not args.classify_only:
        print(f"\nExtraction Summary:")
        print(f"  Table pages: {result.table_pages}")
        print(f"  Samples extracted: {len(result.samples)}")

        if result.samples:
            depths = [float(s.depth_feet) for s in result.samples if s.depth_feet]
            if depths:
                print(f"  Depth range: {min(depths):.2f} - {max(depths):.2f} feet")

    if args.json_output:
        print("\n" + json.dumps({
            "classifications": result.classifications,
            "stats": result.stats
        }, indent=2))

    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        csv_path = output_dir / "core_analysis_minimal.csv"
        json_path = output_dir / "core_analysis_minimal.json"

        extractor.save_csv(result, csv_path)
        extractor.save_json(result, json_path)

        print(f"\nOutputs saved:")
        print(f"  CSV: {csv_path}")
        print(f"  JSON: {json_path}")


if __name__ == "__main__":
    main()
