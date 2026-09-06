# S-Organizer

Automatic file organization with PyQt6 GUI.

## Features

- **Real-time monitoring** - Watch folders and auto-organize files as they appear
- **Rule-based sorting** - Define rules to move, copy, rename, or delete files
- **Flexible matching** - Match by extension, name pattern, size, age, or content keywords
- **Content-aware sorting** - Search within PDF, DOCX, XLSX, CSV, TXT, and image EXIF data
- **Undo support** - Reverse any file operation from history (persisted across sessions)
- **Duplicate detection** - Find and handle duplicate files with CSV export
- **Rule templates** - Browse pre-built templates when creating new rules
- **JSON rules** - Easy to create, share, and version control rules
- **Dark theme** - Switch between light and dark themes
- **System tray** - Minimize to tray with notifications for file operations
- **One-shot scan** - Scan a folder once without continuous monitoring
- **Log to file** - Configurable file logging with rotation
- **CLI mode** - Command-line interface for headless scanning
- **Auto-update** - Built-in check for updates (Help menu in GUI)
- **Windows Installer** - Proper installer that registers in Control Panel

## Installation

### Option 1: Windows Installer (Recommended)
1. Go to [Releases](https://github.com/Shrestha7/S-Organizer/releases)
2. Download `S-Organizer-0.4.0-Setup.exe`
3. Run the installer — it registers in **Control Panel > Programs and Features** for easy uninstall
4. **Windows Defender Warning**: If you see a false positive warning, click "More info" → "Run anyway" or add an exclusion for the file

### Option 2: Standalone EXE (Windows)
1. Go to [Releases](https://github.com/Shrestha7/S-Organizer/releases)
2. Download `S-Organizer.exe`
3. **Windows Defender Warning**: If you see a false positive warning, click "More info" → "Run anyway" or add an exclusion for the file

### Option 3: Install with pip
```bash
pip install s-organizer
```

### Option 4: From source
```bash
git clone https://github.com/Shrestha7/S-Organizer.git
cd s-organizer
pip install -r requirements.txt
# Or install in development mode
pip install -e ".[dev,content]"
```

## Usage

### GUI Mode (Default)

```bash
python -m src.main
# Or simply double-click the exe/installed shortcut
```

### CLI Mode

```bash
# One-time scan of a folder
python -m src.main --scan ~/Downloads

# Use custom config
python -m src.main --scan ~/Downloads --config my_config.json

# Show version
python -m src.main --version
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
