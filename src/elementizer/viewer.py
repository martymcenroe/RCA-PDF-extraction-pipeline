"""Web viewer for exploring extracted PDF elements."""

import json
import sqlite3
from pathlib import Path

from flask import Flask, render_template_string, request, send_from_directory, g

app = Flask(__name__)

# Configuration - set via environment or command line
DATABASE_PATH = None
IMAGES_DIR = None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PDF Element Viewer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #eee; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        h1, h2, h3 { margin-bottom: 15px; }
        h1 { color: #00d4ff; }
        a { color: #00d4ff; text-decoration: none; }
        a:hover { text-decoration: underline; }

        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .stat-card { background: #16213e; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-card .number { font-size: 2em; color: #00d4ff; font-weight: bold; }
        .stat-card .label { color: #888; font-size: 0.9em; }

        .search-box { margin-bottom: 30px; }
        .search-box input { width: 100%; padding: 12px; font-size: 16px; border: none; border-radius: 8px; background: #16213e; color: #fff; }
        .search-box input::placeholder { color: #666; }

        .page-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); gap: 10px; margin-bottom: 30px; }
        .page-card { background: #16213e; padding: 15px; border-radius: 8px; text-align: center; transition: transform 0.2s; }
        .page-card:hover { transform: scale(1.05); background: #1f3460; }
        .page-card .page-num { font-size: 1.5em; color: #00d4ff; }
        .page-card .count { font-size: 0.8em; color: #888; }

        .element-list { background: #16213e; border-radius: 8px; overflow: hidden; }
        .element-item { padding: 15px; border-bottom: 1px solid #0f3460; }
        .element-item:last-child { border-bottom: none; }
        .element-item:hover { background: #1f3460; }
        .element-type { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; margin-right: 10px; }
        .type-text { background: #2ecc71; color: #000; }
        .type-image { background: #e74c3c; color: #fff; }
        .type-line { background: #3498db; color: #fff; }
        .type-rect { background: #9b59b6; color: #fff; }
        .type-path { background: #f39c12; color: #000; }

        .text-content { font-family: monospace; background: #0a0a15; padding: 10px; border-radius: 4px; margin-top: 10px; white-space: pre-wrap; word-break: break-word; max-height: 200px; overflow-y: auto; }
        .position { color: #666; font-size: 0.8em; }
        .font-info { color: #888; font-size: 0.85em; }

        .image-preview { max-width: 300px; max-height: 200px; margin-top: 10px; border-radius: 4px; }
        .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .image-card { background: #16213e; padding: 10px; border-radius: 8px; text-align: center; }
        .image-card img { max-width: 100%; max-height: 150px; border-radius: 4px; }
        .image-card .meta { font-size: 0.8em; color: #888; margin-top: 5px; }

        .nav { margin-bottom: 20px; padding: 10px; background: #16213e; border-radius: 8px; }
        .nav a { margin-right: 20px; }

        .search-results { margin-top: 20px; }
        .search-result { padding: 15px; background: #16213e; margin-bottom: 10px; border-radius: 8px; }
        .search-result .page-link { color: #00d4ff; font-weight: bold; }
        .search-result .context { margin-top: 5px; }
        .highlight { background: #f39c12; color: #000; padding: 0 2px; }

        .pagination { margin-top: 20px; text-align: center; }
        .pagination a { display: inline-block; padding: 8px 15px; margin: 0 5px; background: #16213e; border-radius: 4px; }
        .pagination a.active { background: #00d4ff; color: #000; }

        .back-link { display: inline-block; margin-bottom: 20px; padding: 8px 15px; background: #16213e; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

HOME_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", """
<h1>PDF Element Viewer</h1>

<div class="nav">
    <a href="/">Home</a>
    <a href="/pages">All Pages</a>
    <a href="/images">All Images</a>
    <a href="/search">Search</a>
</div>

<h2>Document: {{ doc.file_path | basename }}</h2>

<div class="stats-grid">
    <div class="stat-card">
        <div class="number">{{ stats.pages }}</div>
        <div class="label">Pages</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ stats.text_blocks }}</div>
        <div class="label">Text Blocks</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ stats.text_spans }}</div>
        <div class="label">Text Spans</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ stats.images }}</div>
        <div class="label">Images</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ stats.lines }}</div>
        <div class="label">Lines</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ stats.rects }}</div>
        <div class="label">Rectangles</div>
    </div>
</div>

<div class="search-box">
    <form action="/search" method="get">
        <input type="text" name="q" placeholder="Search text content..." autofocus>
    </form>
</div>

<h2>Pages with Content</h2>
<div class="page-grid">
    {% for page in pages %}
    <a href="/page/{{ page.page_number }}" class="page-card">
        <div class="page-num">{{ page.page_number }}</div>
        <div class="count">{{ page.element_count }} elements</div>
    </a>
    {% endfor %}
</div>
""")

PAGES_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", """
<a href="/" class="back-link">&larr; Back to Home</a>
<h1>All Pages</h1>

<div class="nav">
    <a href="/">Home</a>
    <a href="/pages">All Pages</a>
    <a href="/images">All Images</a>
    <a href="/search">Search</a>
</div>

<div class="page-grid">
    {% for page in pages %}
    <a href="/page/{{ page.page_number }}" class="page-card">
        <div class="page-num">{{ page.page_number }}</div>
        <div class="count">{{ page.width|int }}x{{ page.height|int }}</div>
    </a>
    {% endfor %}
</div>
""")

PAGE_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", """
<a href="/" class="back-link">&larr; Back to Home</a>
<h1>Page {{ page_number }}</h1>

<div class="nav">
    {% if page_number > 1 %}<a href="/page/{{ page_number - 1 }}">&larr; Prev</a>{% endif %}
    <a href="/">Home</a>
    <a href="/pages">All Pages</a>
    {% if page_number < total_pages %}<a href="/page/{{ page_number + 1 }}">Next &rarr;</a>{% endif %}
</div>

<div class="stats-grid">
    <div class="stat-card">
        <div class="number">{{ page.width|int }}x{{ page.height|int }}</div>
        <div class="label">Dimensions</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ text_blocks|length }}</div>
        <div class="label">Text Blocks</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ images|length }}</div>
        <div class="label">Images</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ lines|length }}</div>
        <div class="label">Lines</div>
    </div>
    <div class="stat-card">
        <div class="number">{{ rects|length }}</div>
        <div class="label">Rects</div>
    </div>
</div>

{% if images %}
<h2>Images</h2>
<div class="image-grid">
    {% for img in images %}
    <div class="image-card">
        {% if img.file_path %}
        <a href="/image/{{ img.file_path | basename }}" target="_blank">
            <img src="/image/{{ img.file_path | basename }}" alt="Image">
        </a>
        {% endif %}
        <div class="meta">{{ img.width }}x{{ img.height }} {{ img.format }}</div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if text_blocks %}
<h2>Text Blocks</h2>
<div class="element-list">
    {% for block in text_blocks %}
    <div class="element-item">
        <span class="element-type type-text">TEXT</span>
        <span class="position">({{ block.x0|int }}, {{ block.y0|int }}) - ({{ block.x1|int }}, {{ block.y1|int }})</span>
        <div class="text-content">{{ block.full_text }}</div>
    </div>
    {% endfor %}
</div>
{% endif %}

{% if lines and lines|length <= 100 %}
<h2>Lines ({{ lines|length }})</h2>
<div class="element-list">
    {% for line in lines[:50] %}
    <div class="element-item">
        <span class="element-type type-line">LINE</span>
        <span class="position">({{ line.start_x|int }}, {{ line.start_y|int }}) &rarr; ({{ line.end_x|int }}, {{ line.end_y|int }})</span>
        {% if line.is_horizontal %}<span class="font-info">horizontal</span>{% endif %}
        {% if line.is_vertical %}<span class="font-info">vertical</span>{% endif %}
    </div>
    {% endfor %}
    {% if lines|length > 50 %}<div class="element-item">... and {{ lines|length - 50 }} more lines</div>{% endif %}
</div>
{% elif lines %}
<h2>Lines: {{ lines|length }} (too many to display)</h2>
{% endif %}
""")

IMAGES_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", """
<a href="/" class="back-link">&larr; Back to Home</a>
<h1>All Images ({{ images|length }})</h1>

<div class="nav">
    <a href="/">Home</a>
    <a href="/pages">All Pages</a>
    <a href="/images">All Images</a>
    <a href="/search">Search</a>
</div>

<div class="image-grid">
    {% for img in images %}
    <div class="image-card">
        {% if img.file_path %}
        <a href="/image/{{ img.file_path | basename }}" target="_blank">
            <img src="/image/{{ img.file_path | basename }}" alt="Image">
        </a>
        {% endif %}
        <div class="meta">Page {{ img.page_number }} - {{ img.width }}x{{ img.height }}</div>
    </div>
    {% endfor %}
</div>

<div class="pagination">
    {% if offset > 0 %}
    <a href="/images?offset={{ offset - limit }}">&larr; Prev</a>
    {% endif %}
    <span>Showing {{ offset + 1 }}-{{ offset + images|length }} of {{ total }}</span>
    {% if offset + limit < total %}
    <a href="/images?offset={{ offset + limit }}">Next &rarr;</a>
    {% endif %}
</div>
""")

SEARCH_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", """
<a href="/" class="back-link">&larr; Back to Home</a>
<h1>Search</h1>

<div class="nav">
    <a href="/">Home</a>
    <a href="/pages">All Pages</a>
    <a href="/images">All Images</a>
    <a href="/search">Search</a>
</div>

<div class="search-box">
    <form action="/search" method="get">
        <input type="text" name="q" placeholder="Search text content..." value="{{ query }}" autofocus>
    </form>
</div>

{% if query %}
<h2>Results for "{{ query }}" ({{ results|length }}{% if results|length >= 100 %}+{% endif %})</h2>

<div class="search-results">
    {% for result in results %}
    <div class="search-result">
        <a href="/page/{{ result.page_number }}" class="page-link">Page {{ result.page_number }}</a>
        <span class="font-info">{{ result.font_name }} {{ result.font_size|round(1) }}pt</span>
        <div class="context">{{ result.text }}</div>
    </div>
    {% endfor %}
</div>
{% endif %}
""")


def get_db():
    """Get database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.template_filter('basename')
def basename_filter(path):
    return Path(path).name if path else ''


@app.route('/')
def home():
    db = get_db()

    # Get document info
    doc = db.execute("SELECT * FROM documents LIMIT 1").fetchone()

    # Get stats
    stats = {}
    for table in ['pages', 'text_blocks', 'text_spans', 'images', 'lines', 'rects']:
        stats[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

    # Get pages with element counts
    pages = db.execute("""
        SELECT page_number, element_count FROM (
            SELECT p.page_number,
                   (SELECT COUNT(*) FROM text_blocks WHERE page_id = p.id) +
                   (SELECT COUNT(*) FROM images WHERE page_id = p.id) +
                   (SELECT COUNT(*) FROM lines WHERE page_id = p.id) +
                   (SELECT COUNT(*) FROM rects WHERE page_id = p.id) as element_count
            FROM pages p
        ) WHERE element_count > 0
        ORDER BY page_number
    """).fetchall()

    return render_template_string(HOME_TEMPLATE, doc=doc, stats=stats, pages=pages)


@app.route('/pages')
def pages():
    db = get_db()
    pages = db.execute("SELECT * FROM pages ORDER BY page_number").fetchall()
    return render_template_string(PAGES_TEMPLATE, pages=pages)


@app.route('/page/<int:page_number>')
def page(page_number):
    db = get_db()

    # Get page
    page = db.execute(
        "SELECT * FROM pages WHERE page_number = ?", (page_number,)
    ).fetchone()

    if not page:
        return "Page not found", 404

    page_id = page['id']
    total_pages = db.execute("SELECT COUNT(*) FROM pages").fetchone()[0]

    # Get elements
    text_blocks = db.execute(
        "SELECT * FROM text_blocks WHERE page_id = ? ORDER BY y0, x0", (page_id,)
    ).fetchall()

    images = db.execute(
        "SELECT * FROM images WHERE page_id = ?", (page_id,)
    ).fetchall()

    lines = db.execute(
        "SELECT * FROM lines WHERE page_id = ?", (page_id,)
    ).fetchall()

    rects = db.execute(
        "SELECT * FROM rects WHERE page_id = ?", (page_id,)
    ).fetchall()

    return render_template_string(
        PAGE_TEMPLATE,
        page=page,
        page_number=page_number,
        total_pages=total_pages,
        text_blocks=text_blocks,
        images=images,
        lines=lines,
        rects=rects,
    )


@app.route('/images')
def images():
    db = get_db()

    limit = 50
    offset = int(request.args.get('offset', 0))

    total = db.execute("SELECT COUNT(*) FROM images").fetchone()[0]

    images = db.execute("""
        SELECT i.*, p.page_number
        FROM images i
        JOIN pages p ON i.page_id = p.id
        ORDER BY p.page_number, i.id
        LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()

    return render_template_string(
        IMAGES_TEMPLATE,
        images=images,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.route('/image/<filename>')
def serve_image(filename):
    if IMAGES_DIR:
        return send_from_directory(IMAGES_DIR, filename)
    return "Images directory not configured", 404


@app.route('/search')
def search():
    db = get_db()
    query = request.args.get('q', '')

    results = []
    if query:
        results = db.execute("""
            SELECT ts.*, p.page_number
            FROM text_spans ts
            JOIN pages p ON ts.page_id = p.id
            WHERE ts.text LIKE ?
            ORDER BY p.page_number, ts.y0, ts.x0
            LIMIT 100
        """, (f"%{query}%",)).fetchall()

    return render_template_string(SEARCH_TEMPLATE, query=query, results=results)


def run_viewer(db_path: str, images_dir: str = None, host: str = '127.0.0.1', port: int = 5000):
    """Run the viewer server."""
    global DATABASE_PATH, IMAGES_DIR
    DATABASE_PATH = db_path
    IMAGES_DIR = images_dir

    print(f"\n{'='*50}")
    print("PDF Element Viewer")
    print(f"{'='*50}")
    print(f"Database: {db_path}")
    if images_dir:
        print(f"Images: {images_dir}")
    print(f"\nOpen in browser: http://{host}:{port}")
    print(f"{'='*50}\n")

    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python viewer.py <database.db> [images_dir]")
        sys.exit(1)

    db_path = sys.argv[1]
    images_dir = sys.argv[2] if len(sys.argv) > 2 else None
    run_viewer(db_path, images_dir)
