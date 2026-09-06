"""Rule template browser dialog."""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.rules.templates import (
    get_template_categories,
    get_templates_by_category,
)


class TemplateBrowser(QDialog):
    """Dialog for browsing and selecting rule templates."""

    template_selected = pyqtSignal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rule Templates")
        self.setMinimumSize(600, 400)
        self._selected_template: dict | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Choose a template to create a new rule:")
        header.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(header)

        # Main content
        content_layout = QHBoxLayout()

        # Category list
        self.category_list = QListWidget()
        self.category_list.setMaximumWidth(200)
        self.category_list.currentItemChanged.connect(self._on_category_changed)
        content_layout.addWidget(self.category_list)

        # Template list
        self.template_list = QListWidget()
        self.template_list.currentItemChanged.connect(self._on_template_changed)
        content_layout.addWidget(self.template_list)

        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setContentsMargins(0, 0, 0, 0)

        self.details_title = QLabel()
        self.details_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        details_layout.addWidget(self.details_title)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)

        content_layout.addWidget(details_widget)

        layout.addLayout(content_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self.use_btn = QPushButton("Use Template")
        self.use_btn.setEnabled(False)
        self.use_btn.clicked.connect(self._on_use_template)
        button_layout.addWidget(self.use_btn)

        layout.addLayout(button_layout)

        # Load categories
        self._load_categories()

    def _load_categories(self) -> None:
        categories = get_template_categories()
        for category in categories:
            self.category_list.addItem(QListWidgetItem(category))

    def _on_category_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        """Handle category selection change."""
        if current is None:
            return

        category = current.text()
        self.template_list.clear()

        templates = get_templates_by_category(category)
        for template in templates:
            item = QListWidgetItem(template.name)
            item.setData(256, template)
            self.template_list.addItem(item)

    def _on_template_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        """Handle template selection change."""
        if current is None:
            self._selected_template = None
            self.use_btn.setEnabled(False)
            return

        template = current.data(256)
        self._selected_template = template
        self.use_btn.setEnabled(True)

        # Show details
        self.details_title.setText(template.name)
        details = f"Category: {template.category}\n\n"
        details += f"Description: {template.description}\n\n"
        details += f"Action: {template.rule.action.type.value.title()}\n"
        if template.rule.action.destination:
            details += f"Destination: {template.rule.action.destination}\n"
        if template.rule.action.template:
            details += f"Rename pattern: {template.rule.action.template}\n"
        self.details_text.setText(details)

    def _on_use_template(self) -> None:
        if self._selected_template:
            self.template_selected.emit(self._selected_template)
            self.accept()
