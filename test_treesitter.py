"""Test tree-sitter parsing directly."""
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
    print("[OK] tree-sitter imports successful")
    
    # Create parser
    parser = Parser()
    parser.set_language(Language(tree_sitter_python.language()))
    print("[OK] Parser created")
    
    # Test on simple Python code
    code = b"""
import os
import sys
from pathlib import Path

def hello():
    print("Hello")
"""
    
    tree = parser.parse(code)
    print(f"[OK] Parsed code, root node type: {tree.root_node.type}")
    
    # Find import nodes
    def find_imports(node, depth=0):
        if node.type in ["import_statement", "import_from_statement"]:
            text = code[node.start_byte:node.end_byte].decode('utf-8')
            print(f"  Found import at depth {depth}: {text.strip()}")
        for child in node.children:
            find_imports(child, depth + 1)
    
    print("\nSearching for imports:")
    find_imports(tree.root_node)
    
    # Now test on real file
    print("\n" + "="*60)
    print("Testing on real file: ../stock-trend-analyzer/app.py")
    print("="*60)
    
    test_file = Path("../stock-trend-analyzer/app.py")
    if test_file.exists():
        content = test_file.read_bytes()
        tree = parser.parse(content)
        print(f"[OK] Parsed file, root node: {tree.root_node.type}")
        print(f"  File size: {len(content)} bytes")
        print(f"  Root children: {len(tree.root_node.children)}")
        
        import_count = 0
        def count_imports(node):
            global import_count
            if node.type in ["import_statement", "import_from_statement"]:
                import_count += 1
                text = content[node.start_byte:node.end_byte].decode('utf-8')
                if import_count <= 5:  # Show first 5
                    print(f"  Import {import_count}: {text.strip()}")
            for child in node.children:
                count_imports(child)
        
        print("\nImports found:")
        count_imports(tree.root_node)
        print(f"\nTotal imports: {import_count}")
    else:
        print("File not found!")
        
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

# Made with Bob
