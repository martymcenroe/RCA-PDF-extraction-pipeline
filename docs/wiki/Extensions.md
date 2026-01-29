# Extensions

Beyond the core assignment requirements, additional tooling was built for development and debugging workflows.

## PDF Elementizer

A general-purpose PDF element extraction toolkit.

### Purpose

- Extract **every** element from a PDF (text, images, lines, rectangles, paths)
- Store in queryable SQLite database
- Enable exploration and debugging of PDF structure

### Architecture

```
src/elementizer/
├── main.py       # CLI interface (click)
├── extractor.py  # PyMuPDF extraction logic
├── database.py   # SQLite storage (8 tables)
├── viewer.py     # Flask web UI
└── models.py     # Data classes
```

### Database Schema

| Table | Records | Description |
|-------|---------|-------------|
| documents | 1 | PDF metadata |
| pages | 253 | Page dimensions, rotation |
| text_blocks | 8,234 | Text with bounding boxes |
| text_spans | 15,891 | Styled text runs |
| images | 468 | Image references + files |
| lines | 12,456 | Vector lines |
| rects | 3,892 | Rectangles |
| paths | 183,665 | Complex vector paths |
| **Total** | **224,706** | |

### CLI Commands

```bash
# Extract PDF to database
python -m src.elementizer.main extract docs/context/init/W20552.pdf \
    --output data/output/extended/

# Search text
python -m src.elementizer.main search data/output/extended/W20552_elements.db "ROUTINE CORE"

# Show page details
python -m src.elementizer.main page data/output/extended/W20552_elements.db 39

# Statistics
python -m src.elementizer.main stats data/output/extended/W20552_elements.db

# Web viewer
python -m src.elementizer.main view data/output/extended/W20552_elements.db \
    --images data/output/extended/W20552_images
```

### Use Cases

| Scenario | Command |
|----------|---------|
| Find all pages with keyword | `search <db> "keyword"` |
| Inspect specific page | `page <db> 39` |
| Understand PDF structure | `stats <db>` |
| Visual exploration | `view <db>` |

## Web Viewer

Interactive browser-based exploration of extracted PDF elements.

### Features

- Browse pages with element counts
- View text blocks with positions
- View extracted images
- Search across all text
- Filter by element type

### Screenshots

**Page List:**
```
Page | Text Blocks | Images | Lines | Rects
-----|-------------|--------|-------|------
  39 |          42 |      0 |   156 |    23
  40 |          38 |      0 |   148 |    21
  ...
```

**Page Detail:**
```
Page 39: SUMMARY OF ROUTINE CORE ANALYSES

Text Blocks:
[1] (72, 89) - (540, 102): "SUMMARY OF ROUTINE CORE ANALYSES RESULTS"
[2] (72, 115) - (320, 125): "Vacuum Oven Dried at 180° F"
...
```

### Running the Viewer

```bash
# Start viewer on port 5000
python -m src.elementizer.main view data/output/extended/W20552_elements.db \
    --images data/output/extended/W20552_images

# Custom port
python -m src.elementizer.main view data/output/extended/W20552_elements.db \
    --images data/output/extended/W20552_images --port 8080
```

Then open http://127.0.0.1:5000 in browser.

**Note:** The viewer is cross-platform (Windows, macOS, Linux).

### Routes

| Route | Description |
|-------|-------------|
| `/` | Home with stats |
| `/pages` | Page list with element counts |
| `/page/<n>` | Page detail view |
| `/images` | Image gallery |
| `/search?q=<term>` | Text search |

## Database-Backed Extractor

Alternative extraction pipeline using the elementizer database.

### Why Use It?

| Benefit | Description |
|---------|-------------|
| Fast repeated queries | 56 ms vs 359 ms |
| Debuggable | Inspect intermediate state |
| Explorable | Use viewer to understand structure |
| Modifiable | Change extraction logic without re-parsing PDF |

### Usage

```bash
# Step 1: Extract to database (one-time)
python -m src.elementizer.main extract docs/context/init/W20552.pdf \
    --output data/output/extended/

# Step 2: Run extraction
python src/core_analysis.py data/output/extended/W20552_elements.db \
    --output data/output/extended/
```

### Code Structure

```python
class CoreAnalysisExtractor:
    """Database-backed extractor."""

    def extract(self) -> ExtractionResult:
        # 1. Classify pages using text search
        classifications = self._classify_pages(conn)

        # 2. Extract data from table pages
        for page_num in table_pages:
            samples = self._extract_page_data(conn, page_num)

        return result
```

## Comparison: Minimal vs Extended

| Aspect | Minimal | Extended |
|--------|---------|----------|
| Files | 1 | 6 |
| Dependencies | 1 | 3 |
| First run | 359 ms | 6.7 s |
| Subsequent | 359 ms | 56 ms |
| Debuggable | No | Yes |
| Visual exploration | No | Yes |
| Best for | Grading, CI/CD | Development |

## Future Extensions

| Extension | Effort | Value |
|-----------|--------|-------|
| OCR fallback for scanned pages | Medium | High for mixed docs |
| REST API wrapper | Low | High for integration |
| Batch processing CLI | Low | Medium |
| Export to Excel | Low | Medium |
| Confidence scoring | Medium | Medium |
| Unit tests | Medium | High for maintenance |
