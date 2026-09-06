"""File system monitoring using watchdog.

This module provides real-time file system event monitoring with debouncing
to handle rapid successive events (e.g., editor save patterns).
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from watchdog.events import (
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class EventType(Enum):
    """File system event types."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


@dataclass
class FileEvent:
    """Represents a file system event with metadata."""

    event_type: EventType
    source_path: Path
    dest_path: Path | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    is_directory: bool = False

    @classmethod
    def from_watchdog(cls, event: FileSystemEvent) -> FileEvent:
        """Create from a watchdog FileSystemEvent."""
        event_type_map = {
            FileCreatedEvent: EventType.CREATED,
            FileModifiedEvent: EventType.MODIFIED,
            FileDeletedEvent: EventType.DELETED,
            FileMovedEvent: EventType.MOVED,
        }

        event_type = EventType.MODIFIED
        for etype, etype_val in event_type_map.items():
            if isinstance(event, etype):
                event_type = etype_val
                break

        dest = None
        if isinstance(event, FileMovedEvent):
            dest = Path(event.dest_path)

        return cls(
            event_type=event_type,
            source_path=Path(event.src_path),
            dest_path=dest,
            is_directory=event.is_directory,
        )


class EventHandler(FileSystemEventHandler):
    """Watchdog event handler with debouncing.

    Debounces rapid events to handle editor save patterns where
    multiple events fire for a single logical operation.
    """

    def __init__(
        self,
        callback: Callable[[FileEvent], None],
        debounce_ms: int = 500,
        ignore_directories: bool = True,
    ):
        """Initialize the event handler.

        Args:
            callback: Function to call with FileEvent when event occurs.
            debounce_ms: Debounce interval in milliseconds.
            ignore_directories: Whether to ignore directory events.
        """
        super().__init__()
        self.callback = callback
        self.debounce_ms = debounce_ms
        self.ignore_directories = ignore_directories
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def _process_event(self, event: FileEvent) -> None:
        """Process an event after debounce period."""
        try:
            self.callback(event)
        except Exception as e:
            logger.error("Error processing event: %s", e)

    def _debounce(self, event: FileEvent) -> None:
        """Debounce an event to handle rapid successive events."""
        key = str(event.source_path)

        with self._lock:
            # Cancel any pending timer for this path
            if key in self._pending:
                self._pending[key].cancel()

            # Create new timer
            timer = threading.Timer(
                self.debounce_ms / 1000.0,
                self._process_event,
                args=[event],
            )
            self._pending[key] = timer
            timer.start()

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file created event."""
        if self.ignore_directories and event.is_directory:
            return
        self._debounce(FileEvent.from_watchdog(event))

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modified event."""
        if self.ignore_directories and event.is_directory:
            return
        self._debounce(FileEvent.from_watchdog(event))

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deleted event."""
        if self.ignore_directories and event.is_directory:
            return
        self._debounce(FileEvent.from_watchdog(event))

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file moved event."""
        if self.ignore_directories and event.is_directory:
            return
        self._debounce(FileEvent.from_watchdog(event))


@dataclass
class WatchConfig:
    """Configuration for watching a directory."""

    path: Path
    recursive: bool = False
    patterns: list[str] = field(default_factory=lambda: ["*"])
    ignore_patterns: list[str] = field(default_factory=list)


class FileMonitor:
    """Manages file system monitoring for multiple directories.

    This class wraps watchdog's Observer to provide a clean interface
    for monitoring directories with debouncing and pattern filtering.
    """

    def __init__(
        self,
        callback: Callable[[FileEvent], None],
        debounce_ms: int = 500,
    ):
        """Initialize the file monitor.

        Args:
            callback: Function to call with FileEvent when event occurs.
            debounce_ms: Debounce interval in milliseconds.
        """
        self.callback = callback
        self.debounce_ms = debounce_ms
        self._observer: Observer | None = None
        self._watches: dict[Path, WatchConfig] = {}
        self._running = False

    def add_watch(self, config: WatchConfig) -> None:
        """Add a directory to watch.

        Args:
            config: Watch configuration.
        """
        self._watches[config.path] = config

        if self._running and self._observer:
            handler = EventHandler(
                callback=self.callback,
                debounce_ms=self.debounce_ms,
            )
            self._observer.schedule(
                handler,
                str(config.path),
                recursive=config.recursive,
            )
            logger.info("Watching: %s (recursive=%s)", config.path, config.recursive)

    def remove_watch(self, path: Path) -> None:
        """Stop watching a directory.

        Args:
            path: Path to stop watching.
        """
        if path in self._watches:
            del self._watches[path]
            logger.info("Stopped watching: %s", path)

    def start(self) -> None:
        """Start monitoring all watched directories."""
        if self._running:
            return

        self._observer = Observer()

        for config in self._watches.values():
            handler = EventHandler(
                callback=self.callback,
                debounce_ms=self.debounce_ms,
            )
            self._observer.schedule(
                handler,
                str(config.path),
                recursive=config.recursive,
            )
            logger.info("Watching: %s (recursive=%s)", config.path, config.recursive)

        self._observer.start()
        self._running = True
        logger.info("File monitor started")

    def stop(self) -> None:
        """Stop monitoring all directories."""
        if not self._running or self._observer is None:
            return

        self._observer.stop()
        self._observer.join(timeout=5)
        self._observer = None
        self._running = False
        logger.info("File monitor stopped")

    @property
    def is_running(self) -> bool:
        """Check if monitor is running."""
        return self._running

    @property
    def watched_paths(self) -> list[Path]:
        """Get list of watched paths."""
        return list(self._watches.keys())
