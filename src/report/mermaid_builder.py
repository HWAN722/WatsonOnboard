"""Build Mermaid diagrams from dependency graphs."""

from collections import defaultdict
from pathlib import Path
from typing import Optional

import networkx as nx

from src.graph.dependency_graph import DependencyGraph


class MermaidBuilder:
    """Build Mermaid diagrams for architecture visualization."""

    def __init__(self, graph: DependencyGraph, max_nodes: int = 30) -> None:
        """
        Initialize the Mermaid builder.
        
        Args:
            graph: Dependency graph
            max_nodes: Maximum nodes to include in diagram
        """
        self.graph = graph
        self.max_nodes = max_nodes

    def build_architecture_diagram(self) -> str:
        """
        Build a Mermaid flowchart showing architecture.
        
        Returns:
            Mermaid diagram as string
        """
        if not self.graph.graph.nodes():
            return "graph TD\n    A[No files found]"

        # Get most important nodes
        important_nodes = self._get_important_nodes()

        # Group by directory
        node_groups = self._group_by_directory(important_nodes)

        # Build diagram
        lines = ["graph TD"]

        # Add nodes with styling
        node_ids = {}
        node_counter = 0

        for group_name, nodes in node_groups.items():
            # Add subgraph for each directory
            if len(node_groups) > 1:
                lines.append(f"    subgraph {self._sanitize_id(group_name)}")

            for node in nodes:
                node_id = f"N{node_counter}"
                node_ids[node] = node_id
                node_counter += 1

                # Get file name
                file_name = Path(node).name

                # Style based on importance
                in_degree = self.graph.get_in_degree(node)
                if in_degree >= 3:
                    # Core module
                    lines.append(f"        {node_id}[{file_name}]:::core")
                elif in_degree == 0:
                    # Entry point
                    lines.append(f"        {node_id}[{file_name}]:::entry")
                else:
                    lines.append(f"        {node_id}[{file_name}]")

            if len(node_groups) > 1:
                lines.append("    end")

        # Add edges
        lines.append("")
        for source in important_nodes:
            if source in node_ids:
                for target in self.graph.get_dependencies(source):
                    if target in node_ids:
                        lines.append(f"    {node_ids[source]} --> {node_ids[target]}")

        # Add styling
        lines.append("")
        lines.append("    classDef core fill:#ff6b6b,stroke:#c92a2a,color:#fff")
        lines.append("    classDef entry fill:#51cf66,stroke:#2f9e44,color:#fff")

        return "\n".join(lines)

    def build_dependency_flow(self, start_file: str, depth: int = 3) -> str:
        """
        Build a Mermaid diagram showing dependencies from a starting file.
        
        Args:
            start_file: Starting file path
            depth: Maximum depth to traverse
            
        Returns:
            Mermaid diagram as string
        """
        if start_file not in self.graph.graph.nodes():
            return f"graph TD\n    A[File not found: {start_file}]"

        lines = ["graph LR"]

        visited = set()
        node_ids = {}
        node_counter = 0

        def add_node(file_path: str, current_depth: int) -> Optional[str]:
            """Add a node and its dependencies recursively."""
            nonlocal node_counter
            
            if current_depth > depth or file_path in visited:
                return node_ids.get(file_path)

            visited.add(file_path)

            # Create node ID
            if file_path not in node_ids:
                node_id = f"N{node_counter}"
                node_ids[file_path] = node_id
                node_counter += 1

                # Add node
                file_name = Path(file_path).name
                lines.append(f"    {node_id}[{file_name}]")

            node_id = node_ids[file_path]

            # Add dependencies
            if current_depth < depth:
                for dep in self.graph.get_dependencies(file_path):
                    dep_id = add_node(dep, current_depth + 1)
                    if dep_id:
                        lines.append(f"    {node_id} --> {dep_id}")

            return node_id

        add_node(start_file, 0)

        return "\n".join(lines)

    def build_module_hierarchy(self) -> str:
        """
        Build a Mermaid diagram showing module hierarchy.
        
        Returns:
            Mermaid diagram as string
        """
        lines = ["graph TD"]

        # Group by top-level directory
        hierarchy = defaultdict(list)

        for node in self.graph.graph.nodes():
            parts = Path(node).parts
            if len(parts) > 1:
                top_level = parts[0]
                hierarchy[top_level].append(node)
            else:
                hierarchy["root"].append(node)

        # Build hierarchy
        dir_ids = {}
        dir_counter = 0

        for dir_name, files in sorted(hierarchy.items()):
            if not files:
                continue

            # Create directory node
            dir_id = f"D{dir_counter}"
            dir_ids[dir_name] = dir_id
            dir_counter += 1

            lines.append(f"    {dir_id}[{dir_name}/]:::directory")

            # Add top files (limit to avoid clutter)
            for i, file_path in enumerate(files[:5]):
                file_name = Path(file_path).name
                file_id = f"F{dir_counter}_{i}"
                lines.append(f"    {file_id}[{file_name}]")
                lines.append(f"    {dir_id} --> {file_id}")

            if len(files) > 5:
                more_id = f"M{dir_counter}"
                lines.append(f"    {more_id}[...{len(files) - 5} more files]:::more")
                lines.append(f"    {dir_id} --> {more_id}")

        # Add styling
        lines.append("")
        lines.append("    classDef directory fill:#4dabf7,stroke:#1971c2,color:#fff")
        lines.append("    classDef more fill:#e9ecef,stroke:#adb5bd,color:#495057")

        return "\n".join(lines)

    def _get_important_nodes(self) -> list[str]:
        """Get the most important nodes to include in diagram."""
        # Calculate importance scores
        scores = {}

        for node in self.graph.graph.nodes():
            in_degree = self.graph.get_in_degree(node)
            out_degree = self.graph.get_out_degree(node)

            # Score based on connectivity
            score = in_degree * 2 + out_degree

            scores[node] = score

        # Sort by score and take top N
        sorted_nodes = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [node for node, _ in sorted_nodes[: self.max_nodes]]

    def _group_by_directory(self, nodes: list[str]) -> dict[str, list[str]]:
        """Group nodes by their parent directory."""
        groups = defaultdict(list)

        for node in nodes:
            parts = Path(node).parts
            if len(parts) > 1:
                # Use first directory as group
                group_name = parts[0]
            else:
                group_name = "root"

            groups[group_name].append(node)

        return dict(groups)

    def _sanitize_id(self, text: str) -> str:
        """Sanitize text for use as Mermaid ID."""
        # Replace special characters
        sanitized = text.replace("/", "_").replace(".", "_").replace("-", "_")
        # Ensure it starts with a letter
        if not sanitized[0].isalpha():
            sanitized = "G_" + sanitized
        return sanitized


def graph_to_mermaid(
    graph: DependencyGraph, max_nodes: int = 30, diagram_type: str = "architecture"
) -> str:
    """
    Convert dependency graph to Mermaid diagram.
    
    Args:
        graph: Dependency graph
        max_nodes: Maximum nodes to include
        diagram_type: Type of diagram ("architecture", "hierarchy")
        
    Returns:
        Mermaid diagram as string
    """
    builder = MermaidBuilder(graph, max_nodes)

    if diagram_type == "hierarchy":
        return builder.build_module_hierarchy()
    else:
        return builder.build_architecture_diagram()


def create_dependency_flow(
    graph: DependencyGraph, start_file: str, depth: int = 3
) -> str:
    """
    Create a dependency flow diagram from a starting file.
    
    Args:
        graph: Dependency graph
        start_file: Starting file path
        depth: Maximum depth to traverse
        
    Returns:
        Mermaid diagram as string
    """
    builder = MermaidBuilder(graph)
    return builder.build_dependency_flow(start_file, depth)

# Made with Bob
