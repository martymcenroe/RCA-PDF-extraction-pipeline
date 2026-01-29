"""SQLite database storage for PDF elements."""

import json
import sqlite3
from pathlib import Path
from typing import Optional

from .models import DocumentElements, PageElements


class ElementDatabase:
    """SQLite storage for extracted PDF elements."""

    SCHEMA = """
    -- Document metadata
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL,
        page_count INTEGER,
        title TEXT,
        author TEXT,
        creator TEXT,
        producer TEXT,
        creation_date TEXT,
        modification_date TEXT,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- Pages
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        width REAL,
        height REAL,
        rotation INTEGER DEFAULT 0,
        FOREIGN KEY (document_id) REFERENCES documents(id),
        UNIQUE(document_id, page_number)
    );

    -- Text blocks
    CREATE TABLE IF NOT EXISTS text_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL,
        x0 REAL, y0 REAL, x1 REAL, y1 REAL,
        full_text TEXT,
        line_count INTEGER,
        structure_json TEXT,
        FOREIGN KEY (page_id) REFERENCES pages(id)
    );

    -- Text spans (individual text runs with formatting)
    CREATE TABLE IF NOT EXISTS text_spans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL,
        block_index INTEGER,
        line_index INTEGER,
        span_index INTEGER,
        x0 REAL, y0 REAL, x1 REAL, y1 REAL,
        text TEXT,
        font_name TEXT,
        font_size REAL,
        color INTEGER,
        flags INTEGER DEFAULT 0,
        FOREIGN KEY (page_id) REFERENCES pages(id)
    );

    -- Images
    CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL,
        xref INTEGER,
        x0 REAL, y0 REAL, x1 REAL, y1 REAL,
        width INTEGER,
        height INTEGER,
        colorspace TEXT,
        bpc INTEGER,
        format TEXT,
        file_path TEXT,
        image_data BLOB,
        FOREIGN KEY (page_id) REFERENCES pages(id)
    );

    -- Lines (vector)
    CREATE TABLE IF NOT EXISTS lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL,
        start_x REAL, start_y REAL,
        end_x REAL, end_y REAL,
        width REAL DEFAULT 1.0,
        color_json TEXT,
        stroke_opacity REAL DEFAULT 1.0,
        is_horizontal BOOLEAN,
        is_vertical BOOLEAN,
        FOREIGN KEY (page_id) REFERENCES pages(id)
    );

    -- Rectangles
    CREATE TABLE IF NOT EXISTS rects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL,
        x0 REAL, y0 REAL, x1 REAL, y1 REAL,
        fill_color_json TEXT,
        stroke_color_json TEXT,
        stroke_width REAL DEFAULT 1.0,
        fill_opacity REAL DEFAULT 1.0,
        stroke_opacity REAL DEFAULT 1.0,
        FOREIGN KEY (page_id) REFERENCES pages(id)
    );

    -- Paths (complex curves)
    CREATE TABLE IF NOT EXISTS paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER NOT NULL,
        x0 REAL, y0 REAL, x1 REAL, y1 REAL,
        items_json TEXT,
        fill_color_json TEXT,
        stroke_color_json TEXT,
        FOREIGN KEY (page_id) REFERENCES pages(id)
    );

    -- Indexes for common queries
    CREATE INDEX IF NOT EXISTS idx_pages_document ON pages(document_id);
    CREATE INDEX IF NOT EXISTS idx_text_blocks_page ON text_blocks(page_id);
    CREATE INDEX IF NOT EXISTS idx_text_spans_page ON text_spans(page_id);
    CREATE INDEX IF NOT EXISTS idx_images_page ON images(page_id);
    CREATE INDEX IF NOT EXISTS idx_lines_page ON lines(page_id);
    CREATE INDEX IF NOT EXISTS idx_rects_page ON rects(page_id);
    CREATE INDEX IF NOT EXISTS idx_paths_page ON paths(page_id);
    """

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def __enter__(self):
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_schema()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            self._conn.close()

    def _create_schema(self):
        """Create database schema."""
        self._conn.executescript(self.SCHEMA)
        self._conn.commit()

    def store_document(self, doc_elements: DocumentElements, store_image_data: bool = False) -> int:
        """Store all document elements in the database."""
        cursor = self._conn.cursor()

        # Insert document
        meta = doc_elements.metadata
        cursor.execute("""
            INSERT INTO documents (
                file_path, page_count, title, author, creator, producer,
                creation_date, modification_date, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_elements.file_path,
            doc_elements.page_count,
            meta.get("title"),
            meta.get("author"),
            meta.get("creator"),
            meta.get("producer"),
            meta.get("creation_date"),
            meta.get("modification_date"),
            json.dumps(meta),
        ))
        document_id = cursor.lastrowid

        # Insert pages and elements
        for page_elements in doc_elements.pages:
            page_id = self._store_page(cursor, document_id, page_elements, store_image_data)

        self._conn.commit()
        return document_id

    def _store_page(
        self,
        cursor: sqlite3.Cursor,
        document_id: int,
        page: PageElements,
        store_image_data: bool,
    ) -> int:
        """Store a page and all its elements."""
        # Insert page
        cursor.execute("""
            INSERT INTO pages (document_id, page_number, width, height, rotation)
            VALUES (?, ?, ?, ?, ?)
        """, (document_id, page.page_number, page.width, page.height, page.rotation))
        page_id = cursor.lastrowid

        # Insert text blocks
        for block_idx, block in enumerate(page.text_blocks):
            cursor.execute("""
                INSERT INTO text_blocks (page_id, x0, y0, x1, y1, full_text, line_count, structure_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page_id,
                block.bbox.x0, block.bbox.y0, block.bbox.x1, block.bbox.y1,
                block.text,
                len(block.lines),
                json.dumps(block.to_dict()),
            ))

            # Insert individual spans for searchability
            for line_idx, line in enumerate(block.lines):
                for span_idx, span in enumerate(line.spans):
                    cursor.execute("""
                        INSERT INTO text_spans (
                            page_id, block_index, line_index, span_index,
                            x0, y0, x1, y1, text, font_name, font_size, color, flags
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        page_id, block_idx, line_idx, span_idx,
                        span.bbox.x0, span.bbox.y0, span.bbox.x1, span.bbox.y1,
                        span.text, span.font_name, span.font_size, span.color, span.flags,
                    ))

        # Insert images
        for img in page.images:
            image_data = img.image_data if store_image_data else None
            cursor.execute("""
                INSERT INTO images (
                    page_id, xref, x0, y0, x1, y1,
                    width, height, colorspace, bpc, format, file_path, image_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page_id, img.xref,
                img.bbox.x0, img.bbox.y0, img.bbox.x1, img.bbox.y1,
                img.width, img.height, img.colorspace, img.bpc,
                img.format, img.file_path, image_data,
            ))

        # Insert lines
        for line in page.lines:
            cursor.execute("""
                INSERT INTO lines (
                    page_id, start_x, start_y, end_x, end_y,
                    width, color_json, stroke_opacity, is_horizontal, is_vertical
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page_id,
                line.start_x, line.start_y, line.end_x, line.end_y,
                line.width, json.dumps(line.color), line.stroke_opacity,
                line.is_horizontal, line.is_vertical,
            ))

        # Insert rectangles
        for rect in page.rects:
            cursor.execute("""
                INSERT INTO rects (
                    page_id, x0, y0, x1, y1,
                    fill_color_json, stroke_color_json, stroke_width,
                    fill_opacity, stroke_opacity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page_id,
                rect.bbox.x0, rect.bbox.y0, rect.bbox.x1, rect.bbox.y1,
                json.dumps(rect.fill_color), json.dumps(rect.stroke_color),
                rect.stroke_width, rect.fill_opacity, rect.stroke_opacity,
            ))

        # Insert paths
        for path in page.paths:
            cursor.execute("""
                INSERT INTO paths (
                    page_id, x0, y0, x1, y1,
                    items_json, fill_color_json, stroke_color_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                page_id,
                path.bbox.x0, path.bbox.y0, path.bbox.x1, path.bbox.y1,
                json.dumps(path.items),
                json.dumps(path.fill_color), json.dumps(path.stroke_color),
            ))

        return page_id

    def get_stats(self) -> dict:
        """Get database statistics."""
        cursor = self._conn.cursor()

        stats = {}
        tables = ["documents", "pages", "text_blocks", "text_spans", "images", "lines", "rects", "paths"]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]

        return stats

    def search_text(self, query: str, document_id: Optional[int] = None) -> list[dict]:
        """Search for text in spans."""
        cursor = self._conn.cursor()

        sql = """
            SELECT ts.*, p.page_number, d.file_path
            FROM text_spans ts
            JOIN pages p ON ts.page_id = p.id
            JOIN documents d ON p.document_id = d.id
            WHERE ts.text LIKE ?
        """
        params = [f"%{query}%"]

        if document_id:
            sql += " AND d.id = ?"
            params.append(document_id)

        sql += " ORDER BY p.page_number, ts.y0, ts.x0"

        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_page_elements(self, document_id: int, page_number: int) -> dict:
        """Get all elements for a specific page."""
        cursor = self._conn.cursor()

        # Get page
        cursor.execute("""
            SELECT * FROM pages WHERE document_id = ? AND page_number = ?
        """, (document_id, page_number))
        page = dict(cursor.fetchone()) if cursor.fetchone() else None

        if not page:
            return {}

        page_id = page["id"]

        # Get all elements
        elements = {"page": page}

        for table in ["text_blocks", "text_spans", "images", "lines", "rects", "paths"]:
            cursor.execute(f"SELECT * FROM {table} WHERE page_id = ?", (page_id,))
            elements[table] = [dict(row) for row in cursor.fetchall()]

        return elements
