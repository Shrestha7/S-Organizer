"""Tests for duplicate detector."""

import tempfile
from pathlib import Path

import pytest

from src.core.duplicate_detector import (
    calculate_file_hash,
    find_duplicates,
    find_duplicates_in_folder,
    get_duplicate_stats,
)


@pytest.fixture
def test_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create identical files
        file1 = tmpdir_path / "file1.txt"
        file2 = tmpdir_path / "file2.txt"
        file1.write_text("Hello, World!")
        file2.write_text("Hello, World!")

        # Create different file
        file3 = tmpdir_path / "file3.txt"
        file3.write_text("Different content")

        yield tmpdir_path


def test_calculate_file_hash(test_dir):
    """Test file hash calculation."""
    hash1 = calculate_file_hash(test_dir / "file1.txt")
    hash2 = calculate_file_hash(test_dir / "file2.txt")
    hash3 = calculate_file_hash(test_dir / "file3.txt")

    assert hash1 == hash2  # Identical files should have same hash
    assert hash1 != hash3  # Different files should have different hashes


def test_find_duplicates(test_dir):
    """Test finding duplicate files."""
    duplicates = find_duplicates([test_dir])
    assert len(duplicates) == 1
    assert len(duplicates[0].files) == 2


def test_find_no_duplicates():
    """Test when no duplicates exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        (tmpdir_path / "file1.txt").write_text("Content A")
        (tmpdir_path / "file2.txt").write_text("Content B")

        duplicates = find_duplicates([tmpdir_path])
        assert len(duplicates) == 0


def test_get_duplicate_stats(test_dir):
    """Test duplicate statistics."""
    duplicates = find_duplicates([test_dir])
    stats = get_duplicate_stats(duplicates)

    assert stats["groups"] == 1
    assert stats["files"] == 2
    assert stats["wasted_bytes"] > 0
    assert stats["wasted_mb"] >= 0


def test_empty_input():
    """Test with empty input."""
    duplicates = find_duplicates([])
    assert len(duplicates) == 0
    stats = get_duplicate_stats([])
    assert stats["groups"] == 0


def test_find_duplicates_in_folder(test_dir):
    """Test finding duplicates in a single folder."""
    duplicates = find_duplicates_in_folder(test_dir)
    assert len(duplicates) == 1
