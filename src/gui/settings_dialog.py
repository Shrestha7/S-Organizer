"""Settings dialog for configuring the application."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.gui.theme import apply_theme
from src.main import FileOrganizer
from src.utils.config import save_config


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    def __init__(self, organizer: FileOrganizer, parent: QWidget | None = None) -> None:
        """Initialize the settings dialog.

        Args:
            organizer: File organizer controller.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.organizer = organizer
        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # General settings
        general_group = QGroupBox("General")
        general_layout = QFormLayout(general_group)

        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(100, 5000)
        self.debounce_spin.setSingleStep(100)
        self.debounce_spin.setValue(self.organizer.config.debounce_ms)
        self.debounce_spin.setSuffix(" ms")
        general_layout.addRow("Debounce interval:", self.debounce_spin)

        self.auto_start_checkbox = QCheckBox("Start monitoring on launch")
        self.auto_start_checkbox.setChecked(self.organizer.config.auto_start)
        general_layout.addRow("", self.auto_start_checkbox)

        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_checkbox.setChecked(self.organizer.config.minimize_to_tray)
        general_layout.addRow("", self.minimize_to_tray_checkbox)

        self.notifications_checkbox = QCheckBox("Show notifications")
        self.notifications_checkbox.setChecked(self.organizer.config.notifications)
        general_layout.addRow("", self.notifications_checkbox)

        layout.addWidget(general_group)

        # Appearance settings
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.organizer.config.theme)
        appearance_layout.addRow("Theme:", self.theme_combo)

        layout.addWidget(appearance_group)

        # Logging settings
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText(self.organizer.config.log_level)
        logging_layout.addRow("Log level:", self.log_level_combo)

        from PyQt6.QtWidgets import QLineEdit
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setText(self.organizer.config.log_file)
        self.log_file_edit.setPlaceholderText("Leave empty for stdout only")
        logging_layout.addRow("Log file:", self.log_file_edit)

        self.log_browse_button = QPushButton("Browse")
        self.log_browse_button.clicked.connect(self._browse_log_file)
        logging_layout.addRow("", self.log_browse_button)

        layout.addWidget(logging_group)

        # Watched folders
        folders_group = QGroupBox("Watched Folders")
        folders_layout = QVBoxLayout(folders_group)

        self.folders_list = QListWidget()
        for folder in self.organizer.config.watched_folders:
            self.folders_list.addItem(folder)
        folders_layout.addWidget(self.folders_list)

        folder_buttons = QHBoxLayout()

        self.add_folder_button = QPushButton("Add Folder")
        self.add_folder_button.clicked.connect(self._add_folder)
        folder_buttons.addWidget(self.add_folder_button)

        self.remove_folder_button = QPushButton("Remove Folder")
        self.remove_folder_button.clicked.connect(self._remove_folder)
        folder_buttons.addWidget(self.remove_folder_button)

        folders_layout.addLayout(folder_buttons)

        layout.addWidget(folders_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _add_folder(self) -> None:
        """Add a folder to watch."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folders_list.addItem(folder)

    def _remove_folder(self) -> None:
        """Remove the selected folder."""
        current = self.folders_list.currentRow()
        if current >= 0:
            self.folders_list.takeItem(current)

    def _browse_log_file(self) -> None:
        """Browse for log file path."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Log File",
            "",
            "Log Files (*.log);;All Files (*)",
        )
        if file_path:
            self.log_file_edit.setText(file_path)

    def _save_settings(self) -> None:
        """Save settings and close dialog."""
        # Update config
        self.organizer.config.debounce_ms = self.debounce_spin.value()
        self.organizer.config.auto_start = self.auto_start_checkbox.isChecked()
        self.organizer.config.minimize_to_tray = self.minimize_to_tray_checkbox.isChecked()
        self.organizer.config.notifications = self.notifications_checkbox.isChecked()
        self.organizer.config.theme = self.theme_combo.currentText()
        self.organizer.config.log_level = self.log_level_combo.currentText()
        self.organizer.config.log_file = self.log_file_edit.text()

        # Update watched folders
        self.organizer.config.watched_folders = []
        for i in range(self.folders_list.count()):
            self.organizer.config.watched_folders.append(self.folders_list.item(i).text())

        # Apply theme
        apply_theme(self.organizer.config.theme)

        # Save to file
        save_config(self.organizer.config)

        self.accept()
