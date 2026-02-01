# Idea: Australian WAPIMS Data Ingestion Module

**Status:** Enhancement
**Effort:** Medium
**Value:** High - Australian basins with unique geology, basket/batch feature

---

## Problem

Western Australia's WAPIMS (Western Australia Petroleum and Geothermal Information Management System) contains extensive well data from Australian basins. Australia provides exposure to different geological settings (Permian basins, Browse Basin) and the WAPIMS portal offers a unique basket/batch download feature that can improve efficiency.

## Technical Context

### WAPIMS Portal

- **Portal:** https://wapims.dmp.wa.gov.au/
- **Data Authority:** Department of Mines, Industry Regulation and Safety (DMIRS)
- **Coverage:** Western Australian basins (Carnarvon, Perth, Browse, Canning, etc.)
- **Auth:** Public access, some data may require registration
- **Format:** PDFs, LAS files, structured data

### Basket/Batch Feature

WAPIMS offers a "shopping basket" feature:
1. Add multiple wells to basket
2. Submit batch download request
3. Receive download link when ready (may be async)

This is more efficient than individual downloads for bulk acquisition.

### Key Identifiers

- Well names (e.g., "Goodwyn 6")
- Permit numbers
- Basin/sub-basin classification

### Basins of Interest

- **Carnarvon Basin** - Major hydrocarbon province (North West Shelf)
- **Perth Basin** - Onshore and offshore
- **Browse Basin** - Gas-rich area
- **Canning Basin** - Large onshore basin

## Proposal

Implement `AustraliaModule` with basket-aware download:

1. Discover wells with RCA data by basin
2. Add to basket up to limit
3. Submit batch download
4. Poll for completion or download individual files
5. Extract and store with compression

## Implementation

### Module Structure

```python
# src/ingestion/modules/australia.py
import httpx
from pathlib import Path
from ..core import SourceModule, DownloadJob

class AustraliaModule(SourceModule):
    """Australian WAPIMS data module with basket support."""

    name = "australia"
    base_url = "https://wapims.dmp.wa.gov.au"
    rate_limit = 1.0

    # Priority basins
    PRIORITY_BASINS = [
        "Carnarvon",
        "Perth",
        "Browse",
        "Canning",
        "Bonaparte",
    ]

    # Batch settings
    BATCH_SIZE = 10  # Wells per batch request
    BATCH_POLL_INTERVAL = 30  # seconds
    BATCH_MAX_WAIT = 600  # 10 minutes max wait

    async def discover_documents(self, limit: int = 50) -> list[DownloadJob]:
        """Discover RCA documents from WAPIMS."""
        jobs = []

        async with httpx.AsyncClient() as client:
            for basin in self.PRIORITY_BASINS:
                if len(jobs) >= limit:
                    break

                wells = await self._search_basin(client, basin)

                for well in wells:
                    if len(jobs) >= limit:
                        break

                    if not well.get("has_core"):
                        continue

                    docs = await self._get_well_documents(client, well["well_id"])
                    for doc in docs:
                        if self._is_rca_document(doc) and len(jobs) < limit:
                            jobs.append(self._create_job(well, doc, basin))

        return jobs

    async def _search_basin(self, client: httpx.AsyncClient, basin: str) -> list[dict]:
        """Search for wells with core data in a basin."""
        await asyncio.sleep(1 / self.rate_limit)

        response = await client.get(
            f"{self.base_url}/api/wells",
            params={
                "basin": basin,
                "hasCore": True,
                "dataRelease": "released"
            }
        )
        response.raise_for_status()
        return response.json().get("wells", [])

    async def _get_well_documents(self, client: httpx.AsyncClient, well_id: str) -> list[dict]:
        """Get documents for a specific well."""
        await asyncio.sleep(1 / self.rate_limit)

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
            "petrophysical", "reservoir characterisation"
        ]
        name = doc.get("name", "").lower()
        doc_type = doc.get("document_type", "").lower()
        return any(kw in name or kw in doc_type for kw in keywords)

    def _create_job(self, well: dict, doc: dict, basin: str) -> DownloadJob:
        return DownloadJob(
            well_id=well["well_id"],
            url=doc["download_url"],
            metadata={
                "region": "WA",
                "basin": basin,
                "well_name": well.get("name"),
                "permit": well.get("permit"),
                "operator": well.get("operator"),
                "document_type": doc.get("document_type"),
                "document_name": doc.get("name")
            }
        )

    def get_target_path(self, job: DownloadJob) -> Path:
        """Path: data/raw/australia/{basin}/{well_name}.pdf.zst"""
        basin = job.metadata.get("basin", "unknown").replace(" ", "_")
        well_name = job.metadata.get("well_name", job.well_id)
        well_name = well_name.replace(" ", "_").replace("/", "_")
        return Path(f"data/raw/australia/{basin}/{well_name}.pdf.zst")
```

### Basket/Batch Download (Advanced)

```python
class AustraliaModule(SourceModule):
    # ... base implementation above ...

    async def download_batch(self, jobs: list[DownloadJob]) -> dict[str, bytes]:
        """Use basket feature for batch download."""
        async with httpx.AsyncClient() as client:
            # Create basket
            basket_id = await self._create_basket(client)

            # Add items to basket
            for job in jobs:
                await self._add_to_basket(client, basket_id, job.url)

            # Submit batch request
            download_request = await self._submit_basket(client, basket_id)

            # Poll for completion
            download_url = await self._poll_for_download(
                client,
                download_request["request_id"]
            )

            # Download ZIP and extract
            return await self._download_and_extract(client, download_url, jobs)

    async def _create_basket(self, client: httpx.AsyncClient) -> str:
        """Create a new download basket."""
        response = await client.post(f"{self.base_url}/api/basket/create")
        response.raise_for_status()
        return response.json()["basket_id"]

    async def _add_to_basket(self, client: httpx.AsyncClient, basket_id: str, doc_url: str):
        """Add document to basket."""
        await asyncio.sleep(1 / self.rate_limit)
        response = await client.post(
            f"{self.base_url}/api/basket/{basket_id}/add",
            json={"document_url": doc_url}
        )
        response.raise_for_status()

    async def _submit_basket(self, client: httpx.AsyncClient, basket_id: str) -> dict:
        """Submit basket for batch download."""
        response = await client.post(
            f"{self.base_url}/api/basket/{basket_id}/submit"
        )
        response.raise_for_status()
        return response.json()

    async def _poll_for_download(self, client: httpx.AsyncClient, request_id: str) -> str:
        """Poll until batch download is ready."""
        start_time = time.time()

        while time.time() - start_time < self.BATCH_MAX_WAIT:
            await asyncio.sleep(self.BATCH_POLL_INTERVAL)

            response = await client.get(
                f"{self.base_url}/api/batch/{request_id}/status"
            )
            status = response.json()

            if status["state"] == "ready":
                return status["download_url"]
            elif status["state"] == "failed":
                raise BatchDownloadError(f"Batch failed: {status.get('error')}")

        raise BatchTimeoutError(f"Batch not ready after {self.BATCH_MAX_WAIT}s")

    async def _download_and_extract(
        self,
        client: httpx.AsyncClient,
        zip_url: str,
        jobs: list[DownloadJob]
    ) -> dict[str, bytes]:
        """Download ZIP and extract to job mapping."""
        response = await client.get(zip_url)
        response.raise_for_status()

        results = {}
        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            for job in jobs:
                # Map ZIP contents to jobs
                for name in zf.namelist():
                    if self._matches_job(name, job):
                        results[job.well_id] = zf.read(name)
                        break

        return results
```

### Fallback to Individual Downloads

```python
async def download_with_fallback(self, jobs: list[DownloadJob]) -> list[bytes]:
    """Try batch first, fall back to individual downloads."""
    try:
        # Try batch download
        batch_results = await self.download_batch(jobs)
        return [batch_results.get(j.well_id) for j in jobs]
    except (BatchDownloadError, BatchTimeoutError) as e:
        logger.warning(f"Batch failed, falling back to individual: {e}")

        # Fall back to individual downloads
        results = []
        for job in jobs:
            try:
                content = await self.download_document(job)
                results.append(content)
            except Exception as e:
                logger.error(f"Individual download failed: {job.well_id}: {e}")
                results.append(None)

        return results
```

## Storage & Compression

```
data/raw/australia/
  Carnarvon/
    Goodwyn_6.pdf.zst
    North_Rankin_1.pdf.zst
  Perth/
    Dongara_1.pdf.zst
  Browse/
    Ichthys_1.pdf.zst
  manifest.json
  metrics.json
```

### Manifest Entry Example

```json
{
  "well_id": "WA-12345",
  "source_url": "https://wapims.dmp.wa.gov.au/api/documents/abc123",
  "local_path": "data/raw/australia/Carnarvon/Goodwyn_6.pdf.zst",
  "sha256": "mno678...",
  "size_bytes": 2800000,
  "compressed_size": 2100000,
  "downloaded_at": "2026-01-31T14:00:00Z",
  "metadata": {
    "region": "WA",
    "basin": "Carnarvon",
    "well_name": "Goodwyn 6",
    "permit": "TP/12",
    "operator": "Woodside"
  }
}
```

## Resilience

### Australia-Specific Considerations

- **Batch system may be async** - polling with timeout required
- **Time zone differences** - downloads may be queued for off-peak
- **Large ZIP files** - batch downloads can be substantial
- **Session management** - basket may require persistent session

```python
class AustraliaModule(SourceModule):
    # Extended timeouts for batch operations
    BATCH_TIMEOUT = 300.0  # 5 minutes for batch downloads

    def __init__(self):
        super().__init__()
        self.session_token = None
        self.basket_id = None

    async def ensure_session(self, client: httpx.AsyncClient):
        """Ensure we have a valid session for basket operations."""
        if not self.session_token:
            response = await client.post(f"{self.base_url}/api/session/create")
            self.session_token = response.json().get("token")
```

## Testing

### Unit Tests

```python
# tests/ingestion/test_australia.py
class TestAustraliaModule:
    def test_basin_search_returns_wells(self, mock_response): ...
    def test_rca_document_filtering(self): ...
    def test_basket_creation(self, mock_wapims_server): ...
    def test_batch_polling(self, mock_wapims_server): ...
    def test_batch_timeout_fallback(self, slow_mock_server): ...
    def test_zip_extraction(self, mock_zip_response): ...
```

### Integration Tests

```python
class TestAustraliaIntegration:
    def test_end_to_end_individual_download(self, mock_wapims_server):
        result = run_ingestion("australia", limit=3)
        assert result.downloaded == 3

    def test_batch_download(self, mock_wapims_server):
        """Test basket/batch workflow."""
        module = AustraliaModule()
        jobs = [make_test_job() for _ in range(5)]
        results = await module.download_batch(jobs)
        assert len(results) == 5

    def test_basin_rotation(self, mock_wapims_server):
        """Verify multiple basins are queried."""
        result = run_ingestion("australia", limit=15)
        basins = {e.metadata["basin"] for e in result.entries}
        assert len(basins) > 1
```

### Smoke Test

```bash
python -m src.ingestion ingest australia --limit 1 --dry-run
python -m src.ingestion ingest australia --limit 3
cat data/raw/australia/manifest.json | jq .
```

## Next Steps

- [ ] Explore WAPIMS portal to confirm API structure
- [ ] Document basket/batch workflow
- [ ] Implement `AustraliaModule` class
- [ ] Implement individual download first
- [ ] Add basket/batch support (enhancement)
- [ ] Handle async batch polling
- [ ] Implement ZIP extraction
- [ ] Write unit tests
- [ ] Run smoke test against WAPIMS
- [ ] Document any registration requirements
