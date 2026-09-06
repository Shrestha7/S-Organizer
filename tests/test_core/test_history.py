"""Tests for history module."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.file_operations import FileAction, FileOperation
from src.core.history import History


@pytest.fixture
def history():
    """Create a temporary history manager."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = History()
        manager.set_save_path(Path(tmpdir) / "history.json")
        yield manager


def _make_operation(
    action: FileAction = FileAction.MOVE,
    source: str = "/path/to/file.txt",
    destination: str | None = "/new/path/file.txt",
    rule_name: str = "",
    success: bool = True,
) -> FileOperation:
    """Create a test file operation."""
    op = FileOperation(
        action=action,
        source=Path(source),
        destination=Path(destination) if destination else None,
        rule_name=rule_name,
    )
    op.success = success
    return op


def test_add_entry(history):
    """Test adding a history entry."""
    op = _make_operation(action=FileAction.MOVE)
    history.add(op)
    assert len(history.entries) == 1
    assert history.entries[0].operation.action == FileAction.MOVE


def test_add_entry_with_metadata(history):
    """Test adding entry with metadata."""
    op = _make_operation(
        action=FileAction.COPY,
        rule_name="Test Rule",
    )
    history.add(op)
    assert history.entries[0].operation.rule_name == "Test Rule"


def test_get_stats(history):
    """Test history statistics."""
    history.add(_make_operation(action=FileAction.MOVE))
    history.add(_make_operation(action=FileAction.DELETE))
    stats = history.stats
    assert stats["total"] == 2
    assert stats["successful"] == 2


def test_export_json(history):
    """Test exporting history to JSON."""
    history.add(_make_operation(action=FileAction.MOVE))
    export_path = Path(tempfile.mktemp(suffix=".json"))
    history.export_json(export_path)
    with open(export_path) as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["action"] == "move"
    export_path.unlink()


def test_save_and_load(history):
    """Test saving and loading history."""
    history.add(_make_operation(action=FileAction.MOVE))
    # Auto-save happens on add

    # Load from file
    loaded = History()
    loaded.load(history._save_path)
    assert len(loaded.entries) == 1
    assert loaded.entries[0].operation.action == FileAction.MOVE


def test_load_nonexistent_file():
    """Test loading from nonexistent file."""
    manager = History()
    count = manager.load(Path("/nonexistent/history.json"))
    assert count == 0


def test_undo_last():
    """Test undoing last operation with real file move."""
    with tempfile.TemporaryDirectory() as tmpdir:
        history = History()

        # Create real file
        src = Path(tmpdir) / "file.txt"
        src.write_text("test content")
        dest = Path(tmpdir) / "moved_file.txt"

        # Actually move the file
        import shutil
        shutil.move(str(src), str(dest))

        # Record the operation as successful
        op = FileOperation(
            action=FileAction.MOVE,
            source=src,
            destination=dest,
        )
        op.success = True
        history.add(op)

        # Verify dest exists and source doesn't
        assert dest.exists()
        assert not src.exists()

        # Undo should move the file back to original source path
        undone = history.undo_last()
        assert len(undone) == 1
        assert undone[0].operation.action == FileAction.MOVE

        # File should be back at original source path
        assert src.exists()
        assert not dest.exists()
