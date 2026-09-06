# AGENTS.md

## Project Overview

S-Organizer - Python-based automatic file organizer with a GUI. Reference implementation: [FileJuggler](https://www.filejuggler.com/features/).

## Tech Stack

- **Language:** Python 3.10+
- **GUI:** PyQt6
- **File monitoring:** watchdog library for filesystem events
- **License:** Apache 2.0

## Core Features (from FileJuggler reference)

1. **Move/copy files** — monitor folders, auto-organize by rules (extension, name pattern, date, size)
2. **Rename files** — rule-based renaming using file metadata or content
3. **Delete files** — auto-delete by age, pattern, or condition
4. **Content-aware sorting** — extract keywords/dates from document contents (PDF, DOCX, TXT)
5. **History & undo** — log all operations, reverse any action
6. **Duplicate detection** — find and handle duplicate files

## Project Structure

```
s-organizer/
├── src/
│   ├── core/          # File monitoring, rule engine, file operations
│   ├── gui/           # PyQt6 GUI components
│   ├── rules/         # Rule definitions and matching logic
│   └── utils/         # Helpers (config, file metadata)
├── tests/
├── rules/             # Sample JSON rule files
├── docs/
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Development

- Run: `python -m src.main`
- Tests: `pytest tests/`
- Lint: `ruff check src/`
- Type check: `mypy src/`

## Conventions

- Use type hints on all functions
- One class per file for GUI widgets
- Rules are dataclasses with JSON serialization
- All file operations go through `src/core/file_operations.py` (never direct `os.rename` / `shutil.move` elsewhere)
- Cross-platform: use `pathlib.Path` over `os.path`
- Use `send2trash` for deletions (never permanent delete)

## Rule Format

JSON files in `rules/` directory:
```json
{
  "name": "Rule Name",
  "enabled": true,
  "trigger": { "folder": "~/Downloads", "recursive": false },
  "match": { "extensions": [".pdf"], "min_size": "1MB" },
  "action": { "type": "move", "destination": "~/Documents/{extension}" }
}
```

Supported placeholders: `{name}`, `{extension}`, `{ext}`, `{date}`, `{year}`, `{month}`, `{day}`, `{parent}`

## Key Files

- `src/core/file_operations.py` — All file ops (move/copy/rename/delete)
- `src/core/file_monitor.py` — Watchdog integration with debouncing
- `src/core/rule_engine.py` — Coordinates rules with file events
- `src/rules/matchers.py` — File matching logic
- `src/utils/config.py` — App configuration
