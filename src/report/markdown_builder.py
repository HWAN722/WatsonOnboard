"""Build markdown documentation from analysis results."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from src.graph.dependency_graph import DependencyGraph
from src.graph.ranking import ModuleRanker
from src.scanner.models import RepositoryMetadata


class MarkdownBuilder:
    """Build markdown documentation for repository onboarding."""

    def __init__(self, repo_meta: RepositoryMetadata) -> None:
        """
        Initialize the markdown builder.
        
        Args:
            repo_meta: Repository metadata
        """
        self.repo_meta = repo_meta

    def build_report(
        self,
        graph: DependencyGraph,
        ranker: ModuleRanker,
        project_summary: Optional[str] = None,
        module_summaries: Optional[dict[str, str]] = None,
        glossary: Optional[str] = None,
        mermaid_diagram: Optional[str] = None,
    ) -> str:
        """
        Build complete onboarding report.
        
        Args:
            graph: Dependency graph
            ranker: Module ranker
            project_summary: AI-generated project summary
            module_summaries: Dict mapping file paths to summaries
            glossary: AI-generated glossary
            mermaid_diagram: Mermaid architecture diagram
            
        Returns:
            Complete markdown report
        """
        sections = []

        # Header
        sections.append(self._build_header())

        # TL;DR
        sections.append(self._build_tldr(project_summary))

        # Tech Stack
        sections.append(self._build_tech_stack())

        # Architecture Diagram
        if mermaid_diagram:
            sections.append(self._build_architecture_section(mermaid_diagram))

        # Reading List
        sections.append(self._build_reading_list(ranker))

        # Module Summaries
        if module_summaries:
            sections.append(self._build_module_summaries(module_summaries, ranker))

        # Dependency Analysis
        sections.append(self._build_dependency_analysis(graph, ranker))

        # Glossary
        if glossary:
            sections.append(self._build_glossary_section(glossary))

        # Footer
        sections.append(self._build_footer())

        return "\n\n".join(sections)

    def _build_header(self) -> str:
        """Build report header."""
        repo_name = Path(self.repo_meta.root_path).name
        return f"""# 📚 Onboarding Guide: {repo_name}

> **Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
> **Tool:** WatsonOnboard - Legacy Code Onboarding Assistant

---"""

    def _build_tldr(self, summary: Optional[str]) -> str:
        """Build TL;DR section."""
        content = ["## 🎯 TL;DR", ""]

        if summary:
            content.append(summary)
        else:
            content.append(
                f"This repository contains {self.repo_meta.total_files} files "
                f"with {self.repo_meta.total_loc:,} lines of code across "
                f"{len(self.repo_meta.languages)} programming languages."
            )

        return "\n".join(content)

    def _build_tech_stack(self) -> str:
        """Build tech stack section."""
        content = ["## 🛠️ Tech Stack", ""]

        # Languages
        content.append("### Languages")
        content.append("")
        for lang, count in sorted(
            self.repo_meta.languages.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / self.repo_meta.total_files) * 100
            content.append(f"- **{lang.title()}**: {count} files ({percentage:.1f}%)")

        # Statistics
        content.append("")
        content.append("### Statistics")
        content.append("")
        content.append(f"- **Total Files:** {self.repo_meta.total_files}")
        content.append(f"- **Total Lines of Code:** {self.repo_meta.total_loc:,}")
        avg_loc = (
            self.repo_meta.total_loc // self.repo_meta.total_files
            if self.repo_meta.total_files > 0
            else 0
        )
        content.append(f"- **Average LOC per File:** {avg_loc}")

        return "\n".join(content)

    def _build_architecture_section(self, mermaid_diagram: str) -> str:
        """Build architecture diagram section."""
        content = ["## 🏗️ Architecture", ""]
        content.append("```mermaid")
        content.append(mermaid_diagram)
        content.append("```")

        return "\n".join(content)

    def _build_reading_list(self, ranker: ModuleRanker) -> str:
        """Build recommended reading list."""
        content = ["## 📖 Start Here: Recommended Reading Order", ""]

        reading_order = ranker.get_reading_order(max_files=15)

        if not reading_order:
            content.append("*No files to recommend.*")
            return "\n".join(content)

        content.append(
            "These files are recommended based on their importance and dependencies:"
        )
        content.append("")

        for i, file_path in enumerate(reading_order, 1):
            ranking = ranker.get_ranking(file_path)
            if ranking:
                reason = self._get_reading_reason(ranking)
                content.append(f"{i}. **`{file_path}`**")
                content.append(f"   - {reason}")
                content.append("")

        return "\n".join(content)

    def _get_reading_reason(self, ranking) -> str:
        """Get reason for reading a file."""
        reasons = []

        if ranking.is_core_module:
            reasons.append(f"Core module (imported by {ranking.in_degree} files)")
        if ranking.is_entry_point:
            reasons.append("Entry point")
        if ranking.pagerank > 0.05:
            reasons.append("High importance score")

        return " • ".join(reasons) if reasons else "Recommended"

    def _build_module_summaries(
        self, summaries: dict[str, str], ranker: ModuleRanker
    ) -> str:
        """Build module summaries section."""
        content = ["## 📦 Module Summaries", ""]

        # Get top modules
        reading_order = ranker.get_reading_order(max_files=10)

        for file_path in reading_order:
            if file_path in summaries:
                content.append(f"### `{file_path}`")
                content.append("")
                content.append(summaries[file_path])
                content.append("")

        return "\n".join(content)

    def _build_dependency_analysis(
        self, graph: DependencyGraph, ranker: ModuleRanker
    ) -> str:
        """Build dependency analysis section."""
        content = ["## 🔗 Dependency Analysis", ""]

        # Core modules
        content.append("### Core Modules (Most Imported)")
        content.append("")
        core_modules = ranker.get_core_modules(top_n=5)
        if core_modules:
            for module in core_modules:
                content.append(
                    f"- **`{module.path}`** - Imported by {module.in_degree} files"
                )
        else:
            content.append("*No core modules identified.*")

        content.append("")

        # Entry points
        content.append("### Entry Points")
        content.append("")
        entry_points = ranker.get_entry_points(top_n=5)
        if entry_points:
            for entry in entry_points:
                content.append(
                    f"- **`{entry.path}`** - Imports {entry.out_degree} files"
                )
        else:
            content.append("*No entry points identified.*")

        content.append("")

        # Circular dependencies
        if graph.has_cycles():
            content.append("### ⚠️ Circular Dependencies Detected")
            content.append("")
            cycles = graph.get_cycles()
            content.append(f"Found {len(cycles)} circular dependency cycle(s):")
            content.append("")
            for i, cycle in enumerate(cycles[:3], 1):  # Show first 3
                cycle_str = " → ".join(cycle[:4])  # Show first 4 files in cycle
                if len(cycle) > 4:
                    cycle_str += " → ..."
                content.append(f"{i}. {cycle_str}")
            content.append("")

        # Isolated files
        isolated = ranker.get_isolated_files()
        if isolated:
            content.append("### Isolated Files")
            content.append("")
            content.append(
                f"These {len(isolated)} files have no dependencies (neither import nor are imported):"
            )
            content.append("")
            for file_path in isolated[:5]:  # Show first 5
                content.append(f"- `{file_path}`")
            if len(isolated) > 5:
                content.append(f"- *...and {len(isolated) - 5} more*")
            content.append("")

        return "\n".join(content)

    def _build_glossary_section(self, glossary: str) -> str:
        """Build glossary section."""
        content = ["## 📚 Glossary", ""]
        content.append(glossary)

        return "\n".join(content)

    def _build_footer(self) -> str:
        """Build report footer."""
        return """---

## 💡 Tips for New Developers

1. **Start with the reading list** - Follow the recommended order for best understanding
2. **Check core modules first** - These are the foundation of the codebase
3. **Understand entry points** - These show how the application starts
4. **Watch for circular dependencies** - These may indicate areas needing refactoring
5. **Use the glossary** - Familiarize yourself with key terms and concepts

## 🤖 About This Report

This onboarding guide was automatically generated by **WatsonOnboard**, powered by IBM Watsonx AI.
It analyzes code structure, dependencies, and patterns to help new developers understand the codebase quickly.

For questions or issues, please refer to the project documentation or contact the development team.

---

*Generated with ❤️ by WatsonOnboard*"""


def build_onboarding_report(
    repo_meta: RepositoryMetadata,
    graph: DependencyGraph,
    ranker: ModuleRanker,
    **kwargs,
) -> str:
    """
    Build a complete onboarding report.
    
    Args:
        repo_meta: Repository metadata
        graph: Dependency graph
        ranker: Module ranker
        **kwargs: Additional optional content (summaries, glossary, etc.)
        
    Returns:
        Complete markdown report
    """
    builder = MarkdownBuilder(repo_meta)
    return builder.build_report(graph, ranker, **kwargs)

# Made with Bob
