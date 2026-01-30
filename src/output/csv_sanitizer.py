"""CSV injection prevention and output utilities."""

import csv
from typing import List


# Characters that trigger formula execution in spreadsheet applications
FORMULA_CHARS = ("=", "+", "-", "@")


def sanitize_csv_value(value: str) -> str:
    """
    Prevent CSV injection by escaping dangerous leading characters.

    Spreadsheet applications (Excel, Google Sheets) interpret cells starting
    with =, +, -, @ as formulas. This can lead to code execution attacks
    when opening untrusted CSV files.

    Args:
        value: The string to sanitize.

    Returns:
        String prefixed with single quote if it starts with formula characters.

    Example:
        >>> sanitize_csv_value("=SUM(A1)")
        "'=SUM(A1)"
        >>> sanitize_csv_value("Normal Header")
        'Normal Header'
        >>> sanitize_csv_value("+1234")
        "'+1234"
    """
    if not value:
        return value

    if value.startswith(FORMULA_CHARS):
        return "'" + value

    return value


def write_csv_with_bom(
    rows: List[List[str]],
    output_path: str,
    headers: List[str],
    sanitize_headers: bool = True,
) -> None:
    """
    Write CSV with UTF-8 BOM for Excel compatibility.

    The UTF-8 BOM (Byte Order Mark) ensures Excel correctly interprets
    the file as UTF-8 encoded, preventing character encoding issues.

    Args:
        rows: Data rows to write.
        output_path: Destination file path.
        headers: Header row.
        sanitize_headers: If True, apply CSV injection protection to headers.
    """
    # Sanitize headers if requested
    safe_headers = headers
    if sanitize_headers:
        safe_headers = [sanitize_csv_value(h) for h in headers]

    # Write with UTF-8 BOM (encoding='utf-8-sig' adds BOM automatically)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(safe_headers)
        writer.writerows(rows)
