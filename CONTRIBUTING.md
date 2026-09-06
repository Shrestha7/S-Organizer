# Contributing to S-Organizer

Thank you for your interest in contributing to S-Organizer! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/Shrestha7/S-Organizer.git
   cd s-organizer
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e ".[dev,content]"
   ```

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding conventions below
   - Add tests for new functionality
   - Update documentation if needed

3. **Run tests and linting**
   ```bash
   pytest tests/ -v
   ruff check src/ tests/
   mypy src/ --ignore-missing-imports
   ```

4. **Commit your changes**
   ```bash
   git commit -m "feat: add new feature description"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## Coding Conventions

- **Type hints**: Use type hints on all functions
- **Docstrings**: Use Google-style docstrings
- **Imports**: Sort imports with ruff
- **Line length**: Maximum 100 characters
- **File structure**: One class per file for GUI widgets

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

## Pull Request Guidelines

- Fill out the PR template completely
- Include screenshots for UI changes
- Link related issues
- Keep PRs focused on a single change
- Ensure all tests pass

## Reporting Issues

- Use the GitHub issue tracker
- Include steps to reproduce
- Include expected vs actual behavior
- Include Python version and OS

## Code of Conduct

Be respectful and inclusive. We welcome contributions from everyone.

## Questions?

Feel free to open an issue for any questions about contributing!
