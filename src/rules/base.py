"""Base rule dataclass and rule definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class RuleAction(Enum):
    """Supported rule actions."""

    MOVE = "move"
    COPY = "copy"
    RENAME = "rename"
    DELETE = "delete"


@dataclass
class RuleMatch:
    """Criteria for matching files."""

    extensions: list[str] = field(default_factory=list)
    name_pattern: str = "*"
    min_size: int | None = None  # Bytes
    max_size: int | None = None  # Bytes
    min_age_days: int | None = None
    max_age_days: int | None = None
    content_keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {}
        if self.extensions:
            result["extensions"] = self.extensions
        if self.name_pattern != "*":
            result["name_pattern"] = self.name_pattern
        if self.min_size is not None:
            result["min_size"] = self.min_size
        if self.max_size is not None:
            result["max_size"] = self.max_size
        if self.min_age_days is not None:
            result["min_age_days"] = self.min_age_days
        if self.max_age_days is not None:
            result["max_age_days"] = self.max_age_days
        if self.content_keywords:
            result["content_keywords"] = self.content_keywords
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleMatch:
        """Create from dictionary."""
        return cls(
            extensions=data.get("extensions", []),
            name_pattern=data.get("name_pattern", "*"),
            min_size=data.get("min_size"),
            max_size=data.get("max_size"),
            min_age_days=data.get("min_age_days"),
            max_age_days=data.get("max_age_days"),
            content_keywords=data.get("content_keywords", []),
        )


@dataclass
class RuleTrigger:
    """Defines when a rule should be triggered."""

    folder: str
    recursive: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {"folder": self.folder, "recursive": self.recursive}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleTrigger:
        """Create from dictionary."""
        return cls(folder=data["folder"], recursive=data.get("recursive", False))


@dataclass
class RuleActionConfig:
    """Configuration for the action to take when rule matches."""

    type: RuleAction
    destination: str = ""
    template: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result: dict[str, Any] = {"type": self.type.value}
        if self.destination:
            result["destination"] = self.destination
        if self.template:
            result["template"] = self.template
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RuleActionConfig:
        """Create from dictionary."""
        return cls(
            type=RuleAction(data["type"]),
            destination=data.get("destination", ""),
            template=data.get("template", ""),
        )


@dataclass
class Rule:
    """Represents an organization rule.

    A rule defines:
    - When to trigger (which folder to monitor)
    - What to match (file criteria)
    - What action to take (move/copy/rename/delete)
    """

    name: str
    enabled: bool = True
    trigger: RuleTrigger = field(default_factory=lambda: RuleTrigger(folder=""))
    match: RuleMatch = field(default_factory=RuleMatch)
    action: RuleActionConfig = field(
        default_factory=lambda: RuleActionConfig(type=RuleAction.MOVE)
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "trigger": self.trigger.to_dict(),
            "match": self.match.to_dict(),
            "action": self.action.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            enabled=data.get("enabled", True),
            trigger=RuleTrigger.from_dict(data.get("trigger", {"folder": ""})),
            match=RuleMatch.from_dict(data.get("match", {})),
            action=RuleActionConfig.from_dict(
                data.get("action", {"type": "move"})
            ),
        )

    @classmethod
    def from_json_file(cls, path: Path) -> Rule:
        """Load a rule from a JSON file."""
        import json

        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_json_file(self, path: Path) -> None:
        """Save rule to a JSON file."""
        import json

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
