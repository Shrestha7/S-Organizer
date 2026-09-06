"""Tests for core file operations."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.core.file_operations import (
    ConflictResolution,
    FileAction,
    FileOperation,
    execute_copy,
    execute_delete,
    execute_move,
    execute_rename,
    format_destination,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_file(temp_dir):
    """Create a test file."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("Hello, World!")
    return file_path


class TestFileOperations:
    """Tests for file operations."""

    def test_execute_move(self, temp_dir, test_file):
        """Test moving a file."""
        dest = temp_dir / "moved.txt"
        op = FileOperation(
            source=test_file,
            action=FileAction.MOVE,
            destination=dest,
        )

        result = execute_move(op)

        assert result.success is True
        assert dest.exists()
        assert not test_file.exists()

    def test_execute_copy(self, temp_dir, test_file):
        """Test copying a file."""
        dest = temp_dir / "copied.txt"
        op = FileOperation(
            source=test_file,
            action=FileAction.COPY,
            destination=dest,
        )

        result = execute_copy(op)

        assert result.success is True
        assert dest.exists()
        assert test_file.exists()

    def test_execute_rename(self, temp_dir, test_file):
        """Test renaming a file."""
        op = FileOperation(
            source=test_file,
            action=FileAction.RENAME,
            new_name="renamed.txt",
        )

        result = execute_rename(op)

        assert result.success is True
        assert (temp_dir / "renamed.txt").exists()
        assert not test_file.exists()

    def test_execute_delete(self, temp_dir, test_file):
        """Test deleting a file (moves to trash)."""
        op = FileOperation(
            source=test_file,
            action=FileAction.DELETE,
        )

        result = execute_delete(op)

        assert result.success is True
        assert not test_file.exists()

    def test_conflict_resolution_rename(self, temp_dir, test_file):
        """Test conflict resolution with rename."""
        existing = temp_dir / "existing.txt"
        existing.write_text("Existing content")

        dest = temp_dir / "existing.txt"
        op = FileOperation(
            source=test_file,
            action=FileAction.MOVE,
            destination=dest,
            conflict_resolution=ConflictResolution.RENAME,
        )

        result = execute_move(op)

        assert result.success is True
        assert (temp_dir / "existing.txt").exists()
        assert result.destination.name == "existing_1.txt"


class TestFormatDestination:
    """Tests for destination formatting."""

    def test_basic_formatting(self, temp_dir):
        """Test basic placeholder formatting."""
        file_path = temp_dir / "document.pdf"
        file_path.touch()

        result = format_destination("~/Documents/{name}{extension}", file_path)

        assert result == "~/Documents/document.pdf"

    def test_extension_formatting(self, temp_dir):
        """Test extension placeholder."""
        file_path = temp_dir / "image.jpg"
        file_path.touch()

        result = format_destination("~/Pictures/{ext}/{name}.{ext}", file_path)

        assert result == "~/Pictures/jpg/image.jpg"

    def test_date_formatting(self, temp_dir):
        """Test date placeholder."""
        file_path = temp_dir / "report.pdf"
        file_path.touch()

        result = format_destination("~/Documents/{date}_{name}{extension}", file_path)

        assert "Documents" in result
        assert "report.pdf" in result
