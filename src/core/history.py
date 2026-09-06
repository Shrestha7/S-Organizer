"""History tracking and undo support for file operations.

This module logs all file operations and provides undo functionality.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.core.file_operations import (
    FileAction,
    FileOperation,
    execute_operation,
)

logger = logging.getLogger(__name__)


@dataclass
class HistoryEntry:
    """A single history entry representing a file operation."""

    operation: FileOperation
    undone: bool = False
    undone_at: datetime | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "source": str(self.operation.source),
            "destination": str(self.operation.destination) if self.operation.destination else None,
            "action": self.operation.action.value,
            "rule_name": self.operation.rule_name,
            "timestamp": self.operation.timestamp.isoformat(),
            "success": self.operation.success,
            "error": self.operation.error,
            "undone": self.undone,
            "undone_at": self.undone_at.isoformat() if self.undone_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> HistoryEntry:
        """Create from dictionary."""
        op = FileOperation(
            source=Path(data["source"]),
            action=FileAction(data["action"]),
            destination=Path(data["destination"]) if data.get("destination") else None,
            rule_name=data.get("rule_name", ""),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            success=data.get("success", False),
            error=data.get("error"),
        )
        entry = cls(operation=op)
        entry.undone = data.get("undone", False)
        if data.get("undone_at"):
            entry.undone_at = datetime.fromisoformat(data["undone_at"])
        return entry


class History:
    """Manages operation history and provides undo functionality.

    Features:
    - Log all file operations
    - Undo individual operations
    - Export/import history
    - Persistent storage (auto-saves to JSON)
    """

    def __init__(self, max_entries: int = 1000) -> None:
        """Initialize history manager.

        Args:
            max_entries: Maximum number of entries to keep.
        """
        self.entries: list[HistoryEntry] = []
        self.max_entries = max_entries
        self._save_path: Path | None = None

    def set_save_path(self, path: Path) -> None:
        """Set the path for automatic persistence.

        Args:
            path: Path to save history JSON file.
        """
        self._save_path = path
        if path.exists():
            self.load(path)

    def add(self, operation: FileOperation) -> None:
        """Add an operation to history.

        Args:
            operation: File operation to record.
        """
        entry = HistoryEntry(operation=operation)
        self.entries.append(entry)

        # Trim old entries if we exceed max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

        logger.info(
            "History: %s %s -> %s (rule: %s)",
            operation.action.value,
            operation.source,
            operation.destination or "deleted",
            operation.rule_name,
        )

        # Auto-save if path is configured
        if self._save_path:
            self.save(self._save_path)

    def undo_last(self, count: int = 1) -> list[HistoryEntry]:
        """Undo the last N successful operations.

        Args:
            count: Number of operations to undo.

        Returns:
            List of undone entries.
        """
        undone = []
        successful_entries = [
            e for e in reversed(self.entries)
            if e.operation.success and not e.undone
        ]

        for entry in successful_entries[:count]:
            result = self._undo_entry(entry)
            if result:
                undone.append(entry)

        return undone

    def undo_entry(self, index: int) -> HistoryEntry | None:
        """Undo a specific history entry by index.

        Args:
            index: Index of the entry to undo.

        Returns:
            The undone entry, or None if not found/undoable.
        """
        if 0 <= index < len(self.entries):
            entry = self.entries[index]
            if entry.operation.success and not entry.undone:
                result = self._undo_entry(entry)
                if result:
                    return entry
        return None

    def _undo_entry(self, entry: HistoryEntry) -> bool:
        """Undo a single history entry.

        Args:
            entry: Entry to undo.

        Returns:
            True if undo was successful.
        """
        op = entry.operation

        # Create reverse operation
        reverse_op = self._create_reverse_operation(op)
        if reverse_op is None:
            logger.error("Cannot undo operation: %s", op.action.value)
            return False

        result = execute_operation(reverse_op)

        if result.success:
            entry.undone = True
            entry.undone_at = datetime.now()
            logger.info("Undone: %s %s", op.action.value, op.source)
            return True
        else:
            logger.error("Undo failed: %s", result.error)
            return False

    def _create_reverse_operation(self, op: FileOperation) -> FileOperation | None:
        """Create a reverse operation for undo.

        Args:
            op: Original operation.

        Returns:
            Reverse operation, or None if not possible.
        """
        if op.action == FileAction.DELETE:
            # Cannot undo delete (file is in trash)
            return None

        if op.action == FileAction.MOVE:
            # Reverse move: move back to original location
            if op.destination and op.destination.exists():
                return FileOperation(
                    source=op.destination,
                    action=FileAction.MOVE,
                    destination=op.source,
                    rule_name="undo",
                )

        if op.action == FileAction.COPY:
            # Reverse copy: delete the copy
            if op.destination and op.destination.exists():
                return FileOperation(
                    source=op.destination,
                    action=FileAction.DELETE,
                    rule_name="undo",
                )

        if op.action == FileAction.RENAME:
            # Reverse rename: rename back to original
            if op.destination and op.destination.exists():
                return FileOperation(
                    source=op.destination,
                    action=FileAction.RENAME,
                    new_name=op.source.name,
                    rule_name="undo",
                )

        return None

    def get_recent(self, count: int = 10) -> list[HistoryEntry]:
        """Get recent history entries.

        Args:
            count: Number of entries to return.

        Returns:
            List of recent entries.
        """
        return list(reversed(self.entries[-count:]))

    def clear(self) -> None:
        """Clear all history entries."""
        self.entries.clear()
        logger.info("History cleared")

    def export_json(self, path: Path) -> None:
        """Export history to a JSON file.

        Args:
            path: Path to export file.
        """
        data = [entry.to_dict() for entry in self.entries]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info("History exported to %s", path)

    def import_json(self, path: Path) -> int:
        """Import history from a JSON file.

        Args:
            path: Path to import file.

        Returns:
            Number of entries imported.
        """
        if not path.exists():
            return 0

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for item in data:
            try:
                entry = HistoryEntry.from_dict(item)
                self.entries.append(entry)
                count += 1
            except Exception as e:
                logger.error("Failed to import entry: %s", e)

        logger.info("Imported %d entries from %s", count, path)
        return count

    def save(self, path: Path | None = None) -> None:
        """Save history to disk.

        Args:
            path: Path to save file. Uses configured path if None.
        """
        save_path = path or self._save_path
        if save_path is None:
            return
        self.export_json(save_path)

    def load(self, path: Path) -> int:
        """Load history from disk.

        Args:
            path: Path to load from.

        Returns:
            Number of entries loaded.
        """
        count = self.import_json(path)
        self._save_path = path
        return count

    @property
    def stats(self) -> dict:
        """Get history statistics."""
        total = len(self.entries)
        successful = sum(1 for e in self.entries if e.operation.success)
        undone = sum(1 for e in self.entries if e.undone)

        return {
            "total": total,
            "successful": successful,
            "failed": total - successful,
            "undone": undone,
        }
