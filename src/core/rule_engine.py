"""Rule engine for matching files and executing actions.

This module coordinates between file events, rules, and file operations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.core.file_monitor import FileEvent
from src.core.file_operations import (
    ConflictResolution,
    FileAction,
    FileOperation,
    execute_operation,
    format_destination,
)
from src.rules.base import Rule, RuleAction
from src.rules.matchers import match_file

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a rule on a file."""

    rule_name: str
    file_path: Path
    operation: FileOperation | None = None
    matched: bool = False
    error: str | None = None


class RuleEngine:
    """Processes file events against rules and executes actions.

    The rule engine is the central coordinator that:
    1. Receives file events from the monitor
    2. Checks which rules match the file
    3. Executes the appropriate actions
    4. Returns results for history logging
    """

    def __init__(self) -> None:
        """Initialize the rule engine."""
        self.rules: list[Rule] = []
        self._conflict_resolution = ConflictResolution.RENAME

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine.

        Args:
            rule: Rule to add.
        """
        self.rules.append(rule)
        logger.info("Added rule: %s", rule.name)

    def remove_rule(self, rule_name: str) -> bool:
        """Remove a rule by name.

        Args:
            rule_name: Name of the rule to remove.

        Returns:
            True if rule was found and removed.
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                del self.rules[i]
                logger.info("Removed rule: %s", rule_name)
                return True
        return False

    def get_rule(self, rule_name: str) -> Rule | None:
        """Get a rule by name.

        Args:
            rule_name: Name of the rule to get.

        Returns:
            Rule if found, None otherwise.
        """
        for rule in self.rules:
            if rule.name == rule_name:
                return rule
        return None

    def load_rules_from_directory(self, directory: Path) -> int:
        """Load all JSON rule files from a directory.

        Args:
            directory: Directory containing .json rule files.

        Returns:
            Number of rules loaded.
        """
        count = 0
        if not directory.exists():
            return count

        for json_file in directory.glob("*.json"):
            try:
                rule = Rule.from_json_file(json_file)
                self.add_rule(rule)
                count += 1
            except Exception as e:
                logger.error("Failed to load rule from %s: %s", json_file, e)

        return count

    def save_rules_to_directory(self, directory: Path) -> int:
        """Save all rules to JSON files in a directory.

        Args:
            directory: Directory to save rule files to.

        Returns:
            Number of rules saved.
        """
        directory.mkdir(parents=True, exist_ok=True)

        # Clear existing rule files
        for json_file in directory.glob("*.json"):
            json_file.unlink()

        # Save each rule
        count = 0
        for rule in self.rules:
            try:
                safe_name = rule.name.replace("/", "_").replace("\\", "_")
                json_file = directory / f"{safe_name}.json"
                rule.to_json_file(json_file)
                count += 1
            except Exception as e:
                logger.error("Failed to save rule %s: %s", rule.name, e)

        return count

    def process_event(self, event: FileEvent) -> list[ExecutionResult]:
        """Process a file event against all enabled rules.

        Args:
            event: File event to process.

        Returns:
            List of execution results.
        """
        results = []

        # Only process file events (not directories)
        if event.is_directory:
            return results

        for rule in self.rules:
            if not rule.enabled:
                continue

            result = self._process_rule(rule, event)
            if result is not None:
                results.append(result)

        return results

    def _process_rule(self, rule: Rule, event: FileEvent) -> ExecutionResult | None:
        """Process a single rule against an event.

        Args:
            rule: Rule to check.
            event: File event to process.

        Returns:
            ExecutionResult if rule matched, None otherwise.
        """
        file_path = event.source_path

        # Check if the file is in the rule's trigger folder
        trigger_path = Path(rule.trigger.folder).expanduser().resolve()
        try:
            file_path.relative_to(trigger_path)
        except ValueError:
            # File is not in the trigger folder
            return None

        # Check if the file matches the rule criteria
        if not match_file(file_path, rule.match):
            return None

        # Create and execute the operation
        operation = self._create_operation(rule, file_path)
        if operation is None:
            return ExecutionResult(
                rule_name=rule.name,
                file_path=file_path,
                matched=True,
                error="Invalid action configuration",
            )

        executed_op = execute_operation(operation)

        return ExecutionResult(
            rule_name=rule.name,
            file_path=file_path,
            operation=executed_op,
            matched=True,
            error=executed_op.error,
        )

    def _create_operation(self, rule: Rule, file_path: Path) -> FileOperation | None:
        """Create a FileOperation from a rule.

        Args:
            rule: Rule defining the action.
            file_path: Path to the file to operate on.

        Returns:
            FileOperation to execute, or None if invalid.
        """
        action_type = rule.action.type

        if action_type == RuleAction.DELETE:
            return FileOperation(
                source=file_path,
                action=FileAction.DELETE,
                rule_name=rule.name,
            )

        if action_type == RuleAction.RENAME:
            if not rule.action.template:
                return None
            new_name = format_destination(rule.action.template, file_path)
            return FileOperation(
                source=file_path,
                action=FileAction.RENAME,
                new_name=new_name,
                rule_name=rule.name,
            )

        if action_type in (RuleAction.MOVE, RuleAction.COPY):
            if not rule.action.destination:
                return None

            dest_str = format_destination(rule.action.destination, file_path)
            dest_path = Path(dest_str).expanduser().resolve()

            action = FileAction.MOVE if action_type == RuleAction.MOVE else FileAction.COPY

            return FileOperation(
                source=file_path,
                action=action,
                destination=dest_path,
                conflict_resolution=self._conflict_resolution,
                rule_name=rule.name,
            )

        return None

    def set_conflict_resolution(self, resolution: ConflictResolution) -> None:
        """Set default conflict resolution strategy.

        Args:
            resolution: Conflict resolution strategy.
        """
        self._conflict_resolution = resolution

    def get_matching_rules(self, file_path: Path) -> list[Rule]:
        """Get all rules that would match a given file.

        Useful for previewing what would happen to a file.

        Args:
            file_path: Path to check.

        Returns:
            List of rules that would match.
        """
        matching = []
        for rule in self.rules:
            if not rule.enabled:
                continue
            if match_file(file_path, rule.match):
                matching.append(rule)
        return matching
