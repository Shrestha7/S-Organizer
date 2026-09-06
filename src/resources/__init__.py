"""Icon resources for S-Organizer."""

from pathlib import Path

from PyQt6.QtGui import QIcon


def get_app_icon() -> QIcon:
    """Get the application icon."""
    icon_path = Path(__file__).parent / "icons" / "app.svg"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def get_tray_icon() -> QIcon:
    """Get the system tray icon."""
    icon_path = Path(__file__).parent / "icons" / "app.svg"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()
