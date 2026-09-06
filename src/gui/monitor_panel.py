"""Monitor panel GUI for viewing live file events."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.file_monitor import EventType, FileEvent
from src.main import FileOrganizer


class OneShotScanWorker(QThread):
    """Worker thread for one-shot folder scan."""

    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, organizer: FileOrganizer, folder: Path) -> None:
        super().__init__()
        self.organizer = organizer
        self.folder = folder

    def run(self) -> None:
        try:
            count = 0
            pattern = "**/*"
            for file_path in self.folder.glob(pattern):
                if not file_path.is_file():
                    continue

                # Create a synthetic file event
                event = FileEvent(
                    event_type=EventType.CREATED,
                    source_path=file_path,
                    is_directory=False,
                )

                # Process against rules
                results = self.organizer.rule_engine.process_event(event)
                for result in results:
                    if result.operation:
                        self.organizer.history.add(result.operation)
                        count += 1

            self.finished.emit(count)
        except Exception as e:
            self.error.emit(str(e))


class MonitorPanel(QWidget):
    """Widget for viewing live file system events."""

    def __init__(self, organizer: FileOrganizer) -> None:
        """Initialize the monitor panel.

        Args:
            organizer: File organizer controller.
        """
        super().__init__()
        self.organizer = organizer
        self._events: list[FileEvent] = []
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header_layout = QVBoxLayout()
        header_layout.addWidget(QLabel("File System Monitor"))

        # Status and controls
        controls_layout = QVBoxLayout()

        self.status_label = QLabel("Status: Stopped")
        controls_layout.addWidget(self.status_label)

        button_layout = QVBoxLayout()
        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self._start_monitoring)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self._stop_monitoring)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        # One-shot scan
        scan_layout = QVBoxLayout()
        self.scan_now_button = QPushButton("Scan Folder Once")
        self.scan_now_button.setToolTip(
            "Run all rules against a folder once (no continuous monitoring)"
        )
        self.scan_now_button.clicked.connect(self._scan_now)
        scan_layout.addWidget(self.scan_now_button)

        self.scan_status_label = QLabel("")
        scan_layout.addWidget(self.scan_status_label)

        button_layout.addLayout(scan_layout)

        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self._clear_log)
        button_layout.addWidget(self.clear_button)

        controls_layout.addLayout(button_layout)
        header_layout.addLayout(controls_layout)

        layout.addLayout(header_layout)

        # Event table
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(4)
        self.event_table.setHorizontalHeaderLabels(["Time", "Event", "Path", "Details"])
        self.event_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.event_table.setAlternatingRowColors(True)
        layout.addWidget(self.event_table)

        # Event count
        self.count_label = QLabel("Events: 0")
        layout.addWidget(self.count_label)

    def _connect_signals(self) -> None:
        """Connect to organizer signals."""
        # Patch the organizer's event handler to also update the GUI
        self._original_handler = self.organizer._on_file_event
        self.organizer._on_file_event = self._on_file_event

    def _on_file_event(self, event: FileEvent) -> None:
        """Handle a file event and update the GUI."""
        # Call original handler
        self._original_handler(event)

        # Store event
        self._events.append(event)
        if len(self._events) > 1000:
            self._events = self._events[-1000:]

        # Update table
        self._add_event_to_table(event)

    def _add_event_to_table(self, event: FileEvent) -> None:
        """Add an event to the table."""
        row = self.event_table.rowCount()
        self.event_table.insertRow(row)

        # Time
        time_item = QTableWidgetItem(event.timestamp.strftime("%H:%M:%S"))
        self.event_table.setItem(row, 0, time_item)

        # Event type
        event_type_map = {
            EventType.CREATED: "Created",
            EventType.MODIFIED: "Modified",
            EventType.DELETED: "Deleted",
            EventType.MOVED: "Moved",
        }
        event_item = QTableWidgetItem(event_type_map.get(event.event_type, "Unknown"))
        self.event_table.setItem(row, 1, event_item)

        # Path
        path_item = QTableWidgetItem(str(event.source_path))
        self.event_table.setItem(row, 2, path_item)

        # Details
        details = ""
        if event.dest_path:
            details = f"-> {event.dest_path}"
        details_item = QTableWidgetItem(details)
        self.event_table.setItem(row, 3, details_item)

        # Update count
        self.count_label.setText(f"Events: {self.event_table.rowCount()}")

        # Auto-scroll to bottom
        self.event_table.scrollToBottom()

    def _start_monitoring(self) -> None:
        """Start monitoring."""
        self.organizer.start()
        self.status_label.setText("Status: Active")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def _stop_monitoring(self) -> None:
        """Stop monitoring."""
        self.organizer.stop()
        self.status_label.setText("Status: Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _clear_log(self) -> None:
        """Clear the event log."""
        self.event_table.setRowCount(0)
        self._events.clear()
        self.count_label.setText("Events: 0")

    def _scan_now(self) -> None:
        """Scan a folder once against all rules."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if not folder:
            return

        folder_path = Path(folder)
        if not folder_path.exists():
            return

        self.scan_now_button.setEnabled(False)
        self.scan_status_label.setText("Scanning...")

        self._scan_worker = OneShotScanWorker(self.organizer, folder_path)
        self._scan_worker.finished.connect(self._on_scan_complete)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.start()

    def _on_scan_complete(self, count: int) -> None:
        """Handle scan completion."""
        self.scan_now_button.setEnabled(True)
        self.scan_status_label.setText(f"Scan complete: {count} file(s) processed")

    def _on_scan_error(self, error_msg: str) -> None:
        """Handle scan error."""
        self.scan_now_button.setEnabled(True)
        self.scan_status_label.setText(f"Scan failed: {error_msg}")

    def refresh_status(self) -> None:
        """Refresh the monitoring status."""
        if self.organizer.is_running:
            self.status_label.setText("Status: Active")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("Status: Stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
