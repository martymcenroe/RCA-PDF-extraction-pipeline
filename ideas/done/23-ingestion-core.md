# Idea: Data Ingestion Core Framework + USGS CRC Module

**Status:** Enhancement
**Effort:** Medium (core framework + first source)
**Value:** High - foundational infrastructure for diverse RCA training data

---

## Problem

To build robust RCA extraction models, we need diverse training data from multiple global sources. Currently there is no automated pipeline to:
- Acquire RCA reports from public geological repositories
- Store them in a consistent, compressed format
- Track provenance and ensure data integrity
- Resume interrupted downloads gracefully

The USGS Core Research Center (CRC) is an ideal first source: public, no authentication, well-structured catalog.

## Technical Context

### USGS CRC API Details

- **Portal:** https://my.usgs.gov/crcwc/
- **Search Endpoint:** Direct catalog browsing by state/basin
- **Auth:** None required (public data)
- **Rate Limits:** Polite crawling expected (1 req/sec)
- **Data Format:** PDFs, some in ZIP archives
- **Catalog Navigation:**
  - Browse by state, then by library number
  - Each core has associated documents (logs, RCA, photos)
  - "Download All" ZIP option available per core

### Key Observations

- Library numbers are the primary identifier
- RCA reports are often bundled with other documents
- Some cores have no RCA data (must filter gracefully)
- ZIP extraction may be required to isolate PDFs

## Proposal

Build the core ingestion framework with three layers:

1. **Base Classes** - `SourceModule`, `DownloadJob`, `ManifestEntry`
2. **Core Controller** - Orchestration, state management, progress tracking
3. **Storage Layer** - zstd compression, path generation, manifest updates

Implement USGS CRC as the first module to validate the architecture.

## Implementation

### Directory Structure

```
src/ingestion/
  __init__.py
  core.py          # Base classes, controller, storage
  modules/
    __init__.py
    usgs.py        # USGS CRC module
  cli.py           # Click-based CLI
```

### Base Classes (core.py)

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime
import hashlib
import json

@dataclass
class ManifestEntry:
    """Single downloaded file in the manifest."""
    well_id: str
    source_url: str
    local_path: str
    sha256: str
    size_bytes: int
    compressed_size: int
    downloaded_at: str
    metadata: dict = field(default_factory=dict)

@dataclass
class DownloadJob:
    """Work unit for downloading a single file."""
    well_id: str
    url: str
    expected_size: Optional[int] = None
    expected_checksum: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    # Filled after download
    actual_size: int = 0
    compressed_size: int = 0
    sha256: str = ""

class SourceModule:
    """Base class for all source modules."""

    name: str = "base"
    base_url: str = ""
    rate_limit: float = 1.0  # requests per second

    async def discover_documents(self, limit: int = 50) -> list[DownloadJob]:
        """Discover available documents from this source."""
        raise NotImplementedError

    async def download_document(self, job: DownloadJob) -> bytes:
        """Download a single document."""
        raise NotImplementedError

    def get_target_path(self, job: DownloadJob) -> Path:
        """Generate storage path for a document."""
        raise NotImplementedError
```

### Core Controller

```python
class IngestionController:
    """Orchestrates downloads across sources with resilience."""

    def __init__(self, sources: list[SourceModule]):
        self.sources = {s.name: s for s in sources}
        self.state_dir = Path("data/state")
        self.raw_dir = Path("data/raw")

    async def run(self, source_names: list[str], limit: int = 50):
        """Run ingestion for specified sources."""
        results = {}

        for name in source_names:
            module = self.sources.get(name)
            if not module:
                continue

            circuit = CircuitBreaker(name)
            state = IngestionState.load(name) or IngestionState(
                source=name,
                started_at=datetime.utcnow().isoformat(),
                completed_wells=[],
                failed_wells={},
                pending_wells=[]
            )

            try:
                result = await self._run_source(module, state, circuit, limit)
                results[name] = result
            except FatalSourceError as e:
                results[name] = SourceResult(status="fatal", error=str(e))
            except Exception as e:
                results[name] = SourceResult(status="error", error=str(e))

        return results
```

### USGS Module (modules/usgs.py)

```python
import httpx
from bs4 import BeautifulSoup
from ..core import SourceModule, DownloadJob

class USGSModule(SourceModule):
    """USGS Core Research Center module."""

    name = "usgs"
    base_url = "https://my.usgs.gov/crcwc"
    rate_limit = 1.0

    async def discover_documents(self, limit: int = 50) -> list[DownloadJob]:
        """Discover RCA documents from USGS catalog."""
        jobs = []

        async with httpx.AsyncClient() as client:
            # Browse catalog by state
            for state in self._priority_states():
                if len(jobs) >= limit:
                    break

                state_docs = await self._get_state_documents(client, state)
                for doc in state_docs:
                    if len(jobs) >= limit:
                        break
                    if self._is_rca_document(doc):
                        jobs.append(self._create_job(doc))

        return jobs

    def _priority_states(self) -> list[str]:
        """States with known good RCA data."""
        return ["TX", "OK", "LA", "NM", "CO", "WY", "ND", "MT", "KS"]

    def _is_rca_document(self, doc: dict) -> bool:
        """Filter for RCA-related documents."""
        keywords = ["routine core analysis", "rca", "core analysis", "porosity"]
        name = doc.get("name", "").lower()
        return any(kw in name for kw in keywords)

    def get_target_path(self, job: DownloadJob) -> Path:
        """Path: data/raw/usgs/{state}/{well_name}_{library_num}.pdf.zst"""
        state = job.metadata.get("state", "unknown")
        library_num = job.metadata.get("library_number", job.well_id)
        well_name = job.metadata.get("well_name", "unknown").replace(" ", "_")
        filename = f"{well_name}_{library_num}.pdf.zst"
        return Path(f"data/raw/usgs/{state}/{filename}")
```

### CLI Interface (cli.py)

```python
import click
import asyncio
from .core import IngestionController
from .modules.usgs import USGSModule

@click.group()
def cli():
    """RCA Data Ingestion Pipeline."""
    pass

@cli.command()
@click.argument("sources", nargs=-1)
@click.option("--limit", default=50, help="Max documents per source")
@click.option("--resume/--no-resume", default=True, help="Resume from checkpoint")
@click.option("--dry-run", is_flag=True, help="Discover only, don't download")
def ingest(sources, limit, resume, dry_run):
    """Ingest documents from specified sources."""
    available = {"usgs": USGSModule()}

    if not sources:
        sources = list(available.keys())

    controller = IngestionController([available[s] for s in sources if s in available])

    if dry_run:
        click.echo(f"Dry run: would ingest from {sources} with limit={limit}")
        return

    results = asyncio.run(controller.run(list(sources), limit=limit))

    for source, result in results.items():
        click.echo(f"{source}: {result.status} - {result.downloaded} downloaded")

@cli.command()
def status():
    """Show ingestion status for all sources."""
    state_dir = Path("data/state")
    for state_file in state_dir.glob("*.json"):
        state = IngestionState.load(state_file.stem)
        click.echo(f"{state.source}: {len(state.completed_wells)} done, "
                   f"{len(state.failed_wells)} failed, "
                   f"{len(state.pending_wells)} pending")

if __name__ == "__main__":
    cli()
```

## Storage & Compression

### zstd Integration

```python
import zstandard as zstd

class StorageManager:
    """Handles file storage with zstd compression."""

    COMPRESSION_LEVEL = 3  # Balance speed/ratio

    def __init__(self, base_dir: Path = Path("data/raw")):
        self.base_dir = base_dir
        self.compressor = zstd.ZstdCompressor(level=self.COMPRESSION_LEVEL)

    def store(self, job: DownloadJob, content: bytes, target: Path) -> ManifestEntry:
        """Store content with compression and create manifest entry."""
        # Ensure directory exists
        target.parent.mkdir(parents=True, exist_ok=True)

        # Compress and write
        compressed = self.compressor.compress(content)
        target.write_bytes(compressed)

        # Compute checksum
        sha256 = hashlib.sha256(content).hexdigest()

        # Create manifest entry
        return ManifestEntry(
            well_id=job.well_id,
            source_url=job.url,
            local_path=str(target),
            sha256=sha256,
            size_bytes=len(content),
            compressed_size=len(compressed),
            downloaded_at=datetime.utcnow().isoformat(),
            metadata=job.metadata
        )
```

### Manifest Format

```json
{
  "source": "usgs",
  "last_updated": "2026-01-31T10:00:00Z",
  "total_files": 48,
  "total_bytes": 125000000,
  "compressed_bytes": 95000000,
  "entries": [
    {
      "well_id": "TX-1234",
      "source_url": "https://my.usgs.gov/...",
      "local_path": "data/raw/usgs/TX/Permian_Well_TX1234.pdf.zst",
      "sha256": "abc123...",
      "size_bytes": 2400000,
      "compressed_size": 1800000,
      "downloaded_at": "2026-01-31T10:05:00Z",
      "metadata": {
        "state": "TX",
        "library_number": "12345",
        "well_name": "Permian Well"
      }
    }
  ]
}
```

## Resilience

### Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

TRANSIENT_ERRORS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.ReadError,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type(TRANSIENT_ERRORS),
)
async def download_with_retry(url: str, timeout: float = 30.0) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
```

### Circuit Breaker

```python
class CircuitBreaker:
    """Fail-fast when a source is consistently failing."""

    FAILURE_THRESHOLD = 5
    RESET_TIMEOUT = 300  # seconds

    def __init__(self, source: str):
        self.source = source
        self.failures = 0
        self.state = "closed"
        self.last_failure = None

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.FAILURE_THRESHOLD:
            self.state = "open"

    def can_proceed(self) -> bool:
        if self.state == "closed":
            return True
        if self.state == "open":
            if time.time() - self.last_failure > self.RESET_TIMEOUT:
                self.state = "half-open"
                return True
            return False
        return True
```

### Checkpoint & Resume

```python
@dataclass
class IngestionState:
    source: str
    started_at: str
    completed_wells: list[str]
    failed_wells: dict[str, str]
    pending_wells: list[str]

    def save(self):
        path = Path(f"data/state/{self.source}.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))

    @classmethod
    def load(cls, source: str) -> "IngestionState | None":
        path = Path(f"data/state/{source}.json")
        if path.exists():
            return cls(**json.loads(path.read_text()))
        return None

    def should_download(self, well_id: str) -> bool:
        return well_id not in self.completed_wells
```

## Testing

### Unit Tests

```python
# tests/ingestion/test_core.py
class TestDownloadJob:
    def test_checksum_verification_passes(self): ...
    def test_checksum_verification_fails_triggers_retry(self): ...
    def test_zstd_compression_applied(self): ...
    def test_manifest_entry_created(self): ...

class TestSourceModule:
    def test_rate_limiting_respected(self): ...
    def test_max_documents_enforced(self): ...
    def test_resume_from_checkpoint(self): ...

# tests/ingestion/test_usgs.py
class TestUSGSModule:
    def test_well_catalog_parsing(self, mock_response): ...
    def test_library_number_extraction(self, mock_response): ...
    def test_download_all_zip_handling(self, mock_response): ...
    def test_graceful_404_handling(self, mock_response): ...
```

### Integration Tests

```python
# tests/ingestion/test_integration.py
class TestPipelineIntegration:
    def test_full_pipeline_downloads_and_compresses(self, mock_usgs_server):
        result = run_ingestion("usgs", limit=3)
        assert result.downloaded == 3
        assert all(f.endswith('.zst') for f in result.files)
        assert Path("data/raw/usgs/manifest.json").exists()

    def test_resume_skips_completed(self, mock_usgs_server, partial_state):
        result = run_ingestion("usgs", limit=5, resume=True)
        assert result.skipped == 2
        assert result.downloaded == 3
```

### Smoke Test

```bash
# Verify connectivity with limit=1
python -m src.ingestion ingest usgs --limit 1 --dry-run
python -m src.ingestion ingest usgs --limit 1

# Verify output
ls -la data/raw/usgs/
cat data/raw/usgs/manifest.json
```

## Next Steps

- [ ] Set up `src/ingestion/` directory structure
- [ ] Implement base classes in `core.py`
- [ ] Implement storage manager with zstd compression
- [ ] Implement USGS module with catalog parsing
- [ ] Add CLI with Click
- [ ] Write unit tests for core components
- [ ] Write integration tests with mocked HTTP
- [ ] Run smoke test against live USGS
- [ ] Update `.gitignore` with `data/raw/`
- [ ] Add dependencies to `pyproject.toml`
