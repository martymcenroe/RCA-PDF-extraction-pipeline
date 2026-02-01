# Idea: Texas University Lands Data Ingestion Module

**Status:** Enhancement
**Effort:** Low-Medium
**Value:** High - Texas Permian Basin is a major RCA source

---

## Problem

Texas University Lands manages millions of acres in the Permian Basin with well data available through a public portal. This represents one of the richest sources of RCA data for West Texas formations. The ingestion pipeline needs a module to acquire this data systematically.

## Technical Context

### University Lands Portal

- **Portal:** https://ulands.utexas.edu/ or data portal
- **Data Type:** Well logs, core analysis, production data
- **Auth:** Public access (may require registration for bulk)
- **Coverage:** Permian Basin (West Texas), primarily University Lands acreage
- **Format:** PDFs, LAS files, some structured data

### API Characteristics

- REST-like endpoints for well queries
- Search by county, API number, formation
- Individual document downloads
- No explicit bulk download API (polite crawling required)

### Key Identifiers

- API numbers (Texas format: 42-XXX-XXXXX)
- Survey/Block/Section identifiers
- County names (Andrews, Ector, Winkler, etc.)

## Proposal

Implement `TexasModule` following the core framework pattern:

1. Query wells by priority counties
2. Filter for RCA-related documents
3. Download with rate limiting (1 req/sec)
4. Compress and store per framework conventions

## Implementation

### Module Structure

```python
# src/ingestion/modules/texas.py
import httpx
from ..core import SourceModule, DownloadJob

class TexasModule(SourceModule):
    """Texas University Lands data module."""

    name = "texas"
    base_url = "https://ulands.utexas.edu"  # Confirm actual API endpoint
    rate_limit = 1.0

    # Priority counties in Permian Basin
    PRIORITY_COUNTIES = [
        "Andrews", "Ector", "Winkler", "Ward", "Crane",
        "Upton", "Reagan", "Irion", "Crockett", "Pecos"
    ]

    async def discover_documents(self, limit: int = 50) -> list[DownloadJob]:
        """Discover RCA documents from Texas University Lands."""
        jobs = []

        async with httpx.AsyncClient() as client:
            for county in self.PRIORITY_COUNTIES:
                if len(jobs) >= limit:
                    break

                wells = await self._search_county(client, county)
                for well in wells:
                    if len(jobs) >= limit:
                        break

                    docs = await self._get_well_documents(client, well["api"])
                    for doc in docs:
                        if self._is_rca_document(doc) and len(jobs) < limit:
                            jobs.append(self._create_job(well, doc))

        return jobs

    async def _search_county(self, client: httpx.AsyncClient, county: str) -> list[dict]:
        """Search for wells in a county."""
        # Implementation depends on actual API structure
        await asyncio.sleep(1 / self.rate_limit)  # Rate limit
        response = await client.get(
            f"{self.base_url}/api/wells",
            params={"county": county, "has_core": True}
        )
        response.raise_for_status()
        return response.json().get("wells", [])

    async def _get_well_documents(self, client: httpx.AsyncClient, api: str) -> list[dict]:
        """Get documents for a specific well."""
        await asyncio.sleep(1 / self.rate_limit)
        response = await client.get(f"{self.base_url}/api/wells/{api}/documents")
        response.raise_for_status()
        return response.json().get("documents", [])

    def _is_rca_document(self, doc: dict) -> bool:
        """Filter for RCA-related documents."""
        keywords = ["core analysis", "rca", "porosity", "permeability", "routine"]
        name = doc.get("name", "").lower()
        doc_type = doc.get("type", "").lower()
        return any(kw in name or kw in doc_type for kw in keywords)

    def _create_job(self, well: dict, doc: dict) -> DownloadJob:
        """Create download job from well and document info."""
        return DownloadJob(
            well_id=well["api"],
            url=doc["download_url"],
            metadata={
                "state": "TX",
                "county": well.get("county"),
                "api_number": well["api"],
                "well_name": well.get("name", "Unknown"),
                "formation": well.get("formation"),
                "document_type": doc.get("type"),
                "document_name": doc.get("name")
            }
        )

    def get_target_path(self, job: DownloadJob) -> Path:
        """Path: data/raw/texas/{county}/{api_number}.pdf.zst"""
        county = job.metadata.get("county", "unknown").replace(" ", "_")
        api = job.well_id.replace("-", "_")
        return Path(f"data/raw/texas/{county}/{api}.pdf.zst")
```

### County Priority Rationale

Ordered by:
1. Core availability (known core data density)
2. Formation diversity (multiple stacked plays)
3. Data quality (better documentation)

## Storage & Compression

Follows core framework conventions:

```
data/raw/texas/
  Andrews/
    42_003_12345.pdf.zst
    42_003_12346.pdf.zst
  Ector/
    42_135_23456.pdf.zst
  manifest.json
  metrics.json
```

### Manifest Entry Example

```json
{
  "well_id": "42-003-12345",
  "source_url": "https://ulands.utexas.edu/api/documents/abc123",
  "local_path": "data/raw/texas/Andrews/42_003_12345.pdf.zst",
  "sha256": "def456...",
  "size_bytes": 1800000,
  "compressed_size": 1350000,
  "downloaded_at": "2026-01-31T11:00:00Z",
  "metadata": {
    "state": "TX",
    "county": "Andrews",
    "api_number": "42-003-12345",
    "well_name": "University 1-15",
    "formation": "Spraberry"
  }
}
```

## Resilience

Inherits from core framework:
- Retry with exponential backoff (3 attempts)
- Circuit breaker for source-level failures
- Checkpoint after each successful download
- Idempotent operations (skip existing)

### Texas-Specific Considerations

- Portal may have session timeouts - handle re-auth gracefully
- Some documents may be restricted - log and skip, don't fail
- API number validation before download attempts

## Testing

### Unit Tests

```python
# tests/ingestion/test_texas.py
class TestTexasModule:
    def test_county_search_returns_wells(self, mock_response): ...
    def test_rca_document_filtering(self): ...
    def test_api_number_validation(self): ...
    def test_rate_limiting_applied(self): ...
    def test_graceful_403_handling(self, mock_response): ...
```

### Integration Tests

```python
class TestTexasIntegration:
    def test_end_to_end_download(self, mock_texas_server):
        result = run_ingestion("texas", limit=3)
        assert result.downloaded == 3
        assert Path("data/raw/texas/manifest.json").exists()

    def test_county_rotation(self, mock_texas_server):
        """Verify multiple counties are queried."""
        result = run_ingestion("texas", limit=10)
        counties = {e.metadata["county"] for e in result.entries}
        assert len(counties) > 1
```

### Smoke Test

```bash
python -m src.ingestion ingest texas --limit 1 --dry-run
python -m src.ingestion ingest texas --limit 3
cat data/raw/texas/manifest.json | jq .
```

## Next Steps

- [ ] Confirm actual API endpoints (may need portal exploration)
- [ ] Implement `TexasModule` class
- [ ] Add county search functionality
- [ ] Add document filtering logic
- [ ] Write unit tests with mocked responses
- [ ] Run smoke test against live portal
- [ ] Document any auth requirements discovered
