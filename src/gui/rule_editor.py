"""Rule editor GUI for creating and managing rules."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from src.gui.template_browser import TemplateBrowser
from src.main import FileOrganizer
from src.rules.base import Rule, RuleAction, RuleActionConfig, RuleMatch, RuleTrigger
from src.rules.matchers import parse_size


class RuleEditor(QWidget):
    """Widget for creating and managing organization rules."""

    rules_changed = pyqtSignal()

    def __init__(self, organizer: FileOrganizer) -> None:
        """Initialize the rule editor.

        Args:
            organizer: File organizer controller.
        """
        super().__init__()
        self.organizer = organizer
        self._setup_ui()
        self._load_rules()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QHBoxLayout(self)

        # Splitter for list and editor
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left panel: Rule list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("Rules"))

        self.rule_list = QListWidget()
        self.rule_list.currentItemChanged.connect(self._on_rule_selected)
        left_layout.addWidget(self.rule_list)

        # Buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add")
        self.add_button.clicked.connect(self._add_rule)
        button_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._remove_rule)
        button_layout.addWidget(self.remove_button)

        self.duplicate_button = QPushButton("Duplicate")
        self.duplicate_button.clicked.connect(self._duplicate_rule)
        button_layout.addWidget(self.duplicate_button)

        self.template_button = QPushButton("Templates")
        self.template_button.clicked.connect(self._open_templates)
        button_layout.addWidget(self.template_button)

        left_layout.addLayout(button_layout)

        # Right panel: Rule editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Rule name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        right_layout.addLayout(name_layout)

        # Enabled checkbox
        self.enabled_checkbox = QCheckBox("Enabled")
        self.enabled_checkbox.setChecked(True)
        right_layout.addWidget(self.enabled_checkbox)

        # Trigger group
        trigger_group = QGroupBox("Trigger")
        trigger_layout = QFormLayout(trigger_group)

        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("~/Downloads")
        trigger_layout.addRow("Folder:", self.folder_edit)

        self.browse_folder_button = QPushButton("Browse...")
        self.browse_folder_button.clicked.connect(self._browse_folder)
        trigger_layout.addRow("", self.browse_folder_button)

        self.recursive_checkbox = QCheckBox("Watch subdirectories")
        trigger_layout.addRow("", self.recursive_checkbox)

        right_layout.addWidget(trigger_group)

        # Match group
        match_group = QGroupBox("Match")
        match_layout = QFormLayout(match_group)

        self.extensions_edit = QLineEdit()
        self.extensions_edit.setPlaceholderText(".pdf, .docx, .txt")
        match_layout.addRow("Extensions:", self.extensions_edit)

        self.name_pattern_edit = QLineEdit()
        self.name_pattern_edit.setPlaceholderText("*")
        match_layout.addRow("Name pattern:", self.name_pattern_edit)

        self.min_size_edit = QLineEdit()
        self.min_size_edit.setPlaceholderText("1KB")
        match_layout.addRow("Min size:", self.min_size_edit)

        self.max_size_edit = QLineEdit()
        self.max_size_edit.setPlaceholderText("100MB")
        match_layout.addRow("Max size:", self.max_size_edit)

        self.min_age_edit = QLineEdit()
        self.min_age_edit.setPlaceholderText("e.g. 7")
        match_layout.addRow("Min age (days):", self.min_age_edit)

        self.max_age_edit = QLineEdit()
        self.max_age_edit.setPlaceholderText("e.g. 30")
        match_layout.addRow("Max age (days):", self.max_age_edit)

        self.content_keywords_edit = QLineEdit()
        self.content_keywords_edit.setPlaceholderText("invoice, report, confidential")
        match_layout.addRow("Content keywords:", self.content_keywords_edit)

        right_layout.addWidget(match_group)

        # Action group
        action_group = QGroupBox("Action")
        action_layout = QVBoxLayout(action_group)

        # Action type
        action_type_layout = QHBoxLayout()
        self.action_group = QButtonGroup()

        self.move_radio = QRadioButton("Move")
        self.move_radio.setChecked(True)
        self.action_group.addButton(self.move_radio, 0)
        action_type_layout.addWidget(self.move_radio)

        self.copy_radio = QRadioButton("Copy")
        self.action_group.addButton(self.copy_radio, 1)
        action_type_layout.addWidget(self.copy_radio)

        self.rename_radio = QRadioButton("Rename")
        self.action_group.addButton(self.rename_radio, 2)
        action_type_layout.addWidget(self.rename_radio)

        self.delete_radio = QRadioButton("Delete")
        self.action_group.addButton(self.delete_radio, 3)
        action_type_layout.addWidget(self.delete_radio)

        action_layout.addLayout(action_type_layout)

        # Destination
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("Destination:"))
        self.destination_edit = QLineEdit()
        self.destination_edit.setPlaceholderText("~/Documents/{extension}/{name}{extension}")
        dest_layout.addWidget(self.destination_edit)
        action_layout.addLayout(dest_layout)

        right_layout.addWidget(action_group)

        # Save button
        self.save_button = QPushButton("Save Rule")
        self.save_button.clicked.connect(self._save_rule)
        right_layout.addWidget(self.save_button)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])

        # Current rule reference
        self._current_rule: Rule | None = None

    def _load_rules(self) -> None:
        """Load rules into the list."""
        self.rule_list.clear()
        for rule in self.organizer.rule_engine.rules:
            item = QListWidgetItem(rule.name)
            item.setData(Qt.ItemDataRole.UserRole, rule)
            if not rule.enabled:
                item.setForeground(Qt.GlobalColor.gray)
            self.rule_list.addItem(item)

    def _on_rule_selected(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        """Handle rule selection."""
        if current is None:
            return

        rule = current.data(Qt.ItemDataRole.UserRole)
        if rule:
            self._load_rule(rule)

    def _load_rule(self, rule: Rule) -> None:
        """Load a rule into the editor."""
        self._current_rule = rule

        self.name_edit.setText(rule.name)
        self.enabled_checkbox.setChecked(rule.enabled)
        self.folder_edit.setText(rule.trigger.folder)
        self.recursive_checkbox.setChecked(rule.trigger.recursive)

        # Extensions
        self.extensions_edit.setText(", ".join(rule.match.extensions))

        self.name_pattern_edit.setText(rule.match.name_pattern)
        self.min_size_edit.setText(self._format_size(rule.match.min_size))
        self.max_size_edit.setText(self._format_size(rule.match.max_size))
        self.min_age_edit.setText(str(rule.match.min_age_days) if rule.match.min_age_days else "")
        self.max_age_edit.setText(str(rule.match.max_age_days) if rule.match.max_age_days else "")
        keywords = rule.match.content_keywords
        self.content_keywords_edit.setText(", ".join(keywords) if keywords else "")

        # Action type
        action_type = rule.action.type
        if action_type == RuleAction.MOVE:
            self.move_radio.setChecked(True)
        elif action_type == RuleAction.COPY:
            self.copy_radio.setChecked(True)
        elif action_type == RuleAction.RENAME:
            self.rename_radio.setChecked(True)
        elif action_type == RuleAction.DELETE:
            self.delete_radio.setChecked(True)

        # Load destination or template based on action type
        if action_type == RuleAction.RENAME:
            self.destination_edit.setText(rule.action.template)
        else:
            self.destination_edit.setText(rule.action.destination)

    def _save_rule(self) -> None:
        """Save the current rule."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Rule name is required.")
            return

        # Parse extensions
        extensions_text = self.extensions_edit.text().strip()
        extensions = [ext.strip() for ext in extensions_text.split(",") if ext.strip()]

        # Parse size (supports human-readable like "1MB", "100KB")
        min_size = parse_size(self.min_size_edit.text()) if self.min_size_edit.text() else None
        max_size = parse_size(self.max_size_edit.text()) if self.max_size_edit.text() else None

        # Parse age
        min_age = int(self.min_age_edit.text()) if self.min_age_edit.text() else None
        max_age = int(self.max_age_edit.text()) if self.max_age_edit.text() else None

        # Parse content keywords
        keywords_text = self.content_keywords_edit.text().strip()
        content_keywords = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]

        # Determine action type
        action_id = self.action_group.checkedId()
        action_types = {
            0: RuleAction.MOVE,
            1: RuleAction.COPY,
            2: RuleAction.RENAME,
            3: RuleAction.DELETE,
        }

        action_type = action_types.get(action_id, RuleAction.MOVE)
        dest_text = self.destination_edit.text()

        # Set destination or template based on action type
        if action_type == RuleAction.RENAME:
            action_config = RuleActionConfig(type=action_type, template=dest_text)
        else:
            action_config = RuleActionConfig(type=action_type, destination=dest_text)

        # Create rule
        rule = Rule(
            name=name,
            enabled=self.enabled_checkbox.isChecked(),
            trigger=RuleTrigger(
                folder=self.folder_edit.text(),
                recursive=self.recursive_checkbox.isChecked(),
            ),
            match=RuleMatch(
                extensions=extensions,
                name_pattern=self.name_pattern_edit.text() or "*",
                min_size=min_size,
                max_size=max_size,
                min_age_days=min_age,
                max_age_days=max_age,
                content_keywords=content_keywords,
            ),
            action=action_config,
        )

        # Update or add
        if self._current_rule:
            # Remove old rule and add new one
            self.organizer.rule_engine.remove_rule(self._current_rule.name)

        self.organizer.rule_engine.add_rule(rule)
        self.organizer.save_rules()
        self._load_rules()
        self.rules_changed.emit()

        # Select the saved rule
        for i in range(self.rule_list.count()):
            item = self.rule_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole).name == name:
                self.rule_list.setCurrentItem(item)
                break

    def _add_rule(self) -> None:
        """Add a new rule."""
        name, ok = QInputDialog.getText(self, "New Rule", "Rule name:")
        if ok and name:
            rule = Rule(name=name)
            self.organizer.rule_engine.add_rule(rule)
            self.organizer.save_rules()
            self._load_rules()
            self.rules_changed.emit()

    def _remove_rule(self) -> None:
        """Remove the selected rule."""
        current = self.rule_list.currentItem()
        if not current:
            return

        rule = current.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(
            self,
            "Remove Rule",
            f"Remove rule '{rule.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.organizer.rule_engine.remove_rule(rule.name)
            self.organizer.save_rules()
            self._load_rules()
            self.rules_changed.emit()
            self._current_rule = None

    def _duplicate_rule(self) -> None:
        """Duplicate the selected rule."""
        current = self.rule_list.currentItem()
        if not current:
            return

        rule = current.data(Qt.ItemDataRole.UserRole)
        new_rule = Rule(
            name=f"{rule.name} (Copy)",
            enabled=rule.enabled,
            trigger=RuleTrigger(
                folder=rule.trigger.folder,
                recursive=rule.trigger.recursive,
            ),
            match=RuleMatch(
                extensions=rule.match.extensions.copy(),
                name_pattern=rule.match.name_pattern,
                min_size=rule.match.min_size,
                max_size=rule.match.max_size,
                min_age_days=rule.match.min_age_days,
                max_age_days=rule.match.max_age_days,
                content_keywords=(
                    rule.match.content_keywords.copy()
                    if rule.match.content_keywords else []
                ),
            ),
            action=RuleActionConfig(
                type=rule.action.type,
                destination=rule.action.destination,
                template=rule.action.template,
            ),
        )

        self.organizer.rule_engine.add_rule(new_rule)
        self.organizer.save_rules()
        self._load_rules()
        self.rules_changed.emit()

    def _open_templates(self) -> None:
        """Open the template browser dialog."""
        dialog = TemplateBrowser(self)
        dialog.template_selected.connect(self._apply_template)
        dialog.exec()

    def _apply_template(self, template: object) -> None:
        """Apply a template to create a new rule."""
        import copy

        from src.rules.templates import RuleTemplate
        if not isinstance(template, RuleTemplate):
            return
        rule = copy.deepcopy(template.rule)

        # Generate unique name
        base_name = rule.name
        counter = 1
        while self.organizer.rule_engine.get_rule(rule.name):
            rule.name = f"{base_name} ({counter})"
            counter += 1

        self.organizer.rule_engine.add_rule(rule)
        self.organizer.save_rules()
        self._load_rules()
        self.rules_changed.emit()

        # Select the new rule
        for i in range(self.rule_list.count()):
            item = self.rule_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole).name == rule.name:
                self.rule_list.setCurrentItem(item)
                break

    def _browse_folder(self) -> None:
        """Browse for a folder."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_edit.setText(folder)

    def _format_size(self, size_bytes: int | None) -> str:
        """Format size in bytes to human-readable string."""
        if size_bytes is None:
            return ""
        size = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def refresh(self) -> None:
        """Refresh the rule list."""
        self._load_rules()
