"""Main application window with tabbed interface."""

from __future__ import annotations

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.history_panel import HistoryPanel
from src.gui.monitor_panel import MonitorPanel
from src.gui.rule_editor import RuleEditor
from src.gui.settings_dialog import SettingsDialog
from src.main import FileOrganizer


class MainWindow(QMainWindow):
    """Main application window with tabbed interface.

    Features:
    - Rules tab: Manage organization rules
    - Monitor tab: View live file events
    - History tab: View and undo operations
    """

    def __init__(self, organizer: FileOrganizer) -> None:
        """Initialize the main window.

        Args:
            organizer: File organizer controller.
        """
        super().__init__()
        self.organizer = organizer
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("S-Organizer")
        self.setMinimumSize(800, 600)

        # Central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.rule_editor = RuleEditor(self.organizer)
        self.monitor_panel = MonitorPanel(self.organizer)
        self.history_panel = HistoryPanel(self.organizer)

        self.tab_widget.addTab(self.rule_editor, "Rules")
        self.tab_widget.addTab(self.monitor_panel, "Monitor")
        self.tab_widget.addTab(self.history_panel, "History")

    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Monitor menu
        monitor_menu = menubar.addMenu("Monitor")

        self.start_action = QAction("Start Monitoring", self)
        self.start_action.setShortcut("Ctrl+Shift+S")
        self.start_action.triggered.connect(self._start_monitoring)
        monitor_menu.addAction(self.start_action)

        self.stop_action = QAction("Stop Monitoring", self)
        self.stop_action.setShortcut("Ctrl+Shift+X")
        self.stop_action.triggered.connect(self._stop_monitoring)
        monitor_menu.addAction(self.stop_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self) -> None:
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Monitoring status
        self.monitor_status_label = QLabel("Monitoring: Stopped")
        self.status_bar.addPermanentWidget(self.monitor_status_label)

        # Rule count
        self.rule_count_label = QLabel("Rules: 0")
        self.status_bar.addPermanentWidget(self.rule_count_label)

        self._update_status()

    def _update_status(self) -> None:
        """Update the status bar."""
        if self.organizer.is_running:
            self.monitor_status_label.setText("Monitoring: Active")
        else:
            self.monitor_status_label.setText("Monitoring: Stopped")

        self.rule_count_label.setText(f"Rules: {len(self.organizer.rule_engine.rules)}")

    def _start_monitoring(self) -> None:
        """Start file monitoring."""
        self.organizer.start()
        self._update_status()
        self.status_bar.showMessage("Monitoring started", 3000)

    def _stop_monitoring(self) -> None:
        """Stop file monitoring."""
        self.organizer.stop()
        self._update_status()
        self.status_bar.showMessage("Monitoring stopped", 3000)

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self.organizer, self)
        if dialog.exec():
            self._update_status()

    def _show_about(self) -> None:
        """Show the about dialog."""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About S-Organizer",
            "S-Organizer v0.1.0\n\n"
            "Automatic file organization with PyQt6 GUI.\n\n"
            "License: Apache 2.0",
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        """Handle window close event."""
        if self.organizer.is_running:
            self.organizer.stop()
        event.accept()
