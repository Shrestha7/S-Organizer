"""Tests for config module."""

import tempfile
from pathlib import Path

import pytest

from src.utils.config import AppConfig, load_config, save_config


@pytest.fixture
def temp_config():
    """Create a temporary config file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.json"
        yield config_path


def test_default_config():
    """Test default config values."""
    config = AppConfig()
    assert config.theme == "light"
    assert config.debounce_ms == 500
    assert config.notifications is True


def test_save_and_load(temp_config):
    """Test saving and loading config."""
    config = AppConfig(theme="dark", log_level="DEBUG")
    save_config(config, temp_config)

    loaded = load_config(temp_config)
    assert loaded.theme == "dark"
    assert loaded.log_level == "DEBUG"


def test_load_nonexistent():
    """Test loading from nonexistent file returns default config."""
    config = load_config(Path("/nonexistent/config.json"))
    assert config.theme == "light"
    assert config.debounce_ms == 500


def test_config_serialization():
    """Test config serialization roundtrip."""
    config = AppConfig(
        theme="dark",
        log_level="DEBUG",
        watched_folders=["/test/folder"],
        debounce_ms=1000,
    )
    data = config.to_dict()
    restored = AppConfig.from_dict(data)

    assert restored.theme == "dark"
    assert restored.log_level == "DEBUG"
    assert restored.watched_folders == ["/test/folder"]
    assert restored.debounce_ms == 1000


def test_ensure_directories():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = AppConfig(
            rules_dir="test_rules",
            history_dir="test_history",
        )
        # Mock get_data_dir to return our temp directory
        from unittest.mock import patch
        with patch("src.utils.config.get_data_dir", return_value=Path(tmpdir)):
            from src.utils.config import ensure_directories
            ensure_directories(config)
            assert (Path(tmpdir) / "test_rules").exists()
            assert (Path(tmpdir) / "test_history").exists()
