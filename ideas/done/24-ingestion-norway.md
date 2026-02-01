# Idea: Norwegian DISKOS Data Ingestion Module

**Status:** Enhancement
**Effort:** Medium
**Value:** High - Volve dataset priority, excellent Norwegian data quality

---

## Problem

Norway maintains DISKOS, one of the world's best-organized petroleum data repositories. The Volve dataset (released in 2018) is particularly valuable as a complete, public dataset with high-quality RCA reports. Norwegian data provides exposure to North Sea geology with exceptional documentation standards.

## Technical Context

### DISKOS Portal

- **Portal:** https://www.diskos.no/ or via NPD FactPages
- **Data Authority:** Norwegian Petroleum Directorate (NPD)
- **Volve Dataset:** https://www.equinor.com/energy/volve-data-sharing
- **Auth:** Public access, some data requires registration
- **Coverage:** Norwegian Continental Shelf (NCS)
- **Format:** PDFs, LAS files, SEGY, structured data

### Volve Dataset (Priority)

- Complete field dataset released by Equinor
- 11 years of production data
- All well logs and core data
- Specifically designed for research/training
- **This is the primary target for Norway module**

### API Characteristics

- DISKOS has structured download portal
- NPD FactPages provide well metadata
- Volve has dedicated download area
- Some data in ZIP archives

### Key Identifiers

- Well bore names (e.g., "15/9-F-1")
- NPD well IDs
- License numbers

## Proposal

Implement `NorwayModule` with two-phase approach:

1. **Phase 1 (Priority):** Volve dataset - direct download of known RCA files
2. **Phase 2:** DISKOS exploration for additional wells

The Volve dataset is well-documented with known file locations, making it ideal for initial implementation.

## Implementation

### Module Structure

```python
# src/ingestion/modules/norway.py
import httpx
from pathlib import Path
from ..core import SourceModule, DownloadJob

class NorwayModule(SourceModule):
    """Norwegian DISKOS/Volve data module."""

    name = "norway"
    base_url = "https://www.diskos.no"
    volve_base = "https://data.equinor.com/volve"  # Confirm actual URL
    rate_limit = 1.0

    # Volve wells with known RCA data
    VOLVE_WELLS = [
        {"well": "15/9-F-1", "name": "Volve F-1"},
        {"well": "15/9-F-1A", "name": "Volve F-1A"},
        {"well": "15/9-F-1B", "name": "Volve F-1B"},
        {"well": "15/9-F-1C", "name": "Volve F-1C"},
        {"well": "15/9-F-4", "name": "Volve F-4"},
        {"well": "15/9-F-5", "name": "Volve F-5"},
        {"well": "15/9-F-11", "name": "Volve F-11"},
        {"well": "15/9-F-12", "name": "Volve F-12"},
        {"well": "15/9-F-14", "name": "Volve F-14"},
        {"well": "15/9-F-15D", "name": "Volve F-15D"},
    ]

    async def discover_documents(self, limit: int = 50) -> list[DownloadJob]:
        """Discover RCA documents, prioritizing Volve."""
        jobs = []

        async with httpx.AsyncClient() as client:
            # Phase 1: Volve wells (priority)
            volve_jobs = await self._discover_volve(client, limit)
            jobs.extend(volve_jobs)

            # Phase 2: DISKOS exploration if limit not reached
            if len(jobs) < limit:
                remaining = limit - len(jobs)
                diskos_jobs = await self._discover_diskos(client, remaining)
                jobs.extend(diskos_jobs)

        return jobs[:limit]

    async def _discover_volve(self, client: httpx.AsyncClient, limit: int) -> list[DownloadJob]:
        """Discover Volve dataset RCA documents."""
        jobs = []

        for well_info in self.VOLVE_WELLS:
            if len(jobs) >= limit:
                break

            await asyncio.sleep(1 / self.rate_limit)

            # Get well document listing
            docs = await self._get_volve_well_docs(client, well_info["well"])

            for doc in docs:
                if self._is_rca_document(doc) and len(jobs) < limit:
                    jobs.append(DownloadJob(
                        well_id=well_info["well"],
                        url=doc["download_url"],
                        metadata={
                            "region": "NCS",
                            "dataset": "volve",
                            "field": "Volve",
                            "well_name": well_info["name"],
                            "well_bore": well_info["well"],
                            "document_type": doc.get("type"),
                            "document_name": doc.get("name")
                        }
                    ))

        return jobs

    async def _get_volve_well_docs(self, client: httpx.AsyncClient, well_id: str) -> list[dict]:
        """Get document listing for a Volve well."""
        # Volve data structure is documented - parse known paths
        well_path = well_id.replace("/", "_").replace("-", "_")

        try:
            response = await client.get(
                f"{self.volve_base}/wells/{well_path}/documents"
            )
            response.raise_for_status()
            return response.json().get("documents", [])
        except httpx.HTTPStatusError:
            # Try alternative path patterns
            return await self._try_alternative_volve_paths(client, well_id)

    async def _try_alternative_volve_paths(self, client: httpx.AsyncClient, well_id: str) -> list[dict]:
        """Try alternative Volve file structure patterns."""
        # Volve may use different path conventions
        patterns = [
            f"{self.volve_base}/wellbore/{well_id}/core/",
            f"{self.volve_base}/Well_data/{well_id}/",
        ]

        for pattern in patterns:
            try:
                response = await client.get(pattern)
                if response.status_code == 200:
                    return self._parse_directory_listing(response.text)
            except Exception:
                continue

        return []

    async def _discover_diskos(self, client: httpx.AsyncClient, limit: int) -> list[DownloadJob]:
        """Discover additional wells from DISKOS (Phase 2)."""
        jobs = []

        # Search DISKOS for wells with core data
        # Focus on major fields: Ekofisk, Statfjord, Gullfaks, Oseberg
        major_fields = ["Ekofisk", "Statfjord", "Gullfaks", "Oseberg", "Troll"]

        for field in major_fields:
            if len(jobs) >= limit:
                break

            await asyncio.sleep(1 / self.rate_limit)

            wells = await self._search_diskos_field(client, field)
            for well in wells:
                if len(jobs) >= limit:
                    break

                docs = await self._get_diskos_well_docs(client, well["well_id"])
                for doc in docs:
                    if self._is_rca_document(doc) and len(jobs) < limit:
                        jobs.append(self._create_diskos_job(well, doc))

        return jobs

    def _is_rca_document(self, doc: dict) -> bool:
        """Filter for RCA-related documents."""
        keywords = [
            "core analysis", "rca", "routine core",
            "porosity", "permeability", "kjerne",  # Norwegian: "core"
            "kjerneanalyse",  # Norwegian: "core analysis"
            "petrophysical", "reservoir"
        ]
        name = doc.get("name", "").lower()
        doc_type = doc.get("type", "").lower()
        return any(kw in name or kw in doc_type for kw in keywords)

    def get_target_path(self, job: DownloadJob) -> Path:
        """Path: data/raw/norway/{dataset}/{well_name}.pdf.zst"""
        dataset = job.metadata.get("dataset", "diskos")
        well_name = job.well_id.replace("/", "_").replace("-", "_")
        return Path(f"data/raw/norway/{dataset}/{well_name}.pdf.zst")
```

## Volve Dataset Details

### Known Data Structure

The Volve dataset is organized as:
```
Volve/
  Well_data/
    15_9-F-1/
      Core/
        RCA_report.pdf
        SCAL_report.pdf
    15_9-F-4/
      Core/
        ...
  Seismic/
  Production/
```

### Priority Files

Focus on these document types from Volve:
1. Routine Core Analysis (RCA) reports
2. Special Core Analysis (SCAL) reports
3. Core description reports
4. Petrophysical summaries

## Storage & Compression

```
data/raw/norway/
  volve/
    15_9_F_1.pdf.zst
    15_9_F_1A.pdf.zst
    15_9_F_4.pdf.zst
  diskos/
    Ekofisk_2_4_A_1.pdf.zst
  manifest.json
  metrics.json
```

### Manifest Entry Example

```json
{
  "well_id": "15/9-F-1",
  "source_url": "https://data.equinor.com/volve/Well_data/15_9-F-1/Core/RCA.pdf",
  "local_path": "data/raw/norway/volve/15_9_F_1.pdf.zst",
  "sha256": "jkl345...",
  "size_bytes": 4500000,
  "compressed_size": 3400000,
  "downloaded_at": "2026-01-31T13:00:00Z",
  "metadata": {
    "region": "NCS",
    "dataset": "volve",
    "field": "Volve",
    "well_name": "Volve F-1",
    "well_bore": "15/9-F-1"
  }
}
```

## Resilience

### Norway-Specific Considerations

- **Volve is stable** - well-maintained dataset, low failure rate expected
- **DISKOS may require auth** - handle gracefully
- **ZIP extraction** - some data bundled in archives
- **Large files** - some SCAL reports are 50+ MB

```python
class NorwayModule(SourceModule):
    # Extended timeout for large files
    DEFAULT_TIMEOUT = 120.0
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB limit

    async def download_document(self, job: DownloadJob) -> bytes:
        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.get(job.url, follow_redirects=True)
            response.raise_for_status()

            # Check file size
            if len(response.content) > self.MAX_FILE_SIZE:
                raise FileTooLargeError(f"{job.well_id}: {len(response.content)} bytes")

            return response.content
```

## Testing

### Unit Tests

```python
# tests/ingestion/test_norway.py
class TestNorwayModule:
    def test_volve_well_discovery(self, mock_volve_server): ...
    def test_norwegian_keyword_matching(self): ...
    def test_well_id_sanitization(self): ...
    def test_alternative_path_fallback(self, mock_server): ...
    def test_large_file_handling(self, large_mock_response): ...
```

### Integration Tests

```python
class TestNorwayIntegration:
    def test_volve_priority(self, mock_servers):
        """Verify Volve wells are downloaded first."""
        result = run_ingestion("norway", limit=5)
        assert all(e.metadata["dataset"] == "volve" for e in result.entries)

    def test_diskos_fallback(self, mock_servers):
        """Verify DISKOS used when Volve exhausted."""
        result = run_ingestion("norway", limit=20)
        datasets = {e.metadata["dataset"] for e in result.entries}
        assert "diskos" in datasets
```

### Smoke Test

```bash
python -m src.ingestion ingest norway --limit 1 --dry-run
python -m src.ingestion ingest norway --limit 5
cat data/raw/norway/manifest.json | jq .
```

## Next Steps

- [ ] Confirm Volve dataset download URLs
- [ ] Document Volve directory structure
- [ ] Implement `NorwayModule` class
- [ ] Implement Volve discovery first
- [ ] Add DISKOS fallback (Phase 2)
- [ ] Handle ZIP extraction if needed
- [ ] Write unit tests
- [ ] Run smoke test against Volve
- [ ] Document any registration requirements for DISKOS
