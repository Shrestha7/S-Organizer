# S-Organizer

Automatic file organization with PyQt6 GUI.

## Features

- **Real-time monitoring** - Watch folders and auto-organize files as they appear
- **Rule-based sorting** - Define rules to move, copy, rename, or delete files
- **Flexible matching** - Match by extension, name pattern, size, age, or content
- **Undo support** - Reverse any file operation from history
- **Duplicate detection** - Find and handle duplicate files
- **JSON rules** - Easy to create, share, and version control rules

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/s-organizer.git
cd s-organizer

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e ".[dev,content]"
```

## Usage

### CLI Mode

```bash
python -m src.main
```

### Python API

```python
from src.main import FileOrganizer

# Initialize the organizer
organizer = FileOrganizer()

# Add a folder to watch
organizer.add_watched_folder("~/Downloads")

# Start monitoring
organizer.start()
```

### Creating Rules

Create a JSON file in the `rules/` directory:

```json
{
  "name": "Move PDFs to Documents",
  "enabled": true,
  "trigger": {
    "folder": "~/Downloads",
    "recursive": false
  },
  "match": {
    "extensions": [".pdf", ".docx"]
  },
  "action": {
    "type": "move",
    "destination": "~/Documents/{extension}/{name}{extension}"
  }
}
```

### Rule Format

#### Trigger
- `folder`: Directory to monitor
- `recursive`: Watch subdirectories (default: false)

#### Match
- `extensions`: List of file extensions (e.g., [".pdf", ".txt"])
- `name_pattern`: Glob pattern (e.g., "*.pdf", "report_*")
- `min_size` / `max_size`: Size limits (e.g., "10MB", "1GB")
- `min_age_days` / `max_age_days`: Age limits
- `content_keywords`: Search within file contents

#### Action
- `type`: "move", "copy", "rename", or "delete"
- `destination`: Target path with placeholders
- `template`: New name template (for rename)

#### Placeholders
- `{name}` - File name without extension
- `{extension}` / `{ext}` - File extension
- `{date}` - Last modified date (YYYY-MM-DD)
- `{year}`, `{month}`, `{day}` - Date components
- `{parent}` - Parent directory name

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src

# Lint
ruff check src/

# Type check
mypy src/
```

## Project Structure

```
s-organizer/
├── src/
│   ├── core/           # File monitoring, rule engine, operations
│   ├── rules/          # Rule definitions and matching
│   ├── gui/            # PyQt6 GUI components
│   └── utils/          # Configuration and helpers
├── tests/              # Test suite
├── rules/              # Sample JSON rule files
├── docs/               # Documentation
└── main.py             # Entry point
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
