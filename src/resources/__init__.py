"""Icon resources for S-Organizer."""

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon


def _get_resource_path(relative: str) -> Path:
    """Get resource path, handling PyInstaller frozen builds."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative
    return Path(__file__).parent / relative


def get_app_icon() -> QIcon:
    """Get the application icon."""
    icon_path = _get_resource_path("icons") / "app.svg"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def get_tray_icon() -> QIcon:
    """Get the system tray icon."""
    icon_path = _get_resource_path("icons") / "app.svg"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()
