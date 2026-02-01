# Idea: UK National Data Repository Ingestion Module

**Status:** Enhancement
**Effort:** Medium (granular lookups, no bulk API)
**Value:** High - North Sea RCA data with different geological context

---

## Problem

The UK National Data Repository (NDR) contains decades of North Sea well data including RCA reports. Unlike US sources, this provides exposure to offshore, deep-water, and different lithology types essential for model diversity. However, the NDR requires granular well-by-well lookups rather than bulk downloads.

## Technical Context

### UK NDR Portal

- **Portal:** https://ndr.ogauthority.co.uk/
- **Data Authority:** North Sea Transition Authority (NSTA, formerly OGA)
- **Auth:** Public access, some data may require registration
- **Coverage:** UK Continental Shelf (UKCS) - North Sea, Celtic Sea, Atlantic Margin
- **Format:** PDFs, LAS files, images, structured data

### API Characteristics

- **No bulk download API** - must query individual wells
- Search by well name, license block, or quadrant
- Well status affects data availability (released vs. confidential)
- Documents organized by well with multiple document types

### Key Identifiers

- Well registration numbers (e.g., "9/13a-A1")
- License blocks (e.g., "P.123")
- Quadrant/Block format (e.g., "9/13a")

### Data Release Policy

- Most data released after confidentiality period
- Newer wells may have restricted access
- Focus on released/public wells

## Proposal

Implement `UKModule` with focus on:

1. Quadrant-by-quadrant discovery (North Sea focus)
2. Filter for wells with core data
3. Per-well document enumeration
4. RCA document download with rate limiting

## Implementation

### Module Structure

```python
# src/ingestion/modules/uk.py
import httpx
from ..core import SourceModule, DownloadJob

class UKModule(SourceModule):
    """UK National Data Repository module."""

    name = "uk"
    base_url = "https://ndr.ogauthority.co.uk"
    rate_limit = 0.5  # Conservative: 1 request per 2 seconds

    # Priority quadrants (productive North Sea areas)
    PRIORITY_QUADRANTS = [
        "9",   # Central North Sea
        "16",  # Brent area
        "22",  # Central Graben
        "30",  # Southern North Sea
        "21",  # Forties area
        "15",  # East Shetland Basin
    ]

    async def discover_documents(self, limit: int = 50) -> list[DownloadJob]:
        """Discover RCA documents from UK NDR."""
        jobs = []

        async with httpx.AsyncClient() as client:
            for quadrant in self.PRIORITY_QUADRANTS:
                if len(jobs) >= limit:
                    break

                wells = await self._search_quadrant(client, quadrant)
                for well in wells:
                    if len(jobs) >= limit:
                        break

                    # Skip if well has no core data indicator
                    if not well.get("has_core_data"):
                        continue

                    docs = await self._get_well_documents(client, well["well_id"])
                    for doc in docs:
                        if self._is_rca_document(doc) and len(jobs) < limit:
                            jobs.append(self._create_job(well, doc))

        return jobs

    async def _search_quadrant(self, client: httpx.AsyncClient, quadrant: str) -> list[dict]:
        """Search for wells in a quadrant with core data."""
        await self._rate_limit()

        # NDR may use POST for searches
        response = await client.post(
            f"{self.base_url}/api/wells/search",
            json={
                "quadrant": quadrant,
                "status": "RELEASED",  # Only public data
                "hasCore": True
            }
        )
        response.raise_for_status()
        return response.json().get("wells", [])

    async def _get_well_documents(self, client: httpx.AsyncClient, well_id: str) -> list[dict]:
        """Get documents for a specific well (granular lookup)."""
        await self._rate_limit()

        response = await client.get(
            f"{self.base_url}/api/wells/{well_id}/documents"
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

    async def _rate_limit(self):
        """Apply conservative rate limiting."""
        await asyncio.sleep(1 / self.rate_limit)

    def _create_job(self, well: dict, doc: dict) -> DownloadJob:
        return DownloadJob(
            well_id=well["well_id"],
            url=doc["download_url"],
            metadata={
                "region": "UKCS",
                "quadrant": well.get("quadrant"),
                "block": well.get("block"),
                "well_name": well.get("name"),
                "operator": well.get("operator"),
                "spud_date": well.get("spud_date"),
                "document_type": doc.get("document_type"),
                "document_name": doc.get("name")
            }
        )

    def get_target_path(self, job: DownloadJob) -> Path:
        """Path: data/raw/uk/{quadrant}/{well_name}.pdf.zst"""
        quadrant = job.metadata.get("quadrant", "unknown")
        # Sanitize well name for filesystem
        well_name = job.well_id.replace("/", "_").replace(" ", "_")
        return Path(f"data/raw/uk/Q{quadrant}/{well_name}.pdf.zst")
```

### Quadrant Priority Rationale

Ordered by:
1. Core data availability (major oil fields)
2. Formation diversity (Brent, Forties, Jurassic, Triassic)
3. Data release status (older fields = more public data)

## Storage & Compression

```
data/raw/uk/
  Q9/
    9_13a_A1.pdf.zst
    9_18b_2.pdf.zst
  Q16/
    16_29a_1.pdf.zst
  Q22/
    22_10_1.pdf.zst
  manifest.json
  metrics.json
```

### Manifest Entry Example

```json
{
  "well_id": "9/13a-A1",
  "source_url": "https://ndr.ogauthority.co.uk/api/documents/xyz789",
  "local_path": "data/raw/uk/Q9/9_13a_A1.pdf.zst",
  "sha256": "ghi012...",
  "size_bytes": 3200000,
  "compressed_size": 2400000,
  "downloaded_at": "2026-01-31T12:00:00Z",
  "metadata": {
    "region": "UKCS",
    "quadrant": "9",
    "block": "13a",
    "well_name": "9/13a-A1",
    "operator": "BP",
    "spud_date": "1975-03-15"
  }
}
```

## Resilience

### UK-Specific Considerations

- **Conservative rate limiting** - UK government portals may be sensitive
- **Graceful 403 handling** - Some wells may be restricted despite filter
- **Session management** - Portal may require session tokens
- **Timeout adjustment** - International requests may be slower

```python
class UKModule(SourceModule):
    # Override timeout for international requests
    DEFAULT_TIMEOUT = 60.0  # seconds

    async def download_document(self, job: DownloadJob) -> bytes:
        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            return await download_with_retry(job.url, timeout=self.DEFAULT_TIMEOUT)
```

### Error Classification

```python
def classify_error(self, response: httpx.Response, well_id: str) -> str:
    if response.status_code == 403:
        return "restricted"  # Log and skip
    elif response.status_code == 404:
        return "not_found"  # Well exists but document removed
    elif response.status_code == 429:
        return "rate_limited"  # Back off significantly
    else:
        return "transient"  # Retry
```

## Testing

### Unit Tests

```python
# tests/ingestion/test_uk.py
class TestUKModule:
    def test_quadrant_search_returns_wells(self, mock_response): ...
    def test_well_id_sanitization(self): ...
    def test_rca_document_filtering(self): ...
    def test_conservative_rate_limiting(self): ...
    def test_graceful_403_handling(self, mock_response): ...
    def test_timeout_handling(self, slow_mock_response): ...
```

### Integration Tests

```python
class TestUKIntegration:
    def test_end_to_end_download(self, mock_uk_server):
        result = run_ingestion("uk", limit=3)
        assert result.downloaded == 3
        assert Path("data/raw/uk/manifest.json").exists()

    def test_restricted_wells_skipped(self, mock_uk_server_with_restricted):
        result = run_ingestion("uk", limit=5)
        assert result.skipped > 0
        assert "restricted" in result.skip_reasons
```

### Smoke Test

```bash
python -m src.ingestion ingest uk --limit 1 --dry-run
python -m src.ingestion ingest uk --limit 3
cat data/raw/uk/manifest.json | jq .
```

## Next Steps

- [ ] Explore NDR portal to confirm API structure
- [ ] Check for registration requirements
- [ ] Implement `UKModule` class
- [ ] Add quadrant search functionality
- [ ] Implement well-level document enumeration
- [ ] Test rate limiting thoroughly
- [ ] Write unit tests with mocked responses
- [ ] Run smoke test against live portal
- [ ] Document any auth/registration requirements
