"""
Demo script to test WatsonOnboard on the InterviewHelper repository.
This version works without Watsonx credentials by demonstrating the
scanner and graph analysis capabilities.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scanner import file_walker
from src.scanner.language_detector import detect_language
from src.scanner.ast_parser import parse_file
from src.scanner.metadata_extractor import extract_metadata
from src.graph.dependency_graph import DependencyGraph
from src.graph.ranking import ModuleRanker


def main():
    """Run the demo analysis on InterviewHelper repository."""
    repo_path = Path(__file__).parent.parent / "test_repo"
    
    if not repo_path.exists():
        print(f"Error: Repository not found at {repo_path}")
        print("Please clone the repository first:")
        print("  git clone https://github.com/HWAN722/InterviewHelper.git test_repo")
        sys.exit(1)
    
    print("=" * 70)
    print("WatsonOnboard Demo - InterviewHelper Repository Analysis")
    print("=" * 70)
    print()
    
    # Step 1: Scan repository
    print("Step 1: Scanning repository files...")
    print("-" * 70)
    files = list(file_walker.walk(repo_path))
    print(f"✓ Found {len(files)} files")
    
    # Show file breakdown by type
    file_types = {}
    for file_path in files:
        ext = file_path.suffix or "no extension"
        file_types[ext] = file_types.get(ext, 0) + 1
    
    print("\nFile breakdown:")
    for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ext}: {count} files")
    print()
    
    # Step 2: Parse and extract metadata
    print("Step 2: Parsing code and extracting metadata...")
    print("-" * 70)
    
    parsed_files = []
    language_stats = {}
    
    for file_path in files:
        language = detect_language(file_path)
        if language:
            language_stats[language] = language_stats.get(language, 0) + 1
            metadata = extract_metadata(file_path, language)
            if metadata:
                parsed_files.append(metadata)
    
    print(f"✓ Successfully parsed {len(parsed_files)} files")
    print(f"✓ Detected {len(language_stats)} programming languages")
    
    print("\nLanguage breakdown:")
    for lang, count in sorted(language_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {lang}: {count} files")
    print()
    
    # Step 3: Extract code statistics
    print("Step 3: Analyzing code structure...")
    print("-" * 70)
    
    total_functions = 0
    total_classes = 0
    total_imports = 0
    
    for metadata in parsed_files:
        total_functions += len(metadata.functions)
        total_classes += len(metadata.classes)
        total_imports += len(metadata.imports)
    
    print(f"✓ Found {total_functions} functions")
    print(f"✓ Found {total_classes} classes")
    print(f"✓ Found {total_imports} import statements")
    print()
    
    # Show some example functions
    if parsed_files:
        print("Sample functions found:")
        func_count = 0
        for metadata in parsed_files:
            if metadata.functions and func_count < 5:
                for func in metadata.functions[:min(2, len(metadata.functions))]:
                    if func_count < 5:
                        file_name = Path(metadata.path).name
                        print(f"  - {func.name}() in {file_name} (line {func.line_start})")
                        func_count += 1
        print()
    
    # Step 4: Build dependency graph
    print("Step 4: Building dependency graph...")
    print("-" * 70)
    dep_graph = DependencyGraph(repo_path)
    dep_graph.build(parsed_files)
    
    nodes = dep_graph.graph.number_of_nodes()
    edges = dep_graph.graph.number_of_edges()
    
    print(f"✓ Dependency graph created")
    print(f"  - Nodes (files): {nodes}")
    print(f"  - Edges (dependencies): {edges}")
    print()
    
    # Step 5: Calculate file importance rankings
    print("Step 5: Calculating file importance rankings...")
    print("-" * 70)
    ranker = ModuleRanker(dep_graph)
    rankings = ranker.rank_all()
    
    print(f"✓ Ranked {len(rankings)} files by importance")
    print()
    
    # Display top 10 most important files
    print("Top 10 Most Important Files (by PageRank):")
    print("-" * 70)
    sorted_rankings = sorted(rankings.values(), key=lambda x: x.pagerank, reverse=True)[:10]
    
    for idx, ranking in enumerate(sorted_rankings, 1):
        file_name = Path(ranking.path).name
        try:
            rel_path = Path(ranking.path).relative_to(repo_path)
        except ValueError:
            rel_path = Path(ranking.path)
        print(f"{idx:2d}. {file_name}")
        print(f"    Path: {rel_path}")
        print(f"    PageRank: {ranking.pagerank:.6f}")
        print(f"    In-degree: {ranking.in_degree}, Out-degree: {ranking.out_degree}")
        print()
    
    # Step 6: Analyze specific Python implementations
    print("Step 6: Analyzing Machine Learning implementations...")
    print("-" * 70)
    
    ml_files = [m for m in parsed_files if "Machine Learning" in m.path and "Implementations" in m.path]
    
    if ml_files:
        print(f"✓ Found {len(ml_files)} ML implementation files")
        print()
        print("ML Implementations:")
        for metadata in ml_files:
            file_name = Path(metadata.path).name
            print(f"\n  {file_name}")
            print(f"    Functions: {len(metadata.functions)}")
            print(f"    Classes: {len(metadata.classes)}")
            print(f"    Lines of code: {metadata.loc}")
            
            if metadata.functions:
                print(f"    Key functions:")
                for func in metadata.functions[:3]:
                    params = ", ".join(func.parameters[:3])
                    if len(func.parameters) > 3:
                        params += ", ..."
                    print(f"      - {func.name}({params})")
    else:
        print("  No ML implementation files found")
    
    print()
    
    # Step 7: Show entry points and core modules
    print("Step 7: Identifying entry points and core modules...")
    print("-" * 70)
    
    entry_points = ranker.get_entry_points(top_n=5)
    if entry_points:
        print("Entry Points (files that import others but aren't imported):")
        for ranking in entry_points:
            file_name = Path(ranking.path).name
            print(f"  - {file_name} (imports {ranking.out_degree} files)")
    else:
        print("  No clear entry points found")
    
    print()
    
    core_modules = ranker.get_core_modules(top_n=5)
    if core_modules:
        print("Core Modules (most imported files):")
        for ranking in core_modules:
            file_name = Path(ranking.path).name
            print(f"  - {file_name} (imported by {ranking.in_degree} files)")
    else:
        print("  No core modules found")
    
    print()
    
    # Summary
    print("=" * 70)
    print("Analysis Summary")
    print("=" * 70)
    print(f"Repository: InterviewHelper")
    print(f"Total files scanned: {len(files)}")
    print(f"Files parsed: {len(parsed_files)}")
    print(f"Programming languages: {', '.join(language_stats.keys())}")
    print(f"Total functions: {total_functions}")
    print(f"Total classes: {total_classes}")
    print(f"Dependency graph nodes: {nodes}")
    print(f"Dependency graph edges: {edges}")
    print()
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print()
    print("Note: This demo shows the scanner and graph analysis capabilities.")
    print("To generate full AI-powered reports and use Q&A features, you need:")
    print("  1. Valid IBM Watsonx credentials in .env file")
    print("  2. Run: watson-onboard analyze test_repo --output report.md")
    print()


if __name__ == "__main__":
    main()

# Made with Bob
