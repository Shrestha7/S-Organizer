"""Main application window with tabbed interface."""

from __future__ import annotations

import sys

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src import __version__
from src.core.updater import UpdateInfo, is_frozen
from src.gui.duplicate_panel import DuplicatePanel
from src.gui.history_panel import HistoryPanel
from src.gui.monitor_panel import MonitorPanel
from src.gui.rule_editor import RuleEditor
from src.gui.settings_dialog import SettingsDialog
from src.gui.system_tray import SystemTrayIcon
from src.gui.update_worker import UpdateCheckWorker, UpdateDownloadWorker, create_update_script
from src.main import FileOrganizer


class MainWindow(QMainWindow):
    """Main application window with tabbed interface.

    Features:
    - Rules tab: Manage organization rules
    - Monitor tab: View live file events
    - History tab: View and undo operations
    - System tray integration
    """

    # Signal for notifications from worker threads
    notification = pyqtSignal(str, str)

    def __init__(self, organizer: FileOrganizer) -> None:
        """Initialize the main window.

        Args:
            organizer: File organizer controller.
        """
        super().__init__()
        self.organizer = organizer
        self.tray_icon: SystemTrayIcon | None = None
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._connect_notifications()

        # Auto-start monitoring if configured
        if self.organizer.config.auto_start:
            self.organizer.start()
            self.monitor_panel.status_label.setText("Status: Active")
            self.monitor_panel.start_button.setEnabled(False)
            self.monitor_panel.stop_button.setEnabled(True)
            self.monitor_status_label.setText("Monitoring: Active")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("S-Organizer")
        self.setMinimumSize(800, 600)
        self.resize(
            self.organizer.config.window_width,
            self.organizer.config.window_height,
        )

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
        self.duplicate_panel = DuplicatePanel()

        self.tab_widget.addTab(self.rule_editor, "Rules")
        self.tab_widget.addTab(self.monitor_panel, "Monitor")
        self.tab_widget.addTab(self.history_panel, "History")
        self.tab_widget.addTab(self.duplicate_panel, "Duplicates")

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

        check_update_action = QAction("Check for Updates...", self)
        check_update_action.triggered.connect(self._check_for_update)
        help_menu.addAction(check_update_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self) -> None:
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Progress bar for updates (hidden by default)
        self.update_progress = QProgressBar()
        self.update_progress.setMaximumWidth(200)
        self.update_progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.update_progress)

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

    def set_tray_icon(self, tray_icon: SystemTrayIcon) -> None:
        """Set the system tray icon for this window.

        Args:
            tray_icon: System tray icon instance.
        """
        self.tray_icon = tray_icon
        self.tray_icon.set_monitoring_state(self.organizer.is_running)

    def _connect_notifications(self) -> None:
        """Connect notification signal to tray icon."""
        self.notification.connect(self._show_notification)

    def _show_notification(self, title: str, message: str) -> None:
        """Show a notification via tray icon.

        Args:
            title: Notification title.
            message: Notification message.
        """
        if self.tray_icon and self.organizer.config.notifications:
            self.tray_icon.show_notification(title, message)

    def _start_monitoring(self) -> None:
        """Start file monitoring."""
        self.organizer.start()
        self._update_status()
        if self.tray_icon:
            self.tray_icon.set_monitoring_state(True)
        self.status_bar.showMessage("Monitoring started", 3000)

    def _stop_monitoring(self) -> None:
        """Stop file monitoring."""
        self.organizer.stop()
        self._update_status()
        if self.tray_icon:
            self.tray_icon.set_monitoring_state(False)
        self.status_bar.showMessage("Monitoring stopped", 3000)

    def _open_settings(self) -> None:
        """Open the settings dialog."""
        dialog = SettingsDialog(self.organizer, self)
        if dialog.exec():
            self._update_status()

    def _show_about(self) -> None:
        """Show the about dialog."""
        QMessageBox.about(
            self,
            "About S-Organizer",
            f"S-Organizer v{__version__}\n\n"
            "Automatic file organization with PyQt6 GUI.\n\n"
            "License: Apache 2.0",
        )

    def _check_for_update(self) -> None:
        """Check for updates from GitHub releases."""
        self.status_bar.showMessage("Checking for updates...")
        self._update_worker = UpdateCheckWorker(__version__)
        self._update_worker.finished.connect(self._on_update_check_complete)
        self._update_worker.error.connect(self._on_update_check_error)
        self._update_worker.start()

    def _on_update_check_complete(self, info: object) -> None:
        """Handle update check completion."""
        if not isinstance(info, UpdateInfo):
            return

        if info.has_update:
            self._show_update_available(info)
        else:
            self.status_bar.showMessage("You're up to date!", 5000)
            QMessageBox.information(
                self,
                "No Updates Available",
                f"You're running the latest version (v{__version__}).",
            )

    def _on_update_check_error(self, error_msg: str) -> None:
        """Handle update check error."""
        self.status_bar.showMessage("Update check failed", 5000)
        QMessageBox.warning(
            self,
            "Update Check Failed",
            f"Could not check for updates:\n{error_msg}",
        )

    def _show_update_available(self, info: UpdateInfo) -> None:
        """Show dialog when update is available."""
        reply = QMessageBox.question(
            self,
            "Update Available",
            f"A new version is available!\n\n"
            f"Current: v{info.current_version}\n"
            f"Latest: v{info.latest_version}\n\n"
            f"{info.release_notes[:200]}{'...' if len(info.release_notes) > 200 else ''}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if is_frozen():
                self._download_update(info)
            else:
                QMessageBox.information(
                    self,
                    "Update Available",
                    "To update, run in your terminal:\n\n"
                    "pip install --upgrade s-organizer",
                )

    def _download_update(self, info: UpdateInfo) -> None:
        """Download the update exe."""
        if not info.download_url:
            QMessageBox.warning(
                self,
                "Download Error",
                "No download URL found for this update.",
            )
            return

        self.status_bar.showMessage("Downloading update...")
        self.update_progress.setVisible(True)
        self.update_progress.setValue(0)

        self._download_worker = UpdateDownloadWorker(info.download_url)
        self._download_worker.progress.connect(self._on_download_progress)
        self._download_worker.finished.connect(self._on_download_complete)
        self._download_worker.error.connect(self._on_download_error)
        self._download_worker.start()

    def _on_download_progress(self, percent: int) -> None:
        """Update progress bar during download."""
        self.update_progress.setValue(percent)

    def _on_download_complete(self, path: str) -> None:
        """Handle download completion."""
        self.update_progress.setVisible(False)
        self.status_bar.showMessage("Update downloaded!", 5000)

        reply = QMessageBox.question(
            self,
            "Update Ready",
            "Update downloaded successfully!\n\nRestart now to apply the update?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._apply_update(path)

    def _on_download_error(self, error_msg: str) -> None:
        """Handle download error."""
        self.update_progress.setVisible(False)
        self.status_bar.showMessage("Download failed", 5000)
        QMessageBox.warning(
            self,
            "Download Failed",
            f"Could not download update:\n{error_msg}",
        )

    def _apply_update(self, new_exe_path: str) -> None:
        """Apply the downloaded update by launching batch script and exiting."""
        import subprocess
        script_path = create_update_script(new_exe_path)

        if sys.platform == "win32":
            subprocess.Popen(
                ["cmd", "/c", script_path],
                creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                ["sh", script_path],
                start_new_session=True,
                close_fds=True,
            )

        # Force kill immediately to release file handle
        import os
        os._exit(0)

    def closeEvent(self, event) -> None:  # noqa: N802
        """Handle window close event."""
        # Minimize to tray if configured and tray icon exists
        if self.organizer.config.minimize_to_tray and self.tray_icon:
            event.ignore()
            self.hide()
            self.tray_icon.show_notification(
                "S-Organizer", "Running in background. Click tray icon to show."
            )
            return

        # Save window size
        self.organizer.config.window_width = self.width()
        self.organizer.config.window_height = self.height()
        from src.utils.config import save_config
        save_config(self.organizer.config)

        if self.organizer.is_running:
            self.organizer.stop()

        # Save history before exit
        self.organizer.history.save()

        event.accept()
