"""Debug script to test import extraction."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.scanner.metadata_extractor import extract_metadata
from src.graph.dependency_graph import DependencyGraph
from src.scanner.models import RepositoryMetadata

# Test on a single file
test_file = Path("../stock-trend-analyzer/app.py")
if test_file.exists():
    print(f"Testing import extraction on: {test_file}")
    print("=" * 60)
    
    metadata = extract_metadata(test_file)
    
    print(f"\nLanguage: {metadata.language}")
    print(f"LOC: {metadata.loc}")
    print(f"\nImports found ({len(metadata.imports)}):")
    for imp in metadata.imports:
        print(f"  - {imp}")
    
    print(f"\nClasses found ({len(metadata.classes)}):")
    for cls in metadata.classes:
        print(f"  - {cls.name}")
    
    print(f"\nFunctions found ({len(metadata.functions)}):")
    for func in metadata.functions:
        print(f"  - {func.name}")
    
    # Test dependency resolution
    print("\n" + "=" * 60)
    print("Testing dependency resolution...")
    print("=" * 60)
    
    repo_root = Path("../stock-trend-analyzer")
    repo_meta = RepositoryMetadata(root_path=str(repo_root))
    
    # Scan a few files
    for py_file in list(repo_root.glob("*.py"))[:5]:
        meta = extract_metadata(py_file)
        repo_meta.add_file(meta)
        print(f"\nAdded: {py_file.name} with {len(meta.imports)} imports")
    
    # Build graph
    graph = DependencyGraph(repo_root)
    graph.build(repo_meta.files)
    
    print(f"\nGraph built:")
    print(f"  Nodes: {graph.graph.number_of_nodes()}")
    print(f"  Edges: {graph.graph.number_of_edges()}")
    
    if graph.graph.number_of_edges() > 0:
        print(f"\nEdges found:")
        for source, target in graph.graph.edges():
            print(f"  {Path(source).name} -> {Path(target).name}")
    else:
        print("\n⚠️  No edges found - imports not being resolved!")
        print("\nDebugging first file's imports:")
        first_file = repo_meta.files[0]
        print(f"\nFile: {first_file.path}")
        print(f"Imports: {first_file.imports}")
        for imp in first_file.imports[:3]:  # Test first 3 imports
            resolved = graph._resolve_import(imp, first_file)
            print(f"  {imp} -> {resolved}")

else:
    print(f"Test file not found: {test_file}")

# Made with Bob
