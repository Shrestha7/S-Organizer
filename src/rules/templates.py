"""Pre-built rule templates for common organization tasks."""

from __future__ import annotations

from dataclasses import dataclass

from src.rules.base import Rule, RuleAction, RuleActionConfig, RuleMatch, RuleTrigger


@dataclass
class RuleTemplate:
    """A rule template with metadata."""

    name: str
    description: str
    category: str
    rule: Rule


def get_templates() -> list[RuleTemplate]:
    """Get all available rule templates.

    Returns:
        List of rule templates.
    """
    return [
        # Document Organization
        RuleTemplate(
            name="Sort PDFs",
            description="Move PDF files to Documents/PDFs folder",
            category="Documents",
            rule=Rule(
                name="Sort PDFs",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".pdf"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Documents/PDFs/{name}{extension}",
                ),
            ),
        ),
        RuleTemplate(
            name="Sort Word Documents",
            description="Move Word documents to Documents folder",
            category="Documents",
            rule=Rule(
                name="Sort Word Documents",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".docx", ".doc"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Documents/{extension}/{name}{extension}",
                ),
            ),
        ),
        RuleTemplate(
            name="Sort Spreadsheets",
            description="Move spreadsheets to Documents/Spreadsheets",
            category="Documents",
            rule=Rule(
                name="Sort Spreadsheets",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".xlsx", ".xls", ".csv"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Documents/Spreadsheets/{name}{extension}",
                ),
            ),
        ),
        # Media Organization
        RuleTemplate(
            name="Sort Photos by Date",
            description="Move photos to Pictures folder organized by date",
            category="Media",
            rule=Rule(
                name="Sort Photos by Date",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Pictures/{year}/{month}/{name}{extension}",
                ),
            ),
        ),
        RuleTemplate(
            name="Sort Videos",
            description="Move videos to Videos folder",
            category="Media",
            rule=Rule(
                name="Sort Videos",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".mp4", ".avi", ".mkv", ".mov", ".wmv"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Videos/{name}{extension}",
                ),
            ),
        ),
        RuleTemplate(
            name="Sort Music",
            description="Move music files to Music folder",
            category="Media",
            rule=Rule(
                name="Sort Music",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".mp3", ".flac", ".wav", ".aac", ".ogg"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Music/{name}{extension}",
                ),
            ),
        ),
        # Cleanup
        RuleTemplate(
            name="Delete Temp Files",
            description="Delete temporary files older than 7 days",
            category="Cleanup",
            rule=Rule(
                name="Delete Temp Files",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(
                    extensions=[".tmp", ".temp", ".bak"],
                    max_age_days=7,
                ),
                action=RuleActionConfig(type=RuleAction.DELETE),
            ),
        ),
        RuleTemplate(
            name="Delete Old Downloads",
            description="Delete files older than 30 days",
            category="Cleanup",
            rule=Rule(
                name="Delete Old Downloads",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(min_age_days=30),
                action=RuleActionConfig(type=RuleAction.DELETE),
            ),
        ),
        RuleTemplate(
            name="Archive Old Files",
            description="Move files older than 60 days to Archive",
            category="Cleanup",
            rule=Rule(
                name="Archive Old Files",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(min_age_days=60),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Archive/{year}/{month}/{name}{extension}",
                ),
            ),
        ),
        # Development
        RuleTemplate(
            name="Sort Source Code",
            description="Move source code files to Code folder",
            category="Development",
            rule=Rule(
                name="Sort Source Code",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".py", ".js", ".ts", ".java", ".cpp", ".c", ".h"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Code/{extension}/{name}{extension}",
                ),
            ),
        ),
        RuleTemplate(
            name="Sort Archives",
            description="Move archive files to Archives folder",
            category="Development",
            rule=Rule(
                name="Sort Archives",
                trigger=RuleTrigger(folder="~/Downloads"),
                match=RuleMatch(extensions=[".zip", ".rar", ".7z", ".tar", ".gz"]),
                action=RuleActionConfig(
                    type=RuleAction.MOVE,
                    destination="~/Archives/{name}{extension}",
                ),
            ),
        ),
    ]


def get_templates_by_category() -> dict[str, list[RuleTemplate]]:
    """Get templates grouped by category.

    Returns:
        Dictionary mapping category names to template lists.
    """
    templates = get_templates()
    categories: dict[str, list[RuleTemplate]] = {}

    for template in templates:
        if template.category not in categories:
            categories[template.category] = []
        categories[template.category].append(template)

    return categories


def get_template_by_name(name: str) -> RuleTemplate | None:
    """Get a template by name.

    Args:
        name: Template name.

    Returns:
        Template if found, None otherwise.
    """
    for template in get_templates():
        if template.name == name:
            return template
    return None
