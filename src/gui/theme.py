"""Theme management for the application."""

from __future__ import annotations

from PyQt6.QtWidgets import QApplication

DARK_STYLESHEET = """
QMainWindow, QDialog {
    background-color: #2b2b2b;
    color: #ffffff;
}

QWidget {
    background-color: #2b2b2b;
    color: #ffffff;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #2b2b2b;
}

QTabBar::tab {
    background-color: #3c3c3c;
    color: #ffffff;
    padding: 8px 16px;
    border: 1px solid #3c3c3c;
    border-bottom: none;
}

QTabBar::tab:selected {
    background-color: #4a4a4a;
    border-bottom: 2px solid #0078d4;
}

QTabBar::tab:hover {
    background-color: #4a4a4a;
}

QPushButton {
    background-color: #0078d4;
    color: #ffffff;
    border: none;
    padding: 6px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #1a8adb;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #3c3c3c;
    color: #808080;
}

QLineEdit, QSpinBox, QComboBox {
    background-color: #3c3c3c;
    color: #ffffff;
    border: 1px solid #555555;
    padding: 4px 8px;
    border-radius: 4px;
}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #0078d4;
}

QTableWidget {
    background-color: #1e1e1e;
    alternate-background-color: #2b2b2b;
    color: #ffffff;
    gridline-color: #3c3c3c;
    selection-background-color: #0078d4;
    border: 1px solid #3c3c3c;
}

QTableWidget::item {
    padding: 4px;
}

QHeaderView::section {
    background-color: #3c3c3c;
    color: #ffffff;
    padding: 6px;
    border: 1px solid #555555;
}

QListWidget {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3c3c3c;
}

QListWidget::item:selected {
    background-color: #0078d4;
}

QGroupBox {
    border: 1px solid #3c3c3c;
    margin-top: 8px;
    padding-top: 8px;
    color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}

QCheckBox, QRadioButton {
    color: #ffffff;
    spacing: 8px;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px;
    height: 16px;
}

QProgressBar {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    text-align: center;
    background-color: #1e1e1e;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 4px;
}

QStatusBar {
    background-color: #1e1e1e;
    color: #ffffff;
}

QMenuBar {
    background-color: #2b2b2b;
    color: #ffffff;
}

QMenuBar::item:selected {
    background-color: #4a4a4a;
}

QMenu {
    background-color: #2b2b2b;
    color: #ffffff;
    border: 1px solid #3c3c3c;
}

QMenu::item:selected {
    background-color: #0078d4;
}

QScrollBar:vertical {
    background-color: #2b2b2b;
    width: 12px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #777777;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #2b2b2b;
    height: 12px;
    border: none;
}

QScrollBar::handle:horizontal {
    background-color: #555555;
    border-radius: 6px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #777777;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

QLabel {
    color: #ffffff;
}

QSplitter::handle {
    background-color: #3c3c3c;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}
"""


def apply_theme(theme: str) -> None:
    """Apply the specified theme to the application.

    Args:
        theme: Theme name ('light' or 'dark').
    """
    app = QApplication.instance()
    if app is None:
        return

    if theme == "dark":
        app.setStyleSheet(DARK_STYLESHEET)
    else:
        app.setStyleSheet("")
