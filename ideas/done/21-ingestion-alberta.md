# Idea: Alberta AER Data Ingestion Module

**Status:** Enhancement
**Effort:** Low-Medium
**Value:** High - Canadian non-confidential wells, WCSB formations

---

## Problem

The Alberta Energy Regulator (AER) maintains extensive well data from the Western Canadian Sedimentary Basin (WCSB). This provides exposure to Canadian petroleum geology, different regulatory formats, and formations not well-represented in US data (Montney, Duvernay, Cardium). The AER has good data availability for non-confidential wells.

## Technical Context

### AER Data Portal

- **Portal:** https://www.aer.ca/ or DDS (Digital Data Submission)
- **Data System:** AER Integrated Resource Information System (IRIS)
- **Coverage:** Alberta wells (WCSB)
- **Auth:** Public access for non-confidential wells
- **Format:** PDFs, LAS files, structured data

### Data Availability

- **Confidentiality Period:** Typically 1 year from well completion
- **Non-confidential wells:** Vast majority of historical wells
- **Core data:** Available for wells with core runs
- **Focus:** Non-confidential wells with RCA data

### Key Identifiers

- UWI (Unique Well Identifier) format: XX-XX-XXX-XXWXM
- License numbers
- Formation/Pool codes

### Formations of Interest

- **Montney** - Major unconventional play
- **Duvernay** - Shale gas/liquids
- **Cardium** - Light oil
- **Viking** - Conventional oil
- **Mannville** - Heavy oil

## Proposal

Implement `AlbertaModule` with focus on:

1. Query non-confidential wells with core data
2. Filter by priority formations
3. Download RCA documents with rate limiting
4. Handle Canadian data format conventions

## Implementation

### Module Structure

```python
# src/ingestion/modules/alberta.py
import httpx
from pathlib import Path
from ..core import SourceModule, DownloadJob

class AlbertaModule(SourceModule):
    """Alberta Energy Regulator data module."""

    name = "alberta"
    base_url = "https://www.aer.ca/data"  # Confirm actual API endpoint
    rate_limit = 1.0

    # Priority formations
    PRIORITY_FORMATIONS = [
        "Montney",
        "Duvernay",
        "Cardium",
        "Viking",
        "Mannville",
        "Leduc",
        "Nisku",
        "Wabamun"
    ]

    async def discover_documents(self, limit: int = 50) -> list[DownloadJob]:
        """Discover RCA documents from AER."""
        jobs = []

        async with httpx.AsyncClient() as client:
            for formation in self.PRIORITY_FORMATIONS:
                if len(jobs) >= limit:
                    break

                wells = await self._search_formation(client, formation)

                for well in wells:
                    if len(jobs) >= limit:
                        break

                    # Skip confidential wells
                    if well.get("confidential"):
                        continue

                    # Skip wells without core data
                    if not well.get("has_core"):
                        continue

                    docs = await self._get_well_documents(client, well["uwi"])
                    for doc in docs:
                        if self._is_rca_document(doc) and len(jobs) < limit:
                            jobs.append(self._create_job(well, doc, formation))

        return jobs

    async def _search_formation(self, client: httpx.AsyncClient, formation: str) -> list[dict]:
        """Search for wells with core data in a formation."""
        await asyncio.sleep(1 / self.rate_limit)

        response = await client.get(
            f"{self.base_url}/api/wells",
            params={
                "formation": formation,
                "hasCore": True,
                "confidential": False,
                "limit": 100
            }
        )
        response.raise_for_status()
        return response.json().get("wells", [])

    async def _get_well_documents(self, client: httpx.AsyncClient, uwi: str) -> list[dict]:
        """Get documents for a specific well by UWI."""
        await asyncio.sleep(1 / self.rate_limit)

        # UWI may need encoding for URL
        uwi_encoded = uwi.replace("/", "-").replace(" ", "")

        response = await client.get(
            f"{self.base_url}/api/wells/{uwi_encoded}/documents"
        )
        response.raise_for_status()
        return response.json().get("documents", [])

    def _is_rca_document(self, doc: dict) -> bool:
        """Filter for RCA-related documents."""
        keywords = [
            "core analysis", "rca", "routine core",
            "porosity", "permeability", "core report",
            "petrophysical", "reservoir"
        ]
        name = doc.get("name", "").lower()
        doc_type = doc.get("document_type", "").lower()
        return any(kw in name or kw in doc_type for kw in keywords)

    def _create_job(self, well: dict, doc: dict, formation: str) -> DownloadJob:
        return DownloadJob(
            well_id=well["uwi"],
            url=doc["download_url"],
            metadata={
                "region": "Alberta",
                "formation": formation,
                "uwi": well["uwi"],
                "well_name": well.get("name"),
                "license": well.get("license"),
                "operator": well.get("operator"),
                "completion_date": well.get("completion_date"),
                "document_type": doc.get("document_type"),
                "document_name": doc.get("name")
            }
        )

    def get_target_path(self, job: DownloadJob) -> Path:
        """Path: data/raw/alberta/{formation}/{uwi}.pdf.zst"""
        formation = job.metadata.get("formation", "unknown").replace(" ", "_")
        # Sanitize UWI for filesystem
        uwi = job.well_id.replace("/", "_").replace("-", "_").replace(" ", "")
        return Path(f"data/raw/alberta/{formation}/{uwi}.pdf.zst")
```

### UWI Handling

```python
class AlbertaModule(SourceModule):
    # ... base implementation above ...

    @staticmethod
    def parse_uwi(uwi: str) -> dict:
        """Parse Canadian UWI into components."""
        # Format: LE-LSd-Sec-Twp-Rge-Mer
        # Example: 100/06-12-034-05W4/0
        parts = uwi.replace("/", "-").split("-")

        if len(parts) >= 6:
            return {
                "location_exception": parts[0],
                "legal_subdivision": parts[1],
                "section": parts[2],
                "township": parts[3],
                "range": parts[4],
                "meridian": parts[5],
                "event_sequence": parts[6] if len(parts) > 6 else "0"
            }
        return {"raw": uwi}

    @staticmethod
    def sanitize_uwi_for_path(uwi: str) -> str:
        """Convert UWI to filesystem-safe format."""
        # 100/06-12-034-05W4/0 -> 100_06_12_034_05W4_0
        return uwi.replace("/", "_").replace("-", "_").replace(" ", "")
```

## Storage & Compression

```
data/raw/alberta/
  Montney/
    100_06_12_034_05W4_0.pdf.zst
    100_07_15_078_23W6_0.pdf.zst
  Duvernay/
    100_10_33_052_03W5_0.pdf.zst
  Cardium/
    100_04_28_041_07W5_0.pdf.zst
  manifest.json
  metrics.json
```

### Manifest Entry Example

```json
{
  "well_id": "100/06-12-034-05W4/0",
  "source_url": "https://www.aer.ca/data/api/documents/xyz123",
  "local_path": "data/raw/alberta/Montney/100_06_12_034_05W4_0.pdf.zst",
  "sha256": "pqr901...",
  "size_bytes": 2200000,
  "compressed_size": 1650000,
  "downloaded_at": "2026-01-31T15:00:00Z",
  "metadata": {
    "region": "Alberta",
    "formation": "Montney",
    "uwi": "100/06-12-034-05W4/0",
    "well_name": "CNRL HZ MONTNEY 06-12",
    "license": "0501234",
    "operator": "Canadian Natural Resources"
  }
}
```

## Resilience

### Alberta-Specific Considerations

- **Confidentiality filtering** - Must not attempt to download confidential data
- **UWI format variations** - Handle different UWI representations
- **Large historical dataset** - Many old wells with varying data quality
- **Formation overlap** - Wells may have data from multiple formations

```python
class AlbertaModule(SourceModule):
    async def download_document(self, job: DownloadJob) -> bytes:
        """Download with confidentiality check."""
        async with httpx.AsyncClient() as client:
            # Pre-flight check for confidentiality
            well_status = await self._check_well_status(client, job.well_id)

            if well_status.get("confidential"):
                raise ConfidentialDataError(
                    f"Well {job.well_id} is confidential, skipping"
                )

            return await download_with_retry(job.url)

    async def _check_well_status(self, client: httpx.AsyncClient, uwi: str) -> dict:
        """Verify well is non-confidential before download."""
        response = await client.get(
            f"{self.base_url}/api/wells/{self.sanitize_uwi_for_path(uwi)}/status"
        )
        return response.json()
```

### Error Classification

```python
def classify_error(self, response: httpx.Response, well_id: str) -> str:
    if response.status_code == 403:
        return "confidential"  # Log and skip
    elif response.status_code == 404:
        return "not_found"
    elif response.status_code == 429:
        return "rate_limited"
    else:
        return "transient"
```

## Testing

### Unit Tests

```python
# tests/ingestion/test_alberta.py
class TestAlbertaModule:
    def test_formation_search_returns_wells(self, mock_response): ...
    def test_uwi_parsing(self):
        uwi = "100/06-12-034-05W4/0"
        parsed = AlbertaModule.parse_uwi(uwi)
        assert parsed["section"] == "12"
        assert parsed["township"] == "034"

    def test_uwi_sanitization(self):
        uwi = "100/06-12-034-05W4/0"
        safe = AlbertaModule.sanitize_uwi_for_path(uwi)
        assert safe == "100_06_12_034_05W4_0"

    def test_confidential_well_skipped(self, mock_response): ...
    def test_rca_document_filtering(self): ...
```

### Integration Tests

```python
class TestAlbertaIntegration:
    def test_end_to_end_download(self, mock_aer_server):
        result = run_ingestion("alberta", limit=3)
        assert result.downloaded == 3
        assert Path("data/raw/alberta/manifest.json").exists()

    def test_formation_rotation(self, mock_aer_server):
        """Verify multiple formations are queried."""
        result = run_ingestion("alberta", limit=15)
        formations = {e.metadata["formation"] for e in result.entries}
        assert len(formations) > 1

    def test_confidential_filtering(self, mock_aer_server_with_confidential):
        """Verify confidential wells are not downloaded."""
        result = run_ingestion("alberta", limit=10)
        assert all(not e.metadata.get("confidential") for e in result.entries)
```

### Smoke Test

```bash
python -m src.ingestion ingest alberta --limit 1 --dry-run
python -m src.ingestion ingest alberta --limit 3
cat data/raw/alberta/manifest.json | jq .
```

## Next Steps

- [ ] Explore AER data portal to confirm API structure
- [ ] Document UWI format variations
- [ ] Implement `AlbertaModule` class
- [ ] Add formation search functionality
- [ ] Implement confidentiality checking
- [ ] Add UWI parsing and sanitization
- [ ] Write unit tests
- [ ] Run smoke test against AER
- [ ] Document any registration requirements
