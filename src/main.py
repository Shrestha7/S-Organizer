"""S-Organizer - Automatic file organization with PyQt6 GUI.

This is the main entry point for the application.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import __version__  # noqa: E402
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
        self._notification_callback: callable | None = None

        # Set up history persistence
        history_path = get_data_dir() / self.config.history_dir / "history.json"
        self.history.set_save_path(history_path)

        self._load_rules()

    def set_notification_callback(self, callback: callable) -> None:
        """Set a callback for notifications.

        Args:
            callback: Function that takes (title, message) arguments.
        """
        self._notification_callback = callback

    def _notify(self, title: str, message: str) -> None:
        """Send a notification.

        Args:
            title: Notification title.
            message: Notification message.
        """
        if self._notification_callback and self.config.notifications:
            self._notification_callback(title, message)

    def _load_rules(self) -> None:
        """Load rules from the rules directory."""
        rules_dir = get_data_dir() / self.config.rules_dir
        count = self.rule_engine.load_rules_from_directory(rules_dir)
        logger.info("Loaded %d rules", count)

    def save_rules(self) -> None:
        """Save all rules to the rules directory."""
        rules_dir = get_data_dir() / self.config.rules_dir
        count = self.rule_engine.save_rules_to_directory(rules_dir)
        logger.info("Saved %d rules", count)

    def _on_file_event(self, event: FileEvent) -> None:
        """Handle a file system event.

        Args:
            event: File event from the monitor.
        """
        logger.debug("File event: %s %s", event.event_type.value, event.source_path)

        # Process event against all rules
        results = self.rule_engine.process_event(event)

        # Record results in history and notify
        for result in results:
            if result.operation:
                self.history.add(result.operation)

                # Send notification for successful operations
                if result.operation.success:
                    action = result.operation.action.value.capitalize()
                    filename = result.operation.source.name
                    dest = result.operation.destination
                    if dest:
                        msg = f"{action}: {filename} -> {dest.parent}"
                    else:
                        msg = f"{action}: {filename}"
                    self._notify(f"File {action}d", msg)

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


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="s-organizer",
        description="S-Organizer - Automatic file organization tool",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        default=True,
        help="Launch GUI (default)",
    )
    parser.add_argument(
        "--scan",
        type=str,
        metavar="FOLDER",
        help="One-time scan of a folder",
    )
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to config file",
    )
    return parser.parse_args()


def scan_folder(folder: str, config: AppConfig | None = None) -> None:
    """Scan a folder once with all rules.

    Args:
        folder: Path to folder to scan.
        config: Optional configuration.
    """
    config = config or load_config()
    ensure_directories(config)

    folder_path = Path(folder).expanduser().resolve()
    if not folder_path.exists():
        print(f"Error: Folder does not exist: {folder}")
        return

    rule_engine = RuleEngine()
    rules_dir = get_data_dir() / config.rules_dir
    count = rule_engine.load_rules_from_directory(rules_dir)
    print(f"Loaded {count} rules")

    # Create a temporary monitor to process the folder
    processed = 0

    from src.core.file_monitor import EventType, FileEvent

    for item in folder_path.rglob("*"):
        if item.is_file():
            event = FileEvent(
                event_type=EventType.CREATED,
                source_path=item,
                dest_path=None,
            )
            results = rule_engine.process_event(event)
            for result in results:
                if result.operation and result.operation.success:
                    processed += 1
                    action = result.operation.action.value.capitalize()
                    print(f"  {action}: {item.name}")

    print(f"\nProcessed {processed} files")


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Load config first to get log settings
    config = load_config(Path(args.config) if args.config else None)

    # Set up logging
    log_handlers: list[logging.Handler] = [logging.StreamHandler()]
    if config.log_file:
        from logging.handlers import RotatingFileHandler
        log_file = Path(config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=5*1024*1024, backupCount=3
        )
        log_handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=log_handlers,
    )

    # CLI mode: scan folder
    if args.scan:
        scan_folder(args.scan, config)
        return

    # GUI mode
    from PyQt6.QtWidgets import QApplication

    from src.gui.main_window import MainWindow
    from src.gui.system_tray import SystemTrayIcon

    app = QApplication(sys.argv)
    app.setApplicationName("S-Organizer")

    # Set application icon
    from src.resources import get_app_icon
    app.setWindowIcon(get_app_icon())

    organizer = FileOrganizer(config)
    window = MainWindow(organizer)

    # Apply theme
    from src.gui.theme import apply_theme
    apply_theme(organizer.config.theme)

    # Set up system tray
    tray_icon = SystemTrayIcon()

    # Connect tray signals to window
    tray_icon.show_window.connect(window.show)
    tray_icon.hide_window.connect(window.hide)
    tray_icon.start_monitoring.connect(window._start_monitoring)
    tray_icon.stop_monitoring.connect(window._stop_monitoring)
    tray_icon.open_settings.connect(window._open_settings)
    tray_icon.quit_app.connect(app.quit)

    # Store tray icon reference on window for notifications
    window.tray_icon = tray_icon

    # Connect window close to tray behavior
    window.set_tray_icon(tray_icon)

    # Connect organizer notifications to window
    organizer.set_notification_callback(window._show_notification)

    tray_icon.show()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
