"""Unit tests for dependency graph module."""

from pathlib import Path

import pytest

from src.graph.dependency_graph import DependencyGraph, build_graph
from src.scanner.models import FileMetadata, RepositoryMetadata


@pytest.fixture
def sample_files():
    """Create sample file metadata for testing."""
    return [
        FileMetadata(
            path="src/main.py",
            language="python",
            loc=50,
            imports=["src.utils", "src.models"],
            sha256="abc123",
        ),
        FileMetadata(
            path="src/utils.py",
            language="python",
            loc=30,
            imports=["src.models"],
            sha256="def456",
        ),
        FileMetadata(
            path="src/models.py",
            language="python",
            loc=40,
            imports=[],
            sha256="ghi789",
        ),
    ]


def test_dependency_graph_initialization(tmp_path):
    """Test graph initialization."""
    graph = DependencyGraph(tmp_path)
    assert graph.repo_root == tmp_path
    assert len(graph.graph.nodes()) == 0


def test_build_graph_adds_nodes(tmp_path, sample_files):
    """Test that building graph adds all files as nodes."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    assert len(graph.graph.nodes()) == 3
    assert "src/main.py" in graph.graph.nodes()
    assert "src/utils.py" in graph.graph.nodes()
    assert "src/models.py" in graph.graph.nodes()


def test_build_graph_adds_edges(tmp_path, sample_files):
    """Test that building graph adds dependency edges."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    # main.py imports utils.py and models.py
    # utils.py imports models.py
    # models.py imports nothing
    assert graph.graph.has_edge("src/main.py", "src/utils.py")
    assert graph.graph.has_edge("src/main.py", "src/models.py")
    assert graph.graph.has_edge("src/utils.py", "src/models.py")


def test_get_dependencies(tmp_path, sample_files):
    """Test getting file dependencies."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    deps = graph.get_dependencies("src/main.py")
    assert len(deps) == 2
    assert "src/utils.py" in deps
    assert "src/models.py" in deps
    
    deps = graph.get_dependencies("src/models.py")
    assert len(deps) == 0


def test_get_dependents(tmp_path, sample_files):
    """Test getting files that depend on a file."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    dependents = graph.get_dependents("src/models.py")
    assert len(dependents) == 2
    assert "src/main.py" in dependents
    assert "src/utils.py" in dependents
    
    dependents = graph.get_dependents("src/main.py")
    assert len(dependents) == 0


def test_get_in_degree(tmp_path, sample_files):
    """Test in-degree calculation."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    # models.py is imported by main.py and utils.py
    assert graph.get_in_degree("src/models.py") == 2
    
    # utils.py is imported by main.py
    assert graph.get_in_degree("src/utils.py") == 1
    
    # main.py is not imported by anyone
    assert graph.get_in_degree("src/main.py") == 0


def test_get_out_degree(tmp_path, sample_files):
    """Test out-degree calculation."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    # main.py imports 2 files
    assert graph.get_out_degree("src/main.py") == 2
    
    # utils.py imports 1 file
    assert graph.get_out_degree("src/utils.py") == 1
    
    # models.py imports nothing
    assert graph.get_out_degree("src/models.py") == 0


def test_has_cycles_no_cycles(tmp_path, sample_files):
    """Test cycle detection with no cycles."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    assert graph.has_cycles() is False


def test_has_cycles_with_cycle(tmp_path):
    """Test cycle detection with circular dependencies."""
    files = [
        FileMetadata(
            path="src/a.py",
            language="python",
            loc=10,
            imports=["src.b"],
            sha256="a",
        ),
        FileMetadata(
            path="src/b.py",
            language="python",
            loc=10,
            imports=["src.a"],
            sha256="b",
        ),
    ]
    
    graph = DependencyGraph(tmp_path)
    graph.build(files)
    
    assert graph.has_cycles() is True
    cycles = graph.get_cycles()
    assert len(cycles) > 0


def test_to_dict(tmp_path, sample_files):
    """Test graph serialization to dictionary."""
    graph = DependencyGraph(tmp_path)
    graph.build(sample_files)
    
    data = graph.to_dict()
    
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 3
    assert len(data["edges"]) == 3


def test_build_graph_helper(tmp_path, sample_files):
    """Test the build_graph helper function."""
    repo_meta = RepositoryMetadata(root_path=str(tmp_path))
    for file in sample_files:
        repo_meta.add_file(file)
    
    graph = build_graph(repo_meta)
    
    assert len(graph.graph.nodes()) == 3
    assert graph.has_cycles() is False

# Made with Bob
