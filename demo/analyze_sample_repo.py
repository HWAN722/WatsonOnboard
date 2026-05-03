"""
Demo script: Analyze a sample repository and generate an onboarding report.

This script demonstrates the full analysis workflow:
1. Scan repository files
2. Parse code and extract metadata
3. Build dependency graph
4. Calculate file importance rankings
5. Generate embeddings for Q&A
6. Create comprehensive onboarding report
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scanner.file_walker import FileWalker
from src.scanner.language_detector import LanguageDetector
from src.scanner.ast_parser import ASTParser
from src.scanner.metadata_extractor import MetadataExtractor
from src.graph.dependency_graph import DependencyGraphBuilder
from src.graph.ranking import PageRankCalculator
from src.watsonx.client import WatsonxClient
from src.report.orchestrator import ReportOrchestrator
from src.config import settings


def main():
    """Run the demo analysis."""
    # Configuration
    repo_path = input("Enter the path to the repository to analyze: ").strip()
    output_file = input("Enter output file path (default: onboarding_report.md): ").strip()
    
    if not output_file:
        output_file = "onboarding_report.md"
    
    repo_path_obj = Path(repo_path)
    if not repo_path_obj.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print("WatsonOnboard Demo - Repository Analysis")
    print(f"{'='*60}\n")
    
    # Step 1: Scan repository
    print("Step 1: Scanning repository files...")
    walker = FileWalker()
    files = walker.walk(str(repo_path_obj))
    print(f"  ✓ Found {len(files)} files\n")
    
    # Step 2: Parse and extract metadata
    print("Step 2: Parsing code and extracting metadata...")
    detector = LanguageDetector()
    parser = ASTParser()
    extractor = MetadataExtractor()
    
    parsed_files = []
    for file_info in files:
        language = detector.detect(file_info.path)
        if language:
            ast_result = parser.parse(file_info.path, language)
            if ast_result:
                metadata = extractor.extract(ast_result, file_info)
                parsed_files.append(metadata)
    
    print(f"  ✓ Parsed {len(parsed_files)} files\n")
    
    # Step 3: Build dependency graph
    print("Step 3: Building dependency graph...")
    graph_builder = DependencyGraphBuilder()
    dep_graph = graph_builder.build(parsed_files)
    print(f"  ✓ Graph has {dep_graph.number_of_nodes()} nodes and {dep_graph.number_of_edges()} edges\n")
    
    # Step 4: Calculate rankings
    print("Step 4: Calculating file importance rankings...")
    ranker = PageRankCalculator()
    rankings = ranker.calculate(dep_graph)
    print(f"  ✓ Ranked {len(rankings)} files\n")
    
    # Display top 5 most important files
    print("  Top 5 most important files:")
    sorted_rankings = sorted(rankings.items(), key=lambda x: x[1], reverse=True)[:5]
    for idx, (file_path, score) in enumerate(sorted_rankings, 1):
        print(f"    {idx}. {file_path} (score: {score:.4f})")
    print()
    
    # Step 5: Generate report
    print("Step 5: Generating onboarding report with Watsonx...")
    watsonx_client = WatsonxClient(
        api_key=settings.WATSONX_API_KEY,
        project_id=settings.WATSONX_PROJECT_ID,
        url=settings.WATSONX_URL,
    )
    
    orchestrator = ReportOrchestrator(watsonx_client)
    report = orchestrator.generate_report(
        files=parsed_files,
        graph=dep_graph,
        rankings=rankings,
    )
    print("  ✓ Report generated\n")
    
    # Step 6: Save report
    print(f"Step 6: Saving report to {output_file}...")
    output_path = Path(output_file)
    output_path.write_text(report, encoding="utf-8")
    print(f"  ✓ Report saved successfully\n")
    
    print(f"{'='*60}")
    print("Analysis Complete!")
    print(f"{'='*60}\n")
    print(f"Report saved to: {output_path.absolute()}")
    print("\nNext steps:")
    print("  1. Review the generated onboarding report")
    print("  2. Use 'watson-onboard ask' to query the codebase")
    print("  3. Start the API server with 'watson-onboard serve'")


if __name__ == "__main__":
    main()

# Made with Bob
