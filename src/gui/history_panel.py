"""History panel GUI for viewing and undoing operations."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.file_operations import FileAction
from src.main import FileOrganizer


class HistoryPanel(QWidget):
    """Widget for viewing operation history and undoing actions."""

    def __init__(self, organizer: FileOrganizer) -> None:
        """Initialize the history panel.

        Args:
            organizer: File organizer controller.
        """
        super().__init__()
        self.organizer = organizer
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header
        layout.addWidget(QLabel("Operation History"))

        # Controls
        button_layout = QVBoxLayout()

        self.undo_button = QPushButton("Undo Selected")
        self.undo_button.clicked.connect(self._undo_selected)
        button_layout.addWidget(self.undo_button)

        self.undo_all_button = QPushButton("Undo Last 10")
        self.undo_all_button.clicked.connect(self._undo_last_10)
        button_layout.addWidget(self.undo_all_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)
        button_layout.addWidget(self.refresh_button)

        self.clear_button = QPushButton("Clear History")
        self.clear_button.clicked.connect(self._clear_history)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Time", "Action", "Source", "Destination", "Rule", "Status"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setAlternatingRowColors(True)
        layout.addWidget(self.history_table)

        # Stats
        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        self.refresh()

    def refresh(self) -> None:
        """Refresh the history table."""
        history = self.organizer.history
        entries = history.entries

        self.history_table.setRowCount(len(entries))

        for i, entry in enumerate(reversed(entries)):
            op = entry.operation

            # Time
            time_item = QTableWidgetItem(op.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
            self.history_table.setItem(i, 0, time_item)

            # Action
            action_map = {
                FileAction.MOVE: "Move",
                FileAction.COPY: "Copy",
                FileAction.RENAME: "Rename",
                FileAction.DELETE: "Delete",
            }
            action_item = QTableWidgetItem(action_map.get(op.action, "Unknown"))
            self.history_table.setItem(i, 1, action_item)

            # Source
            source_item = QTableWidgetItem(str(op.source))
            self.history_table.setItem(i, 2, source_item)

            # Destination
            dest_item = QTableWidgetItem(str(op.destination) if op.destination else "")
            self.history_table.setItem(i, 3, dest_item)

            # Rule
            rule_item = QTableWidgetItem(op.rule_name)
            self.history_table.setItem(i, 4, rule_item)

            # Status
            if entry.undone:
                status = "Undone"
            elif op.success:
                status = "Success"
            else:
                status = f"Failed: {op.error}"
            status_item = QTableWidgetItem(status)
            self.history_table.setItem(i, 5, status_item)

            # Gray out undone entries
            if entry.undone:
                for col in range(6):
                    item = self.history_table.item(i, col)
                    if item:
                        item.setForeground(Qt.GlobalColor.gray)

        # Update stats
        stats = history.stats
        self.stats_label.setText(
            f"Total: {stats['total']} | "
            f"Success: {stats['successful']} | "
            f"Failed: {stats['failed']} | "
            f"Undone: {stats['undone']}"
        )

    def _undo_selected(self) -> None:
        """Undo the selected operation."""
        selected = self.history_table.currentRow()
        if selected < 0:
            return

        # Get the actual index (reversed order)
        total = len(self.organizer.history.entries)
        actual_index = total - 1 - selected

        entry = self.organizer.history.undo_entry(actual_index)
        if entry:
            self.refresh()

    def _undo_last_10(self) -> None:
        """Undo the last 10 operations."""
        undone = self.organizer.history.undo_last(10)
        if undone:
            self.refresh()

    def _clear_history(self) -> None:
        """Clear all history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Clear all history? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.organizer.history.clear()
            self.refresh()
