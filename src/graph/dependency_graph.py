"""Build dependency graphs from file metadata."""

import re
from pathlib import Path
from typing import Optional

import networkx as nx

from src.scanner.models import FileMetadata, RepositoryMetadata


class DependencyGraph:
    """Dependency graph for a repository."""

    def __init__(self, repo_root: Path) -> None:
        """
        Initialize the dependency graph.
        
        Args:
            repo_root: Root path of the repository
        """
        self.repo_root = repo_root
        self.graph = nx.DiGraph()
        self._file_map: dict[str, FileMetadata] = {}

    def build(self, files: list[FileMetadata]) -> nx.DiGraph:
        """
        Build dependency graph from file metadata.
        
        Args:
            files: List of file metadata objects
            
        Returns:
            NetworkX directed graph
        """
        # Reset graph
        self.graph.clear()
        self._file_map.clear()

        # Add all files as nodes
        for file_meta in files:
            self.graph.add_node(
                file_meta.path,
                language=file_meta.language,
                loc=file_meta.loc,
                classes=len(file_meta.classes),
                functions=len(file_meta.functions),
            )
            self._file_map[file_meta.path] = file_meta

        # Add edges based on imports
        for file_meta in files:
            self._add_import_edges(file_meta)

        return self.graph

    def _add_import_edges(self, file_meta: FileMetadata) -> None:
        """
        Add edges for import relationships.
        
        Args:
            file_meta: File metadata with imports
        """
        source_path = file_meta.path

        for import_name in file_meta.imports:
            # Try to resolve import to a file in the repository
            target_path = self._resolve_import(import_name, file_meta)
            
            if target_path and target_path in self._file_map:
                # Add edge from source to target (source imports target)
                self.graph.add_edge(source_path, target_path, import_name=import_name)

    def _resolve_import(
        self, import_name: str, source_file: FileMetadata
    ) -> Optional[str]:
        """
        Resolve an import statement to a file path.
        
        Args:
            import_name: Import module name
            source_file: Source file metadata
            
        Returns:
            Resolved file path or None if not found
        """
        if source_file.language == "python":
            return self._resolve_python_import(import_name, source_file)
        elif source_file.language in ["javascript", "typescript"]:
            return self._resolve_js_import(import_name, source_file)
        
        return None

    def _resolve_python_import(
        self, import_name: str, source_file: FileMetadata
    ) -> Optional[str]:
        """
        Resolve Python import to file path.
        
        Args:
            import_name: Python module name (e.g., "src.scanner.models")
            source_file: Source file metadata
            
        Returns:
            Resolved file path or None
        """
        # Skip standard library and third-party imports
        if not import_name or import_name.split(".")[0] in [
            "os", "sys", "re", "json", "pathlib", "typing", "dataclasses",
            "collections", "itertools", "functools", "datetime", "time",
            "math", "random", "hashlib", "logging", "unittest", "pytest",
            "numpy", "pandas", "requests", "flask", "django", "fastapi",
            "sqlalchemy", "pydantic", "click", "typer", "rich", "networkx",
        ]:
            return None
        
        # Convert module name to potential file paths
        parts = import_name.split(".")
        
        # Try as package/__init__.py
        package_path = self.repo_root / Path(*parts) / "__init__.py"
        normalized = str(package_path).replace("\\", "/")
        for file_path in self._file_map.keys():
            if file_path.replace("\\", "/").endswith(normalized.replace(str(self.repo_root).replace("\\", "/") + "/", "")):
                return file_path
        
        # Try as module.py
        if len(parts) > 0:
            module_path = self.repo_root / Path(*parts[:-1]) / f"{parts[-1]}.py"
            normalized = str(module_path).replace("\\", "/")
            for file_path in self._file_map.keys():
                if file_path.replace("\\", "/").endswith(normalized.replace(str(self.repo_root).replace("\\", "/") + "/", "")):
                    return file_path
        
        # Try relative imports from source file directory
        source_dir = Path(source_file.path).parent
        
        # Relative import: from . import x
        if import_name.startswith("."):
            rel_parts = import_name.lstrip(".").split(".")
            if rel_parts and rel_parts[0]:
                rel_path = source_dir / f"{rel_parts[0]}.py"
                normalized = str(rel_path).replace("\\", "/")
                for file_path in self._file_map.keys():
                    if file_path.replace("\\", "/") == normalized:
                        return file_path
        
        return None

    def _resolve_js_import(
        self, import_name: str, source_file: FileMetadata
    ) -> Optional[str]:
        """
        Resolve JavaScript/TypeScript import to file path.
        
        Args:
            import_name: Import path (e.g., "./utils", "../components/Button")
            source_file: Source file metadata
            
        Returns:
            Resolved file path or None
        """
        # Skip node_modules and external packages
        if not import_name.startswith(".") and not import_name.startswith("/"):
            return None
        
        # Handle relative imports
        if import_name.startswith("."):
            source_dir = Path(source_file.path).parent
            
            # Try different extensions
            for ext in [".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"]:
                # Try as file with extension
                file_path = source_dir / f"{import_name}{ext}"
                normalized = str(file_path.resolve()).replace("\\", "/")
                for fp in self._file_map.keys():
                    if fp.replace("\\", "/") == normalized:
                        return fp
                
                # Try as file already with extension
                file_path = source_dir / import_name
                if file_path.suffix == ext:
                    normalized = str(file_path.resolve()).replace("\\", "/")
                    for fp in self._file_map.keys():
                        if fp.replace("\\", "/") == normalized:
                            return fp
                
                # Try as index file
                index_path = source_dir / import_name / f"index{ext}"
                normalized = str(index_path.resolve()).replace("\\", "/")
                for fp in self._file_map.keys():
                    if fp.replace("\\", "/") == normalized:
                        return fp
        
        return None

    def get_dependencies(self, file_path: str) -> list[str]:
        """
        Get all files that a file depends on (imports).
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of file paths that are imported
        """
        if file_path not in self.graph:
            return []
        
        return list(self.graph.successors(file_path))

    def get_dependents(self, file_path: str) -> list[str]:
        """
        Get all files that depend on a file (import it).
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of file paths that import this file
        """
        if file_path not in self.graph:
            return []
        
        return list(self.graph.predecessors(file_path))

    def get_in_degree(self, file_path: str) -> int:
        """
        Get the in-degree of a file (number of files importing it).
        
        Args:
            file_path: Path to the file
            
        Returns:
            In-degree count
        """
        if file_path not in self.graph:
            return 0
        
        return int(self.graph.in_degree(file_path))  # type: ignore

    def get_out_degree(self, file_path: str) -> int:
        """
        Get the out-degree of a file (number of files it imports).
        
        Args:
            file_path: Path to the file
            
        Returns:
            Out-degree count
        """
        if file_path not in self.graph:
            return 0
        
        return int(self.graph.out_degree(file_path))  # type: ignore

    def has_cycles(self) -> bool:
        """
        Check if the graph has circular dependencies.
        
        Returns:
            True if cycles exist, False otherwise
        """
        try:
            cycles = list(nx.simple_cycles(self.graph))
            return len(cycles) > 0
        except Exception:
            return False

    def get_cycles(self) -> list[list[str]]:
        """
        Get all circular dependency cycles.
        
        Returns:
            List of cycles, where each cycle is a list of file paths
        """
        try:
            return list(nx.simple_cycles(self.graph))
        except Exception:
            return []

    def get_strongly_connected_components(self) -> list[set[str]]:
        """
        Get strongly connected components (groups of mutually dependent files).
        
        Returns:
            List of components, where each component is a set of file paths
        """
        return list(nx.strongly_connected_components(self.graph))

    def to_dict(self) -> dict:
        """
        Convert graph to dictionary representation.
        
        Returns:
            Dictionary with nodes and edges
        """
        return {
            "nodes": [
                {
                    "path": node,
                    **self.graph.nodes[node],
                }
                for node in self.graph.nodes()
            ],
            "edges": [
                {
                    "source": source,
                    "target": target,
                    **self.graph.edges[source, target],
                }
                for source, target in self.graph.edges()
            ],
        }


def build_graph(repo_meta: RepositoryMetadata) -> DependencyGraph:
    """
    Build dependency graph from repository metadata.
    
    Args:
        repo_meta: Repository metadata
        
    Returns:
        DependencyGraph instance
    """
    graph = DependencyGraph(Path(repo_meta.root_path))
    graph.build(repo_meta.files)
    return graph

# Made with Bob
