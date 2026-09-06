"""System tray integration for background monitoring."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QMenu,
    QSystemTrayIcon,
    QWidget,
)


class SystemTrayIcon(QSystemTrayIcon):
    """System tray icon for background monitoring.

    Features:
    - Show/hide main window
    - Start/stop monitoring
    - Quick access to settings
    - Notifications for file operations
    """

    show_window = pyqtSignal()
    hide_window = pyqtSignal()
    start_monitoring = pyqtSignal()
    stop_monitoring = pyqtSignal()
    open_settings = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the system tray icon.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Set icon (using a default icon for now)
        self.setIcon(QIcon.fromTheme("folder-sync"))

        # Create context menu
        self._create_menu()

        # Connect signals
        self.activated.connect(self._on_activated)

        # Status
        self._is_monitoring = False

    def _create_menu(self) -> None:
        """Create the context menu."""
        menu = QMenu()

        # Show/Hide
        show_action = QAction("Show Window", self)
        show_action.triggered.connect(self.show_window.emit)
        menu.addAction(show_action)

        hide_action = QAction("Hide Window", self)
        hide_action.triggered.connect(self.hide_window.emit)
        menu.addAction(hide_action)

        menu.addSeparator()

        # Monitoring
        self.start_action = QAction("Start Monitoring", self)
        self.start_action.triggered.connect(self._on_start_monitoring)
        menu.addAction(self.start_action)

        self.stop_action = QAction("Stop Monitoring", self)
        self.stop_action.triggered.connect(self._on_stop_monitoring)
        self.stop_action.setEnabled(False)
        menu.addAction(self.stop_action)

        menu.addSeparator()

        # Settings
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Quit
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app.emit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window.emit()

    def _on_start_monitoring(self) -> None:
        """Start monitoring."""
        self._is_monitoring = True
        self.start_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.start_monitoring.emit()

    def _on_stop_monitoring(self) -> None:
        """Stop monitoring."""
        self._is_monitoring = False
        self.start_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.stop_monitoring.emit()

    def set_monitoring_state(self, is_monitoring: bool) -> None:
        """Update the monitoring state.

        Args:
            is_monitoring: Whether monitoring is active.
        """
        self._is_monitoring = is_monitoring
        self.start_action.setEnabled(not is_monitoring)
        self.stop_action.setEnabled(is_monitoring)

    def show_notification(self, title: str, message: str) -> None:
        """Show a notification.

        Args:
            title: Notification title.
            message: Notification message.
        """
        self.showMessage(title, message)
