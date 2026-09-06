"""Tests for rule matching."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.rules.base import Rule, RuleAction, RuleActionConfig, RuleMatch, RuleTrigger
from src.rules.matchers import (
    matches_age,
    matches_extensions,
    matches_keywords,
    matches_name_pattern,
    matches_size,
    parse_size,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_files(temp_dir):
    """Create test files with various properties."""
    files = {}

    # PDF file
    files["pdf"] = temp_dir / "document.pdf"
    files["pdf"].write_text("Test PDF content")

    # Text file
    files["txt"] = temp_dir / "notes.txt"
    files["txt"].write_text("Hello world")

    # Image file
    files["jpg"] = temp_dir / "photo.jpg"
    files["jpg"].write_bytes(b"\xff\xd8\xff\xe0")  # JPEG header

    # Large file
    files["large"] = temp_dir / "large.bin"
    files["large"].write_bytes(b"x" * (10 * 1024 * 1024))  # 10MB

    return files


class TestMatchers:
    """Tests for file matching functions."""

    def test_matches_extensions(self, test_files):
        """Test extension matching."""
        assert matches_extensions(test_files["pdf"], [".pdf", ".docx"])
        assert not matches_extensions(test_files["pdf"], [".txt", ".jpg"])
        assert matches_extensions(test_files["txt"], [])  # Empty = match all

    def test_matches_name_pattern(self, test_files):
        """Test name pattern matching."""
        assert matches_name_pattern(test_files["pdf"], "*.pdf")
        assert matches_name_pattern(test_files["txt"], "*.txt")
        assert not matches_name_pattern(test_files["pdf"], "*.jpg")
        assert matches_name_pattern(test_files["pdf"], "*")  # Wildcard matches all

    def test_matches_size(self, test_files):
        """Test size matching."""
        small_file = test_files["txt"]
        large_file = test_files["large"]

        assert matches_size(small_file, max_size=1024)
        assert not matches_size(large_file, max_size=1024)
        assert matches_size(large_file, min_size=1024)

    def test_parse_size(self):
        """Test size string parsing."""
        assert parse_size("100B") == 100
        assert parse_size("1KB") == 1024
        assert parse_size("1MB") == 1024**2
        assert parse_size("1GB") == 1024**3
        assert parse_size("10MB") == 10 * 1024**2

    def test_parse_size_with_spaces(self):
        """Test size parsing with spaces."""
        assert parse_size(" 1 KB ") == 1024
        assert parse_size("10 MB") == 10 * 1024**2

    def test_matches_age(self, test_files):
        """Test age matching."""
        # All files are new, so they should match min_age=0
        assert matches_age(test_files["txt"], min_age_days=0)
        # They should not match min_age=100 (100 days old)
        assert not matches_age(test_files["txt"], min_age_days=100)
        # max_age=100 should match (files are new)
        assert matches_age(test_files["txt"], max_age_days=100)

    def test_matches_keywords(self, test_files):
        """Test keyword matching."""
        # File contains "Hello world"
        assert matches_keywords(test_files["txt"], ["Hello"])
        assert matches_keywords(test_files["txt"], ["hello"])  # Case-insensitive
        assert not matches_keywords(test_files["txt"], ["Nonexistent"])
        assert matches_keywords(test_files["txt"], [])  # Empty = match all

    def test_match_file_composite(self, test_files):
        """Test composite file matching with multiple criteria."""
        from src.rules.base import RuleMatch

        # Should match - all criteria satisfied
        match_config = RuleMatch(
            extensions=[".txt"],
            name_pattern="*.txt",
            max_size=1024,
        )
        assert matches_name_pattern(test_files["txt"], match_config.name_pattern)
        assert matches_extensions(test_files["txt"], match_config.extensions)
        assert matches_size(test_files["txt"], max_size=match_config.max_size)

        # Should not match - wrong extension
        match_config2 = RuleMatch(extensions=[".pdf"])
        assert not matches_extensions(test_files["txt"], match_config2.extensions)


class TestRuleMatch:
    """Tests for RuleMatch configuration."""

    def test_rule_match_creation(self):
        """Test creating a RuleMatch."""
        match = RuleMatch(
            extensions=[".pdf", ".txt"],
            name_pattern="*",
            min_size=1024,
        )

        assert match.extensions == [".pdf", ".txt"]
        assert match.min_size == 1024

    def test_rule_match_serialization(self):
        """Test RuleMatch serialization."""
        match = RuleMatch(
            extensions=[".pdf"],
            min_size=1024,
        )

        data = match.to_dict()
        restored = RuleMatch.from_dict(data)

        assert restored.extensions == [".pdf"]
        assert restored.min_size == 1024


class TestRule:
    """Tests for Rule configuration."""

    def test_rule_creation(self):
        """Test creating a Rule."""
        rule = Rule(
            name="Test Rule",
            trigger=RuleTrigger(folder="/tmp"),
            match=RuleMatch(extensions=[".pdf"]),
            action=RuleActionConfig(type=RuleAction.MOVE, destination="/dest"),
        )

        assert rule.name == "Test Rule"
        assert rule.enabled is True

    def test_rule_serialization(self):
        """Test Rule serialization."""
        rule = Rule(
            name="Test Rule",
            trigger=RuleTrigger(folder="/tmp"),
            match=RuleMatch(extensions=[".pdf"]),
            action=RuleActionConfig(type=RuleAction.MOVE, destination="/dest"),
        )

        data = rule.to_dict()
        restored = Rule.from_dict(data)

        assert restored.name == "Test Rule"
        assert restored.match.extensions == [".pdf"]
