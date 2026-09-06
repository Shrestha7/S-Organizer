"""Update checker - queries GitHub releases for newer versions."""

from __future__ import annotations

import json
import logging
import sys
import urllib.request
from dataclasses import dataclass

from packaging.version import Version

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/repos/Shrestha7/S-Organizer/releases/latest"
GITHUB_RELEASE_URL = "https://github.com/Shrestha7/S-Organizer/releases/tag/"


@dataclass
class UpdateInfo:
    """Information about an available update."""

    has_update: bool
    current_version: str
    latest_version: str
    download_url: str
    release_notes: str


def is_frozen() -> bool:
    """Check if running as a PyInstaller frozen executable."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def check_for_update(current_version: str) -> UpdateInfo:
    """Check GitHub for a newer release.

    Args:
        current_version: The current app version string (e.g. "0.1.1").

    Returns:
        UpdateInfo with details about the update.
    """
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        latest_tag = data.get("tag_name", "").lstrip("v")
        release_notes = data.get("body", "")[:500]

        current = Version(current_version)
        latest = Version(latest_tag)

        # Find the exe asset for frozen builds
        exe_url = ""
        if is_frozen():
            for asset in data.get("assets", []):
                if asset["name"].endswith(".exe"):
                    exe_url = asset["browser_download_url"]
                    break

        return UpdateInfo(
            has_update=latest > current,
            current_version=current_version,
            latest_version=latest_tag,
            download_url=exe_url,
            release_notes=release_notes,
        )

    except Exception:
        logger.exception("Failed to check for updates")
        return UpdateInfo(
            has_update=False,
            current_version=current_version,
            latest_version=current_version,
            download_url="",
            release_notes="",
        )
