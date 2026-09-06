"""File matching logic for rules."""

from __future__ import annotations

import fnmatch
from datetime import datetime
from pathlib import Path

from src.rules.base import RuleMatch


def matches_extensions(file_path: Path, extensions: list[str]) -> bool:
    """Check if file matches any of the specified extensions.

    Args:
        file_path: Path to the file.
        extensions: List of extensions to match (e.g., ['.pdf', '.txt']).

    Returns:
        True if file matches any extension.
    """
    if not extensions:
        return True

    file_ext = file_path.suffix.lower()
    return any(ext.lower() == file_ext for ext in extensions)


def matches_name_pattern(file_path: Path, pattern: str) -> bool:
    """Check if file name matches the given pattern.

    Supports Unix shell-style wildcards:
        * - matches everything
        ? - matches any single character
        [seq] - matches any character in seq
        [!seq] - matches any character not in seq

    Args:
        file_path: Path to the file.
        pattern: Glob pattern to match against.

    Returns:
        True if file name matches pattern.
    """
    if not pattern or pattern == "*":
        return True

    return fnmatch.fnmatch(file_path.name, pattern)


def matches_size(
    file_path: Path,
    min_size: int | None = None,
    max_size: int | None = None,
) -> bool:
    """Check if file size is within specified bounds.

    Args:
        file_path: Path to the file.
        min_size: Minimum size in bytes (inclusive).
        max_size: Maximum size in bytes (inclusive).

    Returns:
        True if file size is within bounds.
    """
    try:
        size = file_path.stat().st_size
    except OSError:
        return False

    if min_size is not None and size < min_size:
        return False

    if max_size is not None and size > max_size:
        return False

    return True


def matches_age(
    file_path: Path,
    min_age_days: int | None = None,
    max_age_days: int | None = None,
) -> bool:
    """Check if file age is within specified bounds.

    Age is based on last modification time.

    Args:
        file_path: Path to the file.
        min_age_days: Minimum age in days (inclusive).
        max_age_days: Maximum age in days (inclusive).

    Returns:
        True if file age is within bounds.
    """
    try:
        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
    except OSError:
        return False

    age_days = (datetime.now() - mtime).days

    if min_age_days is not None and age_days < min_age_days:
        return False

    if max_age_days is not None and age_days > max_age_days:
        return False

    return True


def matches_keywords(file_path: Path, keywords: list[str]) -> bool:
    """Check if file content contains specified keywords.

    Currently supports: PDF, DOCX, TXT, MD, XLSX, CSV, and image EXIF.

    Args:
        file_path: Path to the file.
        keywords: List of keywords to search for (case-insensitive).

    Returns:
        True if file contains any of the keywords.
    """
    if not keywords:
        return True

    suffix = file_path.suffix.lower()

    try:
        if suffix == ".txt" or suffix == ".md":
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        elif suffix == ".pdf":
            content = _extract_pdf_text(file_path)
        elif suffix == ".docx":
            content = _extract_docx_text(file_path)
        elif suffix == ".xlsx":
            content = _extract_xlsx_text(file_path)
        elif suffix == ".csv":
            content = _extract_csv_text(file_path)
        elif suffix in (".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".gif", ".webp"):
            content = _extract_image_exif(file_path)
        else:
            return False
    except Exception:
        return False

    content_lower = content.lower()
    return any(keyword.lower() in content_lower for keyword in keywords)


def _extract_pdf_text(file_path: Path) -> str:
    """Extract text from a PDF file.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Extracted text content.
    """
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(str(file_path))
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return " ".join(text_parts)
    except ImportError:
        return ""
    except Exception:
        return ""


def _extract_docx_text(file_path: Path) -> str:
    """Extract text from a DOCX file.

    Args:
        file_path: Path to the DOCX file.

    Returns:
        Extracted text content.
    """
    try:
        from docx import Document

        doc = Document(str(file_path))
        return " ".join(paragraph.text for paragraph in doc.paragraphs)
    except ImportError:
        return ""
    except Exception:
        return ""


def _extract_xlsx_text(file_path: Path) -> str:
    """Extract text from an XLSX file.

    Args:
        file_path: Path to the XLSX file.

    Returns:
        Extracted text content.
    """
    try:
        from openpyxl import load_workbook

        wb = load_workbook(str(file_path), read_only=True, data_only=True)
        text_parts = []
        for sheet in wb.sheetnames:
            ws = wb[sheet]
            for row in ws.iter_rows(values_only=True):
                for cell in row:
                    if cell is not None:
                        text_parts.append(str(cell))
        wb.close()
        return " ".join(text_parts)
    except ImportError:
        return ""
    except Exception:
        return ""


def _extract_csv_text(file_path: Path) -> str:
    """Extract text from a CSV file.

    Args:
        file_path: Path to the CSV file.

    Returns:
        Extracted text content.
    """
    try:
        import csv

        text_parts = []
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            for row in reader:
                for cell in row:
                    if cell:
                        text_parts.append(cell)
        return " ".join(text_parts)
    except Exception:
        return ""


def _extract_image_exif(file_path: Path) -> str:
    """Extract EXIF metadata from an image file.

    Args:
        file_path: Path to the image file.

    Returns:
        Extracted EXIF text content.
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS

        img = Image.open(file_path)
        exif_data = img.getexif()

        if not exif_data:
            return ""

        text_parts = []
        for tag_id, value in exif_data.items():
            tag_name = TAGS.get(tag_id, str(tag_id))
            if isinstance(value, bytes):
                continue
            text_parts.append(f"{tag_name}: {value}")

        # Also check ImageInfo for XMP data
        if hasattr(img, "info"):
            for key, value in img.info.items():
                if isinstance(value, str) and len(value) > 0:
                    text_parts.append(f"{key}: {value}")

        return " ".join(text_parts)
    except ImportError:
        return ""
    except Exception:
        return ""


def parse_size(size_str: str) -> int:
    """Parse a human-readable size string to bytes.

    Supported formats: '10MB', '1GB', '500KB', '1024B'

    Args:
        size_str: Size string to parse.

    Returns:
        Size in bytes.
    """
    size_str = size_str.strip().upper()

    multipliers = {
        "TB": 1024**4,
        "GB": 1024**3,
        "MB": 1024**2,
        "KB": 1024,
        "B": 1,
    }

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number = size_str[: -len(suffix)].strip()
            return int(float(number) * multiplier)

    return int(size_str)


def match_file(file_path: Path, match_config: RuleMatch) -> bool:
    """Check if a file matches all criteria in a RuleMatch configuration.

    Args:
        file_path: Path to the file to check.
        match_config: Rule match configuration.

    Returns:
        True if file matches all criteria.
    """
    if not file_path.exists() or not file_path.is_file():
        return False

    if not matches_extensions(file_path, match_config.extensions):
        return False

    if not matches_name_pattern(file_path, match_config.name_pattern):
        return False

    if not matches_size(file_path, match_config.min_size, match_config.max_size):
        return False

    if not matches_age(
        file_path, match_config.min_age_days, match_config.max_age_days
    ):
        return False

    if not matches_keywords(file_path, match_config.content_keywords):
        return False

    return True
