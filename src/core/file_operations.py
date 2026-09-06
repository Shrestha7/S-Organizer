"""Single source of truth for all file operations.

All file moves, copies, renames, and deletes must go through this module.
Never use os.rename or shutil.move directly elsewhere in the codebase.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from send2trash import send2trash


class FileAction(Enum):
    """Supported file actions."""

    MOVE = "move"
    COPY = "copy"
    RENAME = "rename"
    DELETE = "delete"


class ConflictResolution(Enum):
    """How to handle file conflicts at destination."""

    RENAME = "rename"  # Add suffix (file_1.txt, file_2.txt)
    SKIP = "skip"  # Leave existing file untouched
    OVERWRITE = "overwrite"  # Replace existing file


@dataclass
class FileOperation:
    """Represents a single file operation to be executed."""

    source: Path
    action: FileAction
    destination: Path | None = None
    new_name: str | None = None
    conflict_resolution: ConflictResolution = ConflictResolution.RENAME
    timestamp: datetime = field(default_factory=datetime.now)
    rule_name: str = ""
    success: bool = False
    error: str | None = None

    @property
    def result_path(self) -> Path | None:
        """Return the final path of the file after operation."""
        if self.action == FileAction.DELETE:
            return None
        if self.action == FileAction.RENAME and self.new_name:
            return self.source.parent / self.new_name
        return self.destination


def _get_unique_path(path: Path) -> Path:
    """Generate a unique file path by adding numeric suffix if needed.

    Args:
        path: Target path to check for conflicts.

    Returns:
        Unique path that doesn't exist yet.
    """
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1

    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


def _resolve_destination(op: FileOperation) -> Path:
    """Resolve the final destination path based on conflict resolution.

    Args:
        op: File operation with destination and conflict resolution.

    Returns:
        Resolved destination path.
    """
    dest = op.destination
    if dest is None:
        raise ValueError("Destination not set for operation")

    if op.new_name:
        dest = dest / op.new_name

    if dest.exists():
        if op.conflict_resolution == ConflictResolution.SKIP:
            return dest
        elif op.conflict_resolution == ConflictResolution.OVERWRITE:
            return dest
        else:  # RENAME
            return _get_unique_path(dest)

    return dest


def execute_move(op: FileOperation) -> FileOperation:
    """Execute a move operation.

    Args:
        op: File operation to execute.

    Returns:
        Updated operation with success/error status.
    """
    try:
        dest = _resolve_destination(op)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(op.source), str(dest))
        op.destination = dest
        op.success = True
    except Exception as e:
        op.error = str(e)
    return op


def execute_copy(op: FileOperation) -> FileOperation:
    """Execute a copy operation.

    Args:
        op: File operation to execute.

    Returns:
        Updated operation with success/error status.
    """
    try:
        dest = _resolve_destination(op)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(op.source), str(dest))
        op.destination = dest
        op.success = True
    except Exception as e:
        op.error = str(e)
    return op


def execute_rename(op: FileOperation) -> FileOperation:
    """Execute a rename operation.

    Args:
        op: File operation to execute.

    Returns:
        Updated operation with success/error status.
    """
    try:
        if op.new_name:
            new_path = op.source.parent / op.new_name
            new_path = _get_unique_path(new_path)
            os.rename(str(op.source), str(new_path))
            op.destination = new_path
            op.success = True
        else:
            op.error = "New name not provided for rename operation"
    except Exception as e:
        op.error = str(e)
    return op


def execute_delete(op: FileOperation) -> FileOperation:
    """Execute a delete operation (moves to trash, not permanent).

    Args:
        op: File operation to execute.

    Returns:
        Updated operation with success/error status.
    """
    try:
        send2trash(str(op.source))
        op.success = True
    except Exception as e:
        op.error = str(e)
    return op


def execute_operation(op: FileOperation) -> FileOperation:
    """Execute a file operation based on its action type.

    This is the main entry point for executing file operations.

    Args:
        op: File operation to execute.

    Returns:
        Updated operation with success/error status.
    """
    executors = {
        FileAction.MOVE: execute_move,
        FileAction.COPY: execute_copy,
        FileAction.RENAME: execute_rename,
        FileAction.DELETE: execute_delete,
    }

    executor = executors.get(op.action)
    if executor is None:
        op.error = f"Unknown action: {op.action}"
        return op

    return executor(op)


def format_destination(template: str, source: Path, **kwargs: str) -> str:
    """Format a destination template with file metadata.

    Supported placeholders:
        {name} - File stem (without extension)
        {extension} - File extension (with dot)
        {ext} - File extension (without dot)
        {date} - Last modified date (YYYY-MM-DD)
        {year} - Year of last modification
        {month} - Month of last modification
        {day} - Day of last modification
        {parent} - Parent directory name

    Args:
        template: Destination template string.
        source: Source file path.
        **kwargs: Additional custom placeholders.

    Returns:
        Formatted destination string.
    """
    stat = source.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime)

    replacements = {
        "name": source.stem,
        "extension": source.suffix,
        "ext": source.suffix.lstrip("."),
        "date": mtime.strftime("%Y-%m-%d"),
        "year": str(mtime.year),
        "month": f"{mtime.month:02d}",
        "day": f"{mtime.day:02d}",
        "parent": source.parent.name,
    }
    replacements.update(kwargs)

    result = template
    for key, value in replacements.items():
        result = result.replace(f"{{{key}}}", value)

    return result
