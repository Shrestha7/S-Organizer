"""S-Organizer - Automatic file organization with PyQt6 GUI.

This is the main entry point for the application.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.core.file_monitor import FileEvent, FileMonitor, WatchConfig  # noqa: E402
from src.core.history import History  # noqa: E402
from src.core.rule_engine import RuleEngine  # noqa: E402
from src.utils.config import (  # noqa: E402
    AppConfig,
    ensure_directories,
    get_data_dir,
    load_config,
    save_config,
)

logger = logging.getLogger(__name__)


class FileOrganizer:
    """Main application controller.

    Coordinates between the file monitor, rule engine, and history.
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        """Initialize the application.

        Args:
            config: Application configuration. Loads from file if None.
        """
        self.config = config or load_config()
        ensure_directories(self.config)

        self.rule_engine = RuleEngine()
        self.history = History()
        self.monitor = FileMonitor(
            callback=self._on_file_event,
            debounce_ms=self.config.debounce_ms,
        )

        self._load_rules()

    def _load_rules(self) -> None:
        """Load rules from the rules directory."""
        rules_dir = get_data_dir() / self.config.rules_dir
        count = self.rule_engine.load_rules_from_directory(rules_dir)
        logger.info("Loaded %d rules", count)

    def _on_file_event(self, event: FileEvent) -> None:
        """Handle a file system event.

        Args:
            event: File event from the monitor.
        """
        logger.debug("File event: %s %s", event.event_type.value, event.source_path)

        # Process event against all rules
        results = self.rule_engine.process_event(event)

        # Record results in history
        for result in results:
            if result.operation:
                self.history.add(result.operation)

    def start(self) -> None:
        """Start monitoring configured folders."""
        for folder_str in self.config.watched_folders:
            folder = Path(folder_str).expanduser().resolve()
            if folder.exists():
                config = WatchConfig(path=folder, recursive=True)
                self.monitor.add_watch(config)

        self.monitor.start()
        logger.info("Monitoring started")

    def stop(self) -> None:
        """Stop monitoring all folders."""
        self.monitor.stop()
        logger.info("Monitoring stopped")

    def add_watched_folder(self, folder: str) -> None:
        """Add a folder to watch.

        Args:
            folder: Path to folder to watch.
        """
        if folder not in self.config.watched_folders:
            self.config.watched_folders.append(folder)

            # Add to monitor if running
            folder_path = Path(folder).expanduser().resolve()
            if folder_path.exists():
                config = WatchConfig(path=folder_path, recursive=True)
                self.monitor.add_watch(config)

            save_config(self.config)

    def remove_watched_folder(self, folder: str) -> None:
        """Stop watching a folder.

        Args:
            folder: Path to folder to stop watching.
        """
        if folder in self.config.watched_folders:
            self.config.watched_folders.remove(folder)

            folder_path = Path(folder).expanduser().resolve()
            self.monitor.remove_watch(folder_path)

            save_config(self.config)

    def undo_last(self, count: int = 1) -> list:
        """Undo the last N operations.

        Args:
            count: Number of operations to undo.

        Returns:
            List of undone operations.
        """
        return self.history.undo_last(count)

    def preview_file(self, file_path: Path) -> list:
        """Preview what rules would match a file.

        Args:
            file_path: Path to check.

        Returns:
            List of rules that would match.
        """
        return self.rule_engine.get_matching_rules(file_path)

    @property
    def is_running(self) -> bool:
        """Check if monitoring is active."""
        return self.monitor.is_running


def main() -> None:
    """Main entry point."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Check if GUI mode is requested
    if "--gui" in sys.argv or len(sys.argv) == 1:
        # Launch GUI
        from PyQt6.QtWidgets import QApplication

        from src.gui.main_window import MainWindow

        app = QApplication(sys.argv)
        app.setApplicationName("S-Organizer")

        organizer = FileOrganizer()
        window = MainWindow(organizer)
        window.show()

        sys.exit(app.exec())
    else:
        # CLI mode
        print("S-Organizer v0.1.0")
        print("Use 'from src.main import FileOrganizer' to import the controller.")
        print("Run without arguments or with --gui to launch the GUI.")


if __name__ == "__main__":
    main()
