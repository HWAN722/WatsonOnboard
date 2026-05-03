"""Unit tests for file_walker module."""

from pathlib import Path

import pytest

from src.scanner.file_walker import (
    count_files,
    get_file_size_mb,
    get_relative_path,
    is_supported_file,
    should_ignore,
    walk,
)


def test_should_ignore_patterns():
    """Test that ignore patterns work correctly."""
    path = Path("node_modules/package/index.js")
    assert should_ignore(path, ["node_modules"]) is True
    
    path = Path("src/main.py")
    assert should_ignore(path, ["node_modules"]) is False
    
    path = Path("test.pyc")
    assert should_ignore(path, ["*.pyc"]) is True


def test_is_supported_file():
    """Test file extension support detection."""
    assert is_supported_file(Path("test.py")) is True
    assert is_supported_file(Path("test.js")) is True
    assert is_supported_file(Path("test.ts")) is True
    assert is_supported_file(Path("test.java")) is True
    assert is_supported_file(Path("test.txt")) is False
    assert is_supported_file(Path("README.md")) is False


def test_get_file_size_mb(tmp_path):
    """Test file size calculation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("x" * 1024 * 1024)  # 1 MB
    
    size = get_file_size_mb(test_file)
    assert 0.9 < size < 1.1  # Allow some tolerance


def test_walk_empty_directory(tmp_path):
    """Test walking an empty directory."""
    files = list(walk(tmp_path))
    assert len(files) == 0


def test_walk_with_supported_files(tmp_path):
    """Test walking directory with supported files."""
    # Create test files
    (tmp_path / "test.py").write_text("print('hello')")
    (tmp_path / "test.js").write_text("console.log('hello')")
    (tmp_path / "README.md").write_text("# README")
    
    files = list(walk(tmp_path))
    assert len(files) == 2  # Only .py and .js
    
    file_names = {f.name for f in files}
    assert "test.py" in file_names
    assert "test.js" in file_names
    assert "README.md" not in file_names


def test_walk_ignores_patterns(tmp_path):
    """Test that walk ignores specified patterns."""
    # Create directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('main')")
    
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "package.js").write_text("// package")
    
    files = list(walk(tmp_path))
    assert len(files) == 1
    assert files[0].name == "main.py"


def test_walk_respects_max_file_size(tmp_path):
    """Test that walk respects max file size."""
    # Create a large file
    large_file = tmp_path / "large.py"
    large_file.write_text("x" * (2 * 1024 * 1024))  # 2 MB
    
    # Create a small file
    small_file = tmp_path / "small.py"
    small_file.write_text("print('hello')")
    
    # Walk with 1 MB limit
    files = list(walk(tmp_path, max_file_size_mb=1))
    assert len(files) == 1
    assert files[0].name == "small.py"


def test_walk_nonexistent_directory():
    """Test that walk raises error for nonexistent directory."""
    with pytest.raises(ValueError, match="does not exist"):
        list(walk(Path("/nonexistent/path")))


def test_walk_file_instead_of_directory(tmp_path):
    """Test that walk raises error when given a file instead of directory."""
    test_file = tmp_path / "test.py"
    test_file.write_text("print('hello')")
    
    with pytest.raises(ValueError, match="not a directory"):
        list(walk(test_file))


def test_count_files(tmp_path):
    """Test file counting."""
    (tmp_path / "test1.py").write_text("print('1')")
    (tmp_path / "test2.py").write_text("print('2')")
    (tmp_path / "test.txt").write_text("text")
    
    count = count_files(tmp_path)
    assert count == 2


def test_get_relative_path(tmp_path):
    """Test relative path calculation."""
    file_path = tmp_path / "src" / "main.py"
    rel_path = get_relative_path(file_path, tmp_path)
    
    assert rel_path == "src/main.py"
    assert "\\" not in rel_path  # Should use forward slashes

# Made with Bob
