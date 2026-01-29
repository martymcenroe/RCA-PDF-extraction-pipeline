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
        """Parse vertical sample lines into a Sample object."""
        if len(lines) < 5:
            return None

        sample = Sample(page_number=page_number)
        sample.core_number = lines[0]
        sample.sample_number = lines[1]
        sample.depth_feet = lines[2].replace(',', '')

        # Remaining values
        values = lines[3:]
        idx = 0

        # First value is permeability_air or "+" for fractures
        if idx < len(values):
            val = values[idx]
            if val == '+':
                # Fracture sample: +, porosity, grain_density, [saturations]
                sample.notes = "fracture"
                idx += 1
                if idx < len(values):
                    sample.porosity_ambient_pct = values[idx]
                    idx += 1
                if idx < len(values):
                    sample.grain_density_gcc = values[idx]
                    idx += 1
            elif val.startswith('<'):
                # Below detection: <0.0001, porosity, [porosity_ncs], grain_density, [saturations]
                sample.permeability_air_md = val
                sample.notes = f"below_detection({val})"
                idx += 1
                # Parse remaining values
                remaining = values[idx:]
                self._parse_remaining_values(sample, remaining)
                return sample
            else:
                # Normal: perm_air, perm_klink, por_amb, por_ncs, grain_den, sat_w, sat_o, sat_t
                sample.permeability_air_md = val
                idx += 1
                if idx < len(values):
                    sample.permeability_klink_md = values[idx]
                    idx += 1

        # Continue with porosity values
        if idx < len(values):
            sample.porosity_ambient_pct = values[idx]
            idx += 1
        if idx < len(values) and not values[idx].startswith('2.'):
            # porosity_ncs if not already at grain density
            sample.porosity_ncs_pct = values[idx]
            idx += 1

        # Grain density (always 2.xx)
        if idx < len(values):
            sample.grain_density_gcc = values[idx]
            idx += 1

        # Saturations (may be ** for no data)
        if idx < len(values) and values[idx] != '**':
            sample.saturation_water_pct = values[idx]
        idx += 1
        if idx < len(values) and values[idx] != '**':
            sample.saturation_oil_pct = values[idx]
        idx += 1
        if idx < len(values) and values[idx] != '**':
            sample.saturation_total_pct = values[idx]

        return sample

    def _parse_remaining_values(self, sample: Sample, values: list):
        """Parse remaining values after permeability for below-detection samples."""
        # Look for grain density (2.xx) to anchor the parsing
        grain_idx = None
        for i, v in enumerate(values):
            if re.match(r'^2\.\d{2}$', v):
                grain_idx = i
                break

        if grain_idx is None:
            return

        # Values before grain density are porosities
        if grain_idx >= 1:
            sample.porosity_ambient_pct = values[grain_idx - 1]
        if grain_idx >= 2:
            sample.porosity_ncs_pct = values[grain_idx - 2]

        sample.grain_density_gcc = values[grain_idx]

        # Values after grain density are saturations
        sat_values = values[grain_idx + 1:]
        if len(sat_values) >= 1 and sat_values[0] != '**':
            sample.saturation_water_pct = sat_values[0]
        if len(sat_values) >= 2 and sat_values[1] != '**':
            sample.saturation_oil_pct = sat_values[1]
        if len(sat_values) >= 3 and sat_values[2] != '**':
            sample.saturation_total_pct = sat_values[2]

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
