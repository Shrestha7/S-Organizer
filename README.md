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

## Features Guide

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
- `min_size` / `max_size`: Size limits (supports "1MB", "100KB", "1GB")
- `min_age_days` / `max_age_days`: Age limits in days
- `content_keywords`: Search within file contents (PDF, DOCX, XLSX, CSV, TXT, images)

#### Action
- `type`: "move", "copy", "rename", or "delete"
- `destination`: Target path with placeholders (for move/copy)
- `template`: New name template (for rename)

#### Placeholders
- `{name}` - File name without extension
- `{extension}` / `{ext}` - File extension
- `{date}` - Last modified date (YYYY-MM-DD)
- `{year}`, `{month}`, `{day}` - Date components
- `{parent}` - Parent directory name

### Rule Templates

Click the **Templates** button in the Rule Editor to browse pre-built templates:

- **Document Organization** - Sort PDFs, Word docs, spreadsheets
- **Media Sorting** - Organize photos, videos, audio files
- **Archive Management** - Handle old files and backups
- **Development Files** - Sort code, configs, logs

Select a template and click "Use Template" to create a new rule instantly.

### Duplicate Detection

1. Open the **Duplicates** tab
2. Select a folder and click **Scan for Duplicates**
3. Review the results — duplicates are grouped by content hash
4. Choose an action:
   - **Keep Original (oldest)** - Skip the oldest file in each group
   - **Move Duplicates to Folder** - Move duplicate copies to a specified folder
   - **Delete Duplicates** - Send duplicates to trash
5. Click **Apply Action to Selected** or use **Export to CSV** to save results

### Logging

Configure logging in **Settings**:

- **Log Level**: DEBUG, INFO, WARNING, or ERROR
- **Log File**: Path to a log file (leave empty for stdout only)

Logs are automatically rotated (max 5MB, keep 3 backups).

### System Tray

- Double-click the tray icon to show/hide the main window
- Right-click for quick access to:
  - Start/Stop monitoring
  - Settings
  - Quit
- Desktop notifications for file operations (when enabled)

### Auto-Update

1. Go to **Help > Check for Updates**
2. If an update is available, click **Download**
3. Restart the app to apply the update

### History and Undo

- All file operations are logged in the **History** tab
- Click **Undo** to reverse any operation
- History persists across sessions (stored in `history/history.json`)
- Export history to JSON for backup

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
│   ├── resources/      # Icons and assets
│   └── utils/          # Configuration and helpers
├── tests/              # Test suite (43 tests)
├── rules/              # Sample JSON rule files
├── installer/          # Inno Setup installer script
├── docs/               # Documentation
└── main.py             # Entry point
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.
