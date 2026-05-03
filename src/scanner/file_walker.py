"""File system walker for repository scanning."""

import fnmatch
from pathlib import Path
from typing import Iterator

from src.config import settings

# Default patterns to ignore
DEFAULT_IGNORE_PATTERNS = [
    ".git",
    ".gitignore",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "*.egg-info",
    ".next",
    ".nuxt",
    "target",
    "bin",
    "obj",
    ".idea",
    ".vscode",
    "*.min.js",
    "*.min.css",
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
]

# File extensions to process
SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cs",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".scala",
    ".html",
    ".htm",
    ".css",
    ".vue",
    ".svelte",
}


def should_ignore(path: Path, ignore_patterns: list[str]) -> bool:
    """
    Check if a path should be ignored based on patterns.
    
    Args:
        path: Path to check
        ignore_patterns: List of glob patterns to ignore
        
    Returns:
        True if path should be ignored, False otherwise
    """
    path_str = str(path)
    path_name = path.name
    
    for pattern in ignore_patterns:
        # Check if pattern matches the full path or just the name
        if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_name, pattern):
            return True
        
        # Check if any parent directory matches the pattern
        for parent in path.parents:
            if fnmatch.fnmatch(parent.name, pattern):
                return True
    
    return False


def is_supported_file(path: Path) -> bool:
    """
    Check if a file has a supported extension.
    
    Args:
        path: Path to check
        
    Returns:
        True if file is supported, False otherwise
    """
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def get_file_size_mb(path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        path: Path to file
        
    Returns:
        File size in MB
    """
    try:
        return path.stat().st_size / (1024 * 1024)
    except (OSError, IOError):
        return 0.0


def walk(
    root: Path,
    ignore_patterns: list[str] | None = None,
    max_file_size_mb: int | None = None,
) -> Iterator[Path]:
    """
    Walk through a directory and yield supported source files.
    
    Args:
        root: Root directory to walk
        ignore_patterns: Additional patterns to ignore (merged with defaults)
        max_file_size_mb: Maximum file size in MB (uses config default if None)
        
    Yields:
        Path objects for each supported source file
        
    Raises:
        ValueError: If root path doesn't exist
    """
    if not root.exists():
        raise ValueError(f"Root path does not exist: {root}")
    
    if not root.is_dir():
        raise ValueError(f"Root path is not a directory: {root}")
    
    # Merge ignore patterns
    all_ignore_patterns = DEFAULT_IGNORE_PATTERNS.copy()
    if ignore_patterns:
        all_ignore_patterns.extend(ignore_patterns)
    
    # Use config default if not specified
    if max_file_size_mb is None:
        max_file_size_mb = settings.max_file_size_mb
    
    # Walk the directory tree
    for path in root.rglob("*"):
        # Skip directories
        if path.is_dir():
            continue
        
        # Skip ignored paths
        if should_ignore(path, all_ignore_patterns):
            continue
        
        # Skip unsupported files
        if not is_supported_file(path):
            continue
        
        # Skip files that are too large
        if get_file_size_mb(path) > max_file_size_mb:
            continue
        
        yield path


def count_files(
    root: Path,
    ignore_patterns: list[str] | None = None,
    max_file_size_mb: int | None = None,
) -> int:
    """
    Count the number of supported files in a directory.
    
    Args:
        root: Root directory to walk
        ignore_patterns: Additional patterns to ignore
        max_file_size_mb: Maximum file size in MB
        
    Returns:
        Number of supported files
    """
    return sum(1 for _ in walk(root, ignore_patterns, max_file_size_mb))


def get_relative_path(file_path: Path, root: Path) -> str:
    """
    Get the relative path of a file from the repository root.
    
    Args:
        file_path: Absolute path to file
        root: Repository root path
        
    Returns:
        Relative path as string with forward slashes
    """
    try:
        rel_path = file_path.relative_to(root)
        return str(rel_path).replace("\\", "/")
    except ValueError:
        # If file is not relative to root, return absolute path
        return str(file_path).replace("\\", "/")

# Made with Bob
