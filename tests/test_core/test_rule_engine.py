"""Tests for the rule engine."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.core.file_monitor import EventType, FileEvent
from src.core.rule_engine import RuleEngine
from src.rules.base import Rule, RuleAction, RuleActionConfig, RuleMatch, RuleTrigger


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def rule_engine():
    """Create a rule engine with a test rule."""
    engine = RuleEngine()

    rule = Rule(
        name="Move PDFs",
        trigger=RuleTrigger(folder=str(Path.cwd())),
        match=RuleMatch(extensions=[".pdf"]),
        action=RuleActionConfig(
            type=RuleAction.MOVE,
            destination=str(Path.cwd() / "output"),
        ),
    )
    engine.add_rule(rule)

    return engine


class TestRuleEngine:
    """Tests for the rule engine."""

    def test_add_rule(self, rule_engine):
        """Test adding a rule."""
        initial_count = len(rule_engine.rules)

        new_rule = Rule(name="New Rule")
        rule_engine.add_rule(new_rule)

        assert len(rule_engine.rules) == initial_count + 1

    def test_remove_rule(self, rule_engine):
        """Test removing a rule."""
        result = rule_engine.remove_rule("Move PDFs")

        assert result is True
        assert len(rule_engine.rules) == 0

    def test_get_rule(self, rule_engine):
        """Test getting a rule by name."""
        rule = rule_engine.get_rule("Move PDFs")

        assert rule is not None
        assert rule.name == "Move PDFs"

    def test_process_event_no_match(self, rule_engine):
        """Test processing an event that doesn't match any rule."""
        event = FileEvent(
            event_type=EventType.CREATED,
            source_path=Path("test.txt"),
        )

        results = rule_engine.process_event(event)

        # Should not match since we only match .pdf files
        assert len(results) == 0 or all(not r.matched for r in results)

    def test_get_matching_rules(self, rule_engine, temp_dir):
        """Test getting rules that would match a file."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.touch()

        matching = rule_engine.get_matching_rules(pdf_file)

        assert len(matching) > 0
        assert any(r.name == "Move PDFs" for r in matching)
