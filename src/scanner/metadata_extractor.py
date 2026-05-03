"""Extract metadata from source code files."""

import hashlib
import re
from pathlib import Path
from typing import Any, Optional

from src.scanner.ast_parser import get_parser
from src.scanner.language_detector import detect_language
from src.scanner.models import ClassInfo, FileMetadata, FunctionInfo


def compute_sha256(content: str) -> str:
    """
    Compute SHA256 hash of content.
    
    Args:
        content: File content
        
    Returns:
        SHA256 hash as hex string
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def count_loc(content: str) -> int:
    """
    Count lines of code (excluding empty lines and comments).
    
    Args:
        content: File content
        
    Returns:
        Number of lines of code
    """
    lines = content.split("\n")
    loc = 0
    
    for line in lines:
        stripped = line.strip()
        # Skip empty lines
        if not stripped:
            continue
        # Skip single-line comments (basic heuristic)
        if stripped.startswith(("#", "//", "/*", "*", "*/")):
            continue
        loc += 1
    
    return loc


def extract_python_imports(tree: Any, content: bytes) -> list[str]:
    """Extract import statements from Python code."""
    imports = []
    parser = get_parser()
    
    # Extract import nodes
    import_nodes = parser.extract_nodes(tree, ["import_statement", "import_from_statement"])
    
    for node in import_nodes:
        text = parser.get_node_text(node, content).strip()
        
        # Parse "import x" or "import x as y" or "import x, y, z"
        if text.startswith("import "):
            # Handle multiple imports: import x, y, z
            import_part = text.replace("import ", "").split("#")[0].strip()
            for item in import_part.split(","):
                item = item.strip()
                # Remove "as alias" part
                module = item.split(" as ")[0].strip()
                if module:
                    imports.append(module)
        
        # Parse "from x import y" or "from x.y.z import a"
        elif text.startswith("from "):
            match = re.match(r"from\s+([\w.]+)\s+import", text)
            if match:
                imports.append(match.group(1))
    
    return list(set(imports))  # Remove duplicates


def extract_javascript_imports(tree: Any, content: bytes) -> list[str]:
    """Extract import statements from JavaScript/TypeScript code."""
    imports = []
    parser = get_parser()
    
    # Extract import nodes
    import_nodes = parser.extract_nodes(tree, ["import_statement"])
    
    for node in import_nodes:
        text = parser.get_node_text(node, content).strip()
        
        # Extract module name from import statement
        # Handle: import x from 'module'
        match = re.search(r'from\s+["\']([^"\']+)["\']', text)
        if match:
            imports.append(match.group(1))
        else:
            # Handle: import 'module' or import('module')
            match = re.search(r'import\s*\(?\s*["\']([^"\']+)["\']', text)
            if match:
                imports.append(match.group(1))
    
    # Also extract require() calls for CommonJS
    require_pattern = re.compile(rb'require\s*\(\s*["\']([^"\']+)["\']\s*\)')
    for match in require_pattern.finditer(content):
        try:
            module = match.group(1).decode('utf-8')
            imports.append(module)
        except:
            pass
    
    return list(set(imports))


def extract_imports(tree: Any, content: bytes, language: str) -> list[str]:
    """
    Extract import statements from code.
    
    Args:
        tree: Tree-sitter tree
        content: File content as bytes
        language: Programming language
        
    Returns:
        List of imported modules
    """
    if tree is None:
        return []
    
    if language == "python":
        return extract_python_imports(tree, content)
    elif language in ["javascript", "typescript"]:
        return extract_javascript_imports(tree, content)
    
    # For other languages, return empty list for now
    return []


def extract_python_functions(tree: Any, content: bytes) -> list[FunctionInfo]:
    """Extract function definitions from Python code."""
    functions = []
    parser = get_parser()
    
    function_nodes = parser.extract_nodes(tree, ["function_definition"])
    
    for node in function_nodes:
        # Get function name
        name_node = None
        for child in node.children:
            if child.type == "identifier":
                name_node = child
                break
        
        if name_node is None:
            continue
        
        name = parser.get_node_text(name_node, content)
        
        # Get parameters
        parameters = []
        for child in node.children:
            if child.type == "parameters":
                param_text = parser.get_node_text(child, content)
                # Simple parameter extraction
                params = re.findall(r"(\w+)(?:\s*:\s*\w+)?(?:\s*=\s*[^,)]+)?", param_text)
                parameters = [p for p in params if p not in ("self", "cls")]
                break
        
        # Get docstring
        docstring = None
        for child in node.children:
            if child.type == "block":
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for expr_child in stmt.children:
                            if expr_child.type == "string":
                                docstring = parser.get_node_text(expr_child, content).strip('"""\'\'\'')
                                break
                        break
                break
        
        functions.append(
            FunctionInfo(
                name=name,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                docstring=docstring,
                parameters=parameters,
                is_async=False,  # TODO: Detect async functions
                is_method=False,  # Will be set when extracting classes
            )
        )
    
    return functions


def extract_python_classes(tree: Any, content: bytes) -> list[ClassInfo]:
    """Extract class definitions from Python code."""
    classes = []
    parser = get_parser()
    
    class_nodes = parser.extract_nodes(tree, ["class_definition"])
    
    for node in class_nodes:
        # Get class name
        name_node = None
        for child in node.children:
            if child.type == "identifier":
                name_node = child
                break
        
        if name_node is None:
            continue
        
        name = parser.get_node_text(name_node, content)
        
        # Get base classes
        base_classes = []
        for child in node.children:
            if child.type == "argument_list":
                bases_text = parser.get_node_text(child, content)
                base_classes = re.findall(r"(\w+)", bases_text)
                break
        
        # Get docstring
        docstring = None
        for child in node.children:
            if child.type == "block":
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for expr_child in stmt.children:
                            if expr_child.type == "string":
                                docstring = parser.get_node_text(expr_child, content).strip('"""\'\'\'')
                                break
                        break
                break
        
        # Extract methods (functions within the class)
        methods = []
        for child in node.children:
            if child.type == "block":
                method_nodes = parser.extract_nodes(child, ["function_definition"])
                for method_node in method_nodes:
                    # Similar to function extraction
                    method_name_node = None
                    for method_child in method_node.children:
                        if method_child.type == "identifier":
                            method_name_node = method_child
                            break
                    
                    if method_name_node:
                        method_name = parser.get_node_text(method_name_node, content)
                        methods.append(
                            FunctionInfo(
                                name=method_name,
                                line_start=method_node.start_point[0] + 1,
                                line_end=method_node.end_point[0] + 1,
                                is_method=True,
                            )
                        )
        
        classes.append(
            ClassInfo(
                name=name,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                docstring=docstring,
                methods=methods,
                base_classes=base_classes,
            )
        )
    
    return classes


def extract_top_docstring(content: str, language: str) -> Optional[str]:
    """
    Extract the top-level docstring from a file.
    
    Args:
        content: File content
        language: Programming language
        
    Returns:
        Top docstring or None
    """
    if language == "python":
        # Match triple-quoted strings at the start of the file
        match = re.match(r'^\s*["\']{{3}}(.*?)["\']{{3}}', content, re.DOTALL)
        if match:
            return match.group(1).strip()
    
    return None


def extract_metadata(file_path: Path, language: Optional[str] = None) -> FileMetadata:
    """
    Extract metadata from a source code file.
    
    Args:
        file_path: Path to the file
        language: Programming language (auto-detected if None)
        
    Returns:
        FileMetadata object
    """
    # Detect language if not provided
    if language is None:
        language = detect_language(file_path)
    
    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        content = ""
    
    # Initialize metadata
    metadata = FileMetadata(
        path=str(file_path),
        language=language,
        loc=count_loc(content),
        sha256=compute_sha256(content),
        top_docstring=extract_top_docstring(content, language),
    )
    
    # Parse with tree-sitter if supported
    parser = get_parser()
    if parser.is_language_supported(language):
        tree = parser.parse_file(file_path, language)
        if tree is not None:
            content_bytes = content.encode("utf-8")
            
            # Extract imports
            metadata.imports = extract_imports(tree, content_bytes, language)
            
            # Extract classes and functions (Python only for now)
            if language == "python":
                metadata.classes = extract_python_classes(tree, content_bytes)
                metadata.functions = extract_python_functions(tree, content_bytes)
    
    return metadata

# Made with Bob
