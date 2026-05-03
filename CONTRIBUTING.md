# Contributing to WatsonOnboard

Thank you for your interest in contributing to WatsonOnboard! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to uphold this code. Please be respectful and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/watson-onboard.git
   cd watson-onboard
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/original/watson-onboard.git
   ```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- IBM Watsonx account (for testing)

### Installation

1. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

4. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

### Verify Installation

```bash
# Run tests
pytest

# Check code style
make lint

# Run type checking
make typecheck
```

## Project Structure

```
watson-onboard/
├── src/
│   ├── scanner/        # Repository scanning and parsing
│   ├── graph/          # Dependency graph analysis
│   ├── watsonx/        # IBM Watsonx integration
│   ├── report/         # Report generation
│   ├── qa/             # Q&A and vector store
│   ├── api/            # REST API
│   └── cli/            # Command-line interface
├── tests/
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── demo/               # Demo scripts
└── docs/               # Documentation
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### 2. Make Changes

- Write clear, concise code
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Commit Changes

Write clear commit messages:

```bash
git commit -m "feat: add support for TypeScript parsing"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Test additions/updates
- `chore:` - Maintenance tasks

### 4. Keep Your Branch Updated

```bash
git fetch upstream
git rebase upstream/main
```

### 5. Push Changes

```bash
git push origin feature/your-feature-name
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_scanner.py

# Run specific test
pytest tests/unit/test_scanner.py::test_file_walker
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names
- Follow the Arrange-Act-Assert pattern
- Mock external dependencies

Example:

```python
def test_file_walker_filters_ignored_files():
    """Test that FileWalker correctly filters ignored files."""
    # Arrange
    walker = FileWalker()
    
    # Act
    files = walker.walk("/test/path")
    
    # Assert
    assert all(not f.path.endswith(".pyc") for f in files)
```

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 100 characters (not 79)
- **Quotes**: Double quotes for strings
- **Imports**: Organized with `isort`
- **Formatting**: Automated with `black`

### Type Hints

All functions should have type hints:

```python
def process_file(path: str, encoding: str = "utf-8") -> FileInfo:
    """Process a file and return metadata."""
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def calculate_score(items: list[str], weights: dict[str, float]) -> float:
    """Calculate weighted score for items.
    
    Args:
        items: List of item identifiers
        weights: Dictionary mapping items to weights
        
    Returns:
        Calculated weighted score
        
    Raises:
        ValueError: If items list is empty
    """
    ...
```

### Code Quality Tools

```bash
# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run all checks
make check
```

## Submitting Changes

### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new functionality
3. **Ensure all tests pass**: `pytest`
4. **Check code style**: `make lint`
5. **Update CHANGELOG.md** with your changes
6. **Create a pull request** on GitHub

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests pass locally
```

### Review Process

1. Maintainers will review your PR
2. Address any feedback
3. Once approved, your PR will be merged

## Reporting Issues

### Bug Reports

Include:
- **Description**: Clear description of the bug
- **Steps to reproduce**: Detailed steps
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: OS, Python version, etc.
- **Logs**: Relevant error messages or logs

### Feature Requests

Include:
- **Description**: Clear description of the feature
- **Use case**: Why this feature is needed
- **Proposed solution**: How it might work
- **Alternatives**: Other approaches considered

## Development Tips

### Debugging

```bash
# Run with verbose logging
export LOG_LEVEL=DEBUG
python -m src.cli.main analyze /path/to/repo

# Use debugger
python -m pdb -m src.cli.main analyze /path/to/repo
```

### Testing with Real Repositories

```bash
# Use demo scripts
python demo/analyze_sample_repo.py

# Test CLI
watson-onboard analyze /path/to/test/repo --output test_report.md
```

### Working with Watsonx

- Use test credentials for development
- Cache responses to avoid API rate limits
- Mock Watsonx calls in unit tests

## Questions?

- Open an issue for questions
- Check existing issues and PRs
- Review documentation in `/docs`

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to WatsonOnboard! 🎉