"""Duplicate file detection and management panel."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.duplicate_detector import (
    DuplicateGroup,
    find_duplicates,
    get_duplicate_stats,
)
from src.core.file_operations import (
    ConflictResolution,
    FileAction,
    FileOperation,
    execute_operation,
)

logger = logging.getLogger(__name__)


class DuplicateScanWorker(QThread):
    """Worker thread for scanning duplicates."""

    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, directories: list[Path], recursive: bool = True) -> None:
        super().__init__()
        self.directories = directories
        self.recursive = recursive

    def run(self) -> None:
        try:
            duplicates = find_duplicates(
                self.directories,
                recursive=self.recursive,
            )
            self.finished.emit(duplicates)
        except Exception as e:
            self.error.emit(str(e))


class DuplicatePanel(QWidget):
    """Panel for finding and managing duplicate files."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._duplicates: list[DuplicateGroup] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Scan controls
        scan_group = QGroupBox("Scan")
        scan_layout = QVBoxLayout(scan_group)

        folder_layout = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Select folder to scan for duplicates...")
        folder_layout.addWidget(self.folder_edit)

        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self._browse_folder)
        folder_layout.addWidget(self.browse_button)

        scan_layout.addLayout(folder_layout)

        button_layout = QHBoxLayout()
        self.scan_button = QPushButton("Scan for Duplicates")
        self.scan_button.clicked.connect(self._start_scan)
        button_layout.addWidget(self.scan_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        button_layout.addWidget(self.progress_bar)

        scan_layout.addLayout(button_layout)

        layout.addWidget(scan_group)

        # Stats
        self.stats_label = QLabel("No duplicates found")
        layout.addWidget(self.stats_label)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(
            ["Group", "File", "Size", "Modified", "Path"]
        )
        self.results_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch
        )
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.results_table)

        # Action controls
        action_group = QGroupBox("Action on Selected Duplicates")
        action_layout = QVBoxLayout(action_group)

        self.action_group = QButtonGroup()
        self.keep_original_radio = QRadioButton("Keep Original (oldest)")
        self.keep_original_radio.setChecked(True)
        self.action_group.addButton(self.keep_original_radio, 0)
        action_layout.addWidget(self.keep_original_radio)

        self.move_radio = QRadioButton("Move Duplicates to Folder")
        self.action_group.addButton(self.move_radio, 1)
        action_layout.addWidget(self.move_radio)

        self.delete_radio = QRadioButton("Delete Duplicates (send to trash)")
        self.action_group.addButton(self.delete_radio, 2)
        action_layout.addWidget(self.delete_radio)

        # Move destination
        move_layout = QHBoxLayout()
        self.move_dest_edit = QLineEdit()
        self.move_dest_edit.setPlaceholderText("Destination folder for move...")
        self.move_dest_edit.setEnabled(False)
        move_layout.addWidget(self.move_dest_edit)

        self.move_browse_button = QPushButton("Browse")
        self.move_browse_button.setEnabled(False)
        self.move_browse_button.clicked.connect(self._browse_move_dest)
        move_layout.addWidget(self.move_browse_button)

        action_layout.addLayout(move_layout)

        # Connect radio buttons
        self.move_radio.toggled.connect(self.move_dest_edit.setEnabled)
        self.move_radio.toggled.connect(self.move_browse_button.setEnabled)

        # Apply button
        button_layout = QHBoxLayout()
        self.apply_button = QPushButton("Apply Action to Selected")
        self.apply_button.clicked.connect(self._apply_action)
        self.apply_button.setEnabled(False)
        button_layout.addWidget(self.apply_button)

        self.select_all_button = QPushButton("Select All Duplicates")
        self.select_all_button.clicked.connect(self._select_all_duplicates)
        self.select_all_button.setEnabled(False)
        button_layout.addWidget(self.select_all_button)

        self.export_button = QPushButton("Export to CSV")
        self.export_button.clicked.connect(self._export_to_csv)
        self.export_button.setEnabled(False)
        button_layout.addWidget(self.export_button)

        action_layout.addLayout(button_layout)

        layout.addWidget(action_group)

    def _browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.folder_edit.setText(folder)

    def _browse_move_dest(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.move_dest_edit.setText(folder)

    def _start_scan(self) -> None:
        folder = self.folder_edit.text().strip()
        if not folder:
            QMessageBox.warning(self, "Error", "Please select a folder to scan.")
            return

        folder_path = Path(folder)
        if not folder_path.exists():
            QMessageBox.warning(self, "Error", "Folder does not exist.")
            return

        self.scan_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.results_table.setRowCount(0)
        self.stats_label.setText("Scanning...")

        self._worker = DuplicateScanWorker([folder_path])
        self._worker.finished.connect(self._on_scan_complete)
        self._worker.error.connect(self._on_scan_error)
        self._worker.start()

    def _on_scan_complete(self, duplicates: list[DuplicateGroup]) -> None:
        self._duplicates = duplicates
        self.scan_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        stats = get_duplicate_stats(duplicates)
        self.stats_label.setText(
            f"Found {stats['groups']} duplicate groups "
            f"({stats['files']} files, {stats['wasted_mb']:.1f} MB wasted)"
        )

        self._populate_table(duplicates)

        has_results = len(duplicates) > 0
        self.apply_button.setEnabled(has_results)
        self.select_all_button.setEnabled(has_results)
        self.export_button.setEnabled(has_results)

    def _on_scan_error(self, error_msg: str) -> None:
        self.scan_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.stats_label.setText("Scan failed")
        QMessageBox.warning(self, "Scan Error", f"Scan failed:\n{error_msg}")

    def _populate_table(self, duplicates: list[DuplicateGroup]) -> None:
        self.results_table.setRowCount(0)

        row = 0
        for group_idx, group in enumerate(duplicates):
            for file_path in group.files:
                self.results_table.insertRow(row)

                # Group number
                self.results_table.setItem(row, 0, QTableWidgetItem(str(group_idx + 1)))

                # File name
                self.results_table.setItem(row, 1, QTableWidgetItem(file_path.name))

                # Size
                try:
                    size = file_path.stat().st_size
                    size_str = self._format_size(size)
                except OSError:
                    size_str = "N/A"
                self.results_table.setItem(row, 2, QTableWidgetItem(size_str))

                # Modified date
                try:
                    import datetime
                    mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                    date_str = mtime.strftime("%Y-%m-%d %H:%M")
                except OSError:
                    date_str = "N/A"
                self.results_table.setItem(row, 3, QTableWidgetItem(date_str))

                # Full path
                self.results_table.setItem(row, 4, QTableWidgetItem(str(file_path)))

                # Store path in user data
                self.results_table.item(row, 4).setData(
                    256, file_path  # Qt.ItemDataRole.UserRole
                )

                row += 1

    def _format_size(self, size: int) -> str:
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _select_all_duplicates(self) -> None:
        """Select all duplicate files (not originals)."""
        self.results_table.clearSelection()
        row = 0
        for group in self._duplicates:
            # Skip first file (original), select rest
            row += 1  # Skip original row
            for _ in group.duplicates:
                if row < self.results_table.rowCount():
                    self.results_table.selectRow(row)
                    row += 1
                else:
                    break

    def _apply_action(self) -> None:
        selected = self.results_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Error", "No files selected.")
            return

        action_id = self.action_group.checkedId()

        if action_id == 1:  # Move
            dest = self.move_dest_edit.text().strip()
            if not dest:
                QMessageBox.warning(self, "Error", "Please select a destination folder.")
                return
            dest_path = Path(dest)
            if not dest_path.exists():
                QMessageBox.warning(self, "Error", "Destination folder does not exist.")
                return

        # Confirm action
        file_count = len(selected)
        if action_id == 0:
            msg = f"Keep original and remove {file_count} duplicate(s)?"
        elif action_id == 1:
            msg = f"Move {file_count} duplicate(s) to {dest}?"
        else:
            msg = f"Delete {file_count} duplicate(s)? (sent to trash)"

        reply = QMessageBox.question(
            self,
            "Confirm Action",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Collect selected file paths
        files_to_process = []
        for index in selected:
            item = self.results_table.item(index.row(), 4)
            if item:
                path = item.data(256)
                if path:
                    files_to_process.append(path)

        # Apply action
        processed = 0
        errors = 0

        for file_path in files_to_process:
            try:
                if action_id == 1:  # Move
                    dest_path = Path(self.move_dest_edit.text()) / file_path.name
                    result = execute_operation(
                        FileOperation(
                            action=FileAction.MOVE,
                            source=Path(file_path),
                            destination=dest_path,
                        ),
                        ConflictResolution.OVERWRITE,
                    )
                    if result.success:
                        processed += 1
                    else:
                        logger.error("Failed to move %s: %s", file_path, result.error)
                        errors += 1
                elif action_id == 2:  # Delete
                    result = execute_operation(
                        FileOperation(
                            action=FileAction.DELETE,
                            source=Path(file_path),
                        ),
                        ConflictResolution.OVERWRITE,
                    )
                    if result.success:
                        processed += 1
                    else:
                        logger.error("Failed to delete %s: %s", file_path, result.error)
                        errors += 1
                else:  # Keep original (skip originals)
                    processed += 1
            except Exception as e:
                logger.error("Failed to process %s: %s", file_path, e)
                errors += 1

        QMessageBox.information(
            self,
            "Complete",
            f"Processed {processed} file(s). Errors: {errors}",
        )

        # Re-scan
        self._start_scan()

    def _export_to_csv(self) -> None:
        """Export duplicate results to CSV file."""
        if not self._duplicates:
            QMessageBox.warning(self, "Error", "No duplicates to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to CSV",
            "duplicates.csv",
            "CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            return

        try:
            import csv

            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Group", "File", "Size", "Modified", "Path"])

                group_num = 1
                for group in self._duplicates:
                    # Write original
                    orig = group.original
                    try:
                        size = orig.stat().st_size
                        size_str = self._format_size(size)
                    except OSError:
                        size_str = "N/A"

                    try:
                        import datetime
                        mtime = datetime.datetime.fromtimestamp(orig.stat().st_mtime)
                        date_str = mtime.strftime("%Y-%m-%d %H:%M")
                    except OSError:
                        date_str = "N/A"

                    writer.writerow([group_num, orig.name, size_str, date_str, str(orig)])

                    # Write duplicates
                    for dup in group.duplicates:
                        try:
                            size = dup.stat().st_size
                            size_str = self._format_size(size)
                        except OSError:
                            size_str = "N/A"

                        try:
                            mtime = datetime.datetime.fromtimestamp(dup.stat().st_mtime)
                            date_str = mtime.strftime("%Y-%m-%d %H:%M")
                        except OSError:
                            date_str = "N/A"

                        writer.writerow([group_num, dup.name, size_str, date_str, str(dup)])

                    group_num += 1

            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported {len(self._duplicates)} duplicate groups to:\n{file_path}",
            )

        except Exception as e:
            QMessageBox.warning(self, "Export Error", f"Failed to export: {e}")
