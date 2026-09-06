"""Application configuration management.

Handles loading, saving, and default configuration values.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default configuration file name
CONFIG_FILE = "config.json"


@dataclass
class AppConfig:
    """Application configuration.

    Attributes:
        rules_dir: Directory containing rule JSON files.
        history_dir: Directory for history storage.
        watched_folders: List of folders to monitor.
        debounce_ms: Debounce interval for file events.
        auto_start: Start monitoring on app launch.
        minimize_to_tray: Minimize to system tray.
        notifications: Show desktop notifications.
        log_file: Path to log file (empty for stdout only).
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """

    rules_dir: str = "rules"
    history_dir: str = "history"
    watched_folders: list[str] = field(default_factory=list)
    debounce_ms: int = 500
    auto_start: bool = False
    minimize_to_tray: bool = True
    notifications: bool = True
    theme: str = "light"
    window_width: int = 1024
    window_height: int = 768
    log_file: str = ""
    log_level: str = "INFO"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rules_dir": self.rules_dir,
            "history_dir": self.history_dir,
            "watched_folders": self.watched_folders,
            "debounce_ms": self.debounce_ms,
            "auto_start": self.auto_start,
            "minimize_to_tray": self.minimize_to_tray,
            "notifications": self.notifications,
            "theme": self.theme,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "log_file": self.log_file,
            "log_level": self.log_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppConfig:
        """Create from dictionary."""
        return cls(
            rules_dir=data.get("rules_dir", "rules"),
            history_dir=data.get("history_dir", "history"),
            watched_folders=data.get("watched_folders", []),
            debounce_ms=data.get("debounce_ms", 500),
            auto_start=data.get("auto_start", False),
            minimize_to_tray=data.get("minimize_to_tray", True),
            notifications=data.get("notifications", True),
            theme=data.get("theme", "light"),
            window_width=data.get("window_width", 1024),
            window_height=data.get("window_height", 768),
            log_file=data.get("log_file", ""),
            log_level=data.get("log_level", "INFO"),
        )


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to config.json in the app directory.
    """
    return Path(__file__).parent.parent.parent / CONFIG_FILE


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load configuration from file.

    Args:
        config_path: Path to config file. Uses default if None.

    Returns:
        Loaded configuration or default if not found.
    """
    if config_path is None:
        config_path = get_config_path()

    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)
            logger.info("Loaded config from %s", config_path)
            return AppConfig.from_dict(data)
        except Exception as e:
            logger.error("Failed to load config: %s", e)

    return AppConfig()


def save_config(config: AppConfig, config_path: Path | None = None) -> bool:
    """Save configuration to file.

    Args:
        config: Configuration to save.
        config_path: Path to config file. Uses default if None.

    Returns:
        True if saved successfully.
    """
    if config_path is None:
        config_path = get_config_path()

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)
        logger.info("Saved config to %s", config_path)
        return True
    except Exception as e:
        logger.error("Failed to save config: %s", e)
        return False


def get_data_dir() -> Path:
    """Get the application data directory.

    Returns:
        Path to the data directory.
    """
    # Use current working directory for now
    # Could be changed to use platform-specific locations later
    return Path.cwd()


def ensure_directories(config: AppConfig) -> None:
    """Ensure all configured directories exist.

    Args:
        config: Application configuration.
    """
    data_dir = get_data_dir()

    dirs = [
        data_dir / config.rules_dir,
        data_dir / config.history_dir,
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
