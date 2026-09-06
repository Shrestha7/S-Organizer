"""Duplicate file detection and handling."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DuplicateGroup:
    """A group of duplicate files."""

    hash: str
    files: list[Path]
    total_size: int

    @property
    def original(self) -> Path:
        """Return the original file (first in list)."""
        return self.files[0] if self.files else Path()

    @property
    def duplicates(self) -> list[Path]:
        """Return duplicate files (all except first)."""
        return self.files[1:] if len(self.files) > 1 else []

    @property
    def wasted_space(self) -> int:
        """Return wasted space in bytes."""
        if len(self.files) <= 1:
            return 0
        return self.total_size * (len(self.files) - 1)


def calculate_file_hash(
    file_path: Path,
    algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str | None:
    """Calculate hash of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (md5, sha1, sha256).
        chunk_size: Read chunk size.

    Returns:
        Hex digest of the hash, or None if error.
    """
    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, PermissionError):
        return None


def find_duplicates(
    directories: list[Path],
    recursive: bool = True,
    algorithm: str = "sha256",
    min_size: int = 1,
) -> list[DuplicateGroup]:
    """Find duplicate files across directories.

    Args:
        directories: Directories to scan.
        recursive: Whether to scan subdirectories.
        algorithm: Hash algorithm to use.
        min_size: Minimum file size to consider.

    Returns:
        List of duplicate groups.
    """
    # Build hash map
    hash_map: dict[str, list[Path]] = defaultdict(list)

    for directory in directories:
        if not directory.exists():
            continue

        pattern = "**/*" if recursive else "*"
        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue

            try:
                size = file_path.stat().st_size
            except OSError:
                continue

            if size < min_size:
                continue

            file_hash = calculate_file_hash(file_path, algorithm)
            if file_hash:
                hash_map[file_hash].append(file_path)

    # Find duplicates
    duplicates = []
    for file_hash, files in hash_map.items():
        if len(files) > 1:
            # Sort by modification time (oldest first)
            files.sort(key=lambda f: f.stat().st_mtime)
            total_size = sum(f.stat().st_size for f in files)
            duplicates.append(
                DuplicateGroup(
                    hash=file_hash,
                    files=files,
                    total_size=total_size,
                )
            )

    # Sort by wasted space (largest first)
    duplicates.sort(key=lambda d: d.wasted_space, reverse=True)

    return duplicates


def find_duplicates_in_folder(
    folder: Path,
    recursive: bool = True,
    algorithm: str = "sha256",
    min_size: int = 1,
) -> list[DuplicateGroup]:
    """Find duplicates in a single folder.

    Args:
        folder: Folder to scan.
        recursive: Whether to scan subdirectories.
        algorithm: Hash algorithm to use.
        min_size: Minimum file size to consider.

    Returns:
        List of duplicate groups.
    """
    return find_duplicates(
        [folder],
        recursive=recursive,
        algorithm=algorithm,
        min_size=min_size,
    )


def get_duplicate_stats(duplicates: list[DuplicateGroup]) -> dict:
    """Get statistics about duplicates.

    Args:
        duplicates: List of duplicate groups.

    Returns:
        Dictionary with statistics.
    """
    total_groups = len(duplicates)
    total_files = sum(len(d.files) for d in duplicates)
    total_wasted = sum(d.wasted_space for d in duplicates)

    return {
        "groups": total_groups,
        "files": total_files,
        "wasted_bytes": total_wasted,
        "wasted_mb": total_wasted / (1024 * 1024),
    }
