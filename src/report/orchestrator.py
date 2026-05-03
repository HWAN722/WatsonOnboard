"""Orchestrate the complete analysis pipeline."""

import logging
from pathlib import Path
from typing import Optional

import structlog

from src.graph.dependency_graph import build_graph
from src.graph.ranking import rank_modules
from src.report.markdown_builder import build_onboarding_report
from src.report.mermaid_builder import graph_to_mermaid
from src.scanner.file_walker import walk
from src.scanner.language_detector import detect_language
from src.scanner.metadata_extractor import extract_metadata
from src.scanner.models import RepositoryMetadata
from src.watsonx.cache import get_cache
from src.watsonx.chunker import get_chunker
from src.watsonx.client import get_client
from src.watsonx.prompts import (
    create_module_summary_prompt,
    create_project_tldr_prompt,
)

logger = structlog.get_logger()


class AnalysisPipeline:
    """Orchestrate the complete repository analysis pipeline."""

    def __init__(
        self,
        repo_path: Path,
        use_llm: bool = True,
        use_cache: bool = True,
    ) -> None:
        """
        Initialize the pipeline.
        
        Args:
            repo_path: Path to repository root
            use_llm: Whether to use LLM for summaries
            use_cache: Whether to use response caching
        """
        self.repo_path = repo_path
        self.use_llm = use_llm
        self.use_cache = use_cache

        # Initialize components
        self.chunker = get_chunker()
        if use_llm:
            try:
                self.llm_client = get_client()
            except Exception as e:
                logger.warning("llm_init_failed", error=str(e))
                self.llm_client = None
                self.use_llm = False
        else:
            self.llm_client = None

        if use_cache:
            self.cache = get_cache()
        else:
            self.cache = None

    def run(self, output_path: Optional[Path] = None) -> str:
        """
        Run the complete analysis pipeline.
        
        Args:
            output_path: Path to write ONBOARDING.md (None to return only)
            
        Returns:
            Generated markdown report
        """
        logger.info("pipeline_start", repo_path=str(self.repo_path))

        # Phase 1: Scan repository
        logger.info("phase_1_scan_start")
        repo_meta = self._scan_repository()
        logger.info(
            "phase_1_scan_complete",
            total_files=repo_meta.total_files,
            total_loc=repo_meta.total_loc,
        )

        # Phase 2: Build dependency graph
        logger.info("phase_2_graph_start")
        graph = build_graph(repo_meta)
        logger.info(
            "phase_2_graph_complete",
            nodes=len(graph.graph.nodes()),
            edges=len(graph.graph.edges()),
        )

        # Phase 3: Rank modules
        logger.info("phase_3_ranking_start")
        ranker = rank_modules(graph)
        logger.info("phase_3_ranking_complete")

        # Phase 4: Generate summaries (optional, with LLM)
        module_summaries = None
        project_summary = None

        if self.use_llm and self.llm_client:
            logger.info("phase_4_llm_start")
            try:
                module_summaries = self._generate_module_summaries(repo_meta, ranker)
                project_summary = self._generate_project_summary(repo_meta, ranker)
                logger.info("phase_4_llm_complete")
            except Exception as e:
                logger.error("phase_4_llm_failed", error=str(e))

        # Phase 5: Generate architecture diagram
        logger.info("phase_5_diagram_start")
        mermaid_diagram = graph_to_mermaid(graph, max_nodes=25)
        logger.info("phase_5_diagram_complete")

        # Phase 6: Build report
        logger.info("phase_6_report_start")
        report = build_onboarding_report(
            repo_meta=repo_meta,
            graph=graph,
            ranker=ranker,
            project_summary=project_summary,
            module_summaries=module_summaries,
            mermaid_diagram=mermaid_diagram,
        )
        logger.info("phase_6_report_complete", report_length=len(report))

        # Write to file if path provided
        if output_path:
            output_path.write_text(report, encoding="utf-8")
            logger.info("report_written", path=str(output_path))

        logger.info("pipeline_complete")

        return report

    def _scan_repository(self) -> RepositoryMetadata:
        """Scan repository and extract metadata."""
        repo_meta = RepositoryMetadata(root_path=str(self.repo_path))

        # Walk files
        for file_path in walk(self.repo_path):
            try:
                # Detect language
                language = detect_language(file_path)

                # Extract metadata
                file_meta = extract_metadata(file_path, language)

                # Add to repository metadata
                repo_meta.add_file(file_meta)

                logger.debug(
                    "file_scanned",
                    path=str(file_path),
                    language=language,
                    loc=file_meta.loc,
                )

            except Exception as e:
                logger.warning("file_scan_failed", path=str(file_path), error=str(e))

        return repo_meta

    def _generate_module_summaries(
        self, repo_meta: RepositoryMetadata, ranker
    ) -> dict[str, str]:
        """Generate AI summaries for top modules."""
        summaries = {}

        # Get top files to summarize
        reading_order = ranker.get_reading_order(max_files=10)

        for file_path in reading_order:
            try:
                # Find file metadata
                file_meta = next(
                    (f for f in repo_meta.files if f.path == file_path), None
                )

                if not file_meta:
                    continue

                # Read file content
                content = Path(file_path).read_text(encoding="utf-8", errors="ignore")

                # Chunk for summarization
                optimized_content = self.chunker.chunk_for_summary(file_meta, content)

                # Create prompt
                prompt = create_module_summary_prompt(
                    file_path=file_path,
                    language=file_meta.language,
                    loc=file_meta.loc,
                    code=optimized_content,
                )

                # Check cache
                cached = None
                if self.cache:
                    cached = self.cache.get(prompt, "summary")

                if cached:
                    summary = cached
                    logger.debug("summary_cache_hit", file=file_path)
                else:
                    # Generate summary
                    summary = self.llm_client.generate(prompt, max_new_tokens=300)

                    # Cache result
                    if self.cache:
                        self.cache.set(prompt, "summary", summary)

                    logger.debug("summary_generated", file=file_path)

                summaries[file_path] = summary

            except Exception as e:
                logger.warning("summary_failed", file=file_path, error=str(e))

        return summaries

    def _generate_project_summary(
        self, repo_meta: RepositoryMetadata, ranker
    ) -> str:
        """Generate AI summary for the entire project."""
        try:
            # Get core modules and entry points
            core_modules = ranker.get_core_modules(top_n=5)
            entry_points = ranker.get_entry_points(top_n=5)

            # Create prompt
            prompt = create_project_tldr_prompt(
                total_files=repo_meta.total_files,
                total_loc=repo_meta.total_loc,
                languages=repo_meta.languages,
                core_modules=[
                    {"path": m.path, "in_degree": m.in_degree} for m in core_modules
                ],
                entry_points=[{"path": e.path} for e in entry_points],
            )

            # Check cache
            cached = None
            if self.cache:
                cached = self.cache.get(prompt, "project_summary")

            if cached:
                logger.debug("project_summary_cache_hit")
                return cached

            # Generate summary
            summary = self.llm_client.generate(prompt, max_new_tokens=500)

            # Cache result
            if self.cache:
                self.cache.set(prompt, "project_summary", summary)

            logger.debug("project_summary_generated")

            return summary

        except Exception as e:
            logger.error("project_summary_failed", error=str(e))
            return ""


def analyze_repository(
    repo_path: Path,
    output_path: Optional[Path] = None,
    use_llm: bool = True,
    use_cache: bool = True,
) -> str:
    """
    Analyze a repository and generate onboarding documentation.
    
    Args:
        repo_path: Path to repository root
        output_path: Path to write ONBOARDING.md (None to return only)
        use_llm: Whether to use LLM for summaries
        use_cache: Whether to use response caching
        
    Returns:
        Generated markdown report
    """
    pipeline = AnalysisPipeline(repo_path, use_llm=use_llm, use_cache=use_cache)
    return pipeline.run(output_path)

# Made with Bob
