"""Rank files by importance and identify entry points."""

from dataclasses import dataclass
from typing import Optional

import networkx as nx

from src.graph.dependency_graph import DependencyGraph


@dataclass
class FileRanking:
    """Ranking information for a file."""

    path: str
    in_degree: int  # Number of files importing this file
    out_degree: int  # Number of files this file imports
    pagerank: float  # PageRank score
    betweenness: float  # Betweenness centrality
    is_entry_point: bool  # True if file has no incoming dependencies
    is_core_module: bool  # True if file is highly imported


class ModuleRanker:
    """Rank modules by importance in the codebase."""

    def __init__(self, graph: DependencyGraph) -> None:
        """
        Initialize the ranker.
        
        Args:
            graph: Dependency graph
        """
        self.graph = graph
        self._rankings: dict[str, FileRanking] = {}

    def rank_all(self) -> dict[str, FileRanking]:
        """
        Rank all files in the graph.
        
        Returns:
            Dictionary mapping file paths to rankings
        """
        if not self.graph.graph.nodes():
            return {}

        # Calculate PageRank
        try:
            pagerank = nx.pagerank(self.graph.graph)
        except Exception:
            pagerank = {node: 0.0 for node in self.graph.graph.nodes()}

        # Calculate betweenness centrality
        try:
            betweenness = nx.betweenness_centrality(self.graph.graph)
        except Exception:
            betweenness = {node: 0.0 for node in self.graph.graph.nodes()}

        # Rank each file
        for file_path in self.graph.graph.nodes():
            in_degree = self.graph.get_in_degree(file_path)
            out_degree = self.graph.get_out_degree(file_path)

            self._rankings[file_path] = FileRanking(
                path=file_path,
                in_degree=in_degree,
                out_degree=out_degree,
                pagerank=pagerank.get(file_path, 0.0),
                betweenness=betweenness.get(file_path, 0.0),
                is_entry_point=in_degree == 0 and out_degree > 0,
                is_core_module=in_degree >= 3,  # Imported by 3+ files
            )

        return self._rankings

    def get_core_modules(self, top_n: int = 10) -> list[FileRanking]:
        """
        Get the most important core modules.
        
        Core modules are files that are heavily imported by others.
        
        Args:
            top_n: Number of top modules to return
            
        Returns:
            List of file rankings sorted by importance
        """
        if not self._rankings:
            self.rank_all()

        # Sort by in-degree (most imported)
        core_modules = sorted(
            self._rankings.values(),
            key=lambda r: (r.in_degree, r.pagerank),
            reverse=True,
        )

        return core_modules[:top_n]

    def get_entry_points(self, top_n: Optional[int] = None) -> list[FileRanking]:
        """
        Get entry point files.
        
        Entry points are files that import others but are not imported themselves.
        
        Args:
            top_n: Number of top entry points to return (None for all)
            
        Returns:
            List of entry point rankings
        """
        if not self._rankings:
            self.rank_all()

        entry_points = [r for r in self._rankings.values() if r.is_entry_point]

        # Sort by out-degree (imports most files)
        entry_points.sort(key=lambda r: r.out_degree, reverse=True)

        if top_n is not None:
            return entry_points[:top_n]
        return entry_points

    def get_reading_order(self, max_files: int = 20) -> list[str]:
        """
        Get a recommended reading order for understanding the codebase.
        
        The order prioritizes:
        1. Core modules (most imported)
        2. Entry points
        3. Files with high PageRank
        
        Args:
            max_files: Maximum number of files to include
            
        Returns:
            List of file paths in recommended reading order
        """
        if not self._rankings:
            self.rank_all()

        # Get core modules
        core = self.get_core_modules(top_n=max_files // 2)
        core_paths = {r.path for r in core}

        # Get entry points
        entry = self.get_entry_points(top_n=max_files // 4)
        entry_paths = {r.path for r in entry}

        # Get high PageRank files
        by_pagerank = sorted(
            self._rankings.values(),
            key=lambda r: r.pagerank,
            reverse=True,
        )

        # Combine in order: core, entry, pagerank
        reading_order = []
        
        # Add core modules first
        for ranking in core:
            if ranking.path not in reading_order:
                reading_order.append(ranking.path)

        # Add entry points
        for ranking in entry:
            if ranking.path not in reading_order:
                reading_order.append(ranking.path)

        # Fill remaining with high PageRank files
        for ranking in by_pagerank:
            if len(reading_order) >= max_files:
                break
            if ranking.path not in reading_order:
                reading_order.append(ranking.path)

        return reading_order[:max_files]

    def get_isolated_files(self) -> list[str]:
        """
        Get files that have no dependencies (neither import nor are imported).
        
        Returns:
            List of isolated file paths
        """
        if not self._rankings:
            self.rank_all()

        return [
            r.path
            for r in self._rankings.values()
            if r.in_degree == 0 and r.out_degree == 0
        ]

    def get_hub_files(self, threshold: int = 5) -> list[FileRanking]:
        """
        Get hub files that both import many files and are imported by many.
        
        Args:
            threshold: Minimum degree to be considered a hub
            
        Returns:
            List of hub file rankings
        """
        if not self._rankings:
            self.rank_all()

        hubs = [
            r
            for r in self._rankings.values()
            if r.in_degree >= threshold and r.out_degree >= threshold
        ]

        # Sort by total degree
        hubs.sort(key=lambda r: r.in_degree + r.out_degree, reverse=True)

        return hubs

    def get_ranking(self, file_path: str) -> Optional[FileRanking]:
        """
        Get ranking for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            FileRanking or None if file not found
        """
        if not self._rankings:
            self.rank_all()

        return self._rankings.get(file_path)

    def to_dict(self) -> dict:
        """
        Convert rankings to dictionary representation.
        
        Returns:
            Dictionary with ranking information
        """
        if not self._rankings:
            self.rank_all()

        return {
            "core_modules": [
                {
                    "path": r.path,
                    "in_degree": r.in_degree,
                    "pagerank": r.pagerank,
                }
                for r in self.get_core_modules()
            ],
            "entry_points": [
                {
                    "path": r.path,
                    "out_degree": r.out_degree,
                }
                for r in self.get_entry_points()
            ],
            "reading_order": self.get_reading_order(),
            "isolated_files": self.get_isolated_files(),
        }


def rank_modules(graph: DependencyGraph) -> ModuleRanker:
    """
    Create a module ranker for the given graph.
    
    Args:
        graph: Dependency graph
        
    Returns:
        ModuleRanker instance
    """
    ranker = ModuleRanker(graph)
    ranker.rank_all()
    return ranker

# Made with Bob
