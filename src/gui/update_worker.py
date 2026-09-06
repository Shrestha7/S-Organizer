"""Background workers for update checking and downloading."""

from __future__ import annotations

import logging
import sys
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from src.core.updater import check_for_update

logger = logging.getLogger(__name__)


class UpdateCheckWorker(QThread):
    """Worker thread that checks for updates without blocking the GUI."""

    finished = pyqtSignal(object)  # Emits UpdateInfo
    error = pyqtSignal(str)

    def __init__(self, current_version: str) -> None:
        super().__init__()
        self.current_version = current_version

    def run(self) -> None:
        try:
            info = check_for_update(self.current_version)
            self.finished.emit(info)
        except Exception as e:
            self.error.emit(str(e))


class UpdateDownloadWorker(QThread):
    """Worker thread that downloads the update exe."""

    progress = pyqtSignal(int)  # Percent 0-100
    finished = pyqtSignal(str)  # Path to downloaded file
    error = pyqtSignal(str)

    def __init__(self, url: str, exe_name: str = "S-Organizer.exe") -> None:
        super().__init__()
        self.url = url
        self.exe_name = exe_name

    def run(self) -> None:
        try:
            # Download to temp directory alongside current exe
            if getattr(sys, "frozen", False):
                exe_path = getattr(sys, "executable", None)
                if exe_path:
                    app_dir = Path(exe_path).parent
                else:
                    app_dir = Path.cwd()
            else:
                app_dir = Path.cwd()

            temp_path = app_dir / f"{self.exe_name}.new"

            req = urllib.request.Request(self.url)
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0

                with open(temp_path, "wb") as f:
                    while True:
                        chunk = resp.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(int(downloaded * 100 / total))

            self.finished.emit(str(temp_path))

        except Exception as e:
            logger.exception("Failed to download update")
            self.error.emit(str(e))


def get_app_dir() -> Path:
    """Get the application directory reliably."""
    if getattr(sys, "frozen", False):
        exe = getattr(sys, "executable", None)
        if exe:
            return Path(exe).parent
    return Path.cwd()


def create_update_script(new_exe_path: str) -> str:
    """Create a batch script to replace the exe after app exits.

    Args:
        new_exe_path: Path to the new exe file.

    Returns:
        Path to the created batch script.
    """
    new_exe = Path(new_exe_path).resolve()
    app_dir = new_exe.parent
    target_exe = app_dir / "S-Organizer.exe"

    script_path = app_dir / "_update.bat"

    script_content = f"""@echo off
cd /d "{app_dir}"
timeout /t 3 /nobreak >nul
taskkill /f /im "S-Organizer.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
del /f /q "{target_exe}" >nul 2>&1
move /y "{new_exe}" "{target_exe}" >nul 2>&1
if exist "{target_exe}" (
    start "" "{target_exe}"
)
del /f /q "%~f0" >nul 2>&1
"""
    script_path.write_text(script_content)
    return str(script_path)
