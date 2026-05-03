"""Abstract Syntax Tree parser using tree-sitter."""

from pathlib import Path
from typing import Any, Optional

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python
    import tree_sitter_javascript
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

# Language to tree-sitter language name mapping
LANGUAGE_MAP = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "c": "c",
    "cpp": "cpp",
    "csharp": "c_sharp",
    "ruby": "ruby",
    "php": "php",
}


class ASTParser:
    """Parser for source code using tree-sitter."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self._parsers: dict[str, Any] = {}
        
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "tree-sitter-languages is not installed. "
                "Install it with: pip install tree-sitter-languages"
            )

    def _get_parser(self, language: str) -> Optional[Any]:
        """
        Get or create a parser for the given language.
        
        Args:
            language: Programming language name
            
        Returns:
            Tree-sitter parser or None if language not supported
        """
        if language not in LANGUAGE_MAP:
            return None
        
        if language in self._parsers:
            return self._parsers[language]
        
        try:
            parser = Parser()
            if language == "python":
                parser.language = Language(tree_sitter_python.language())
            elif language in ["javascript", "typescript"]:
                parser.language = Language(tree_sitter_javascript.language())
            else:
                return None
            
            self._parsers[language] = parser
            return parser
        except Exception as e:
            # Log the error for debugging
            print(f"[DEBUG] Failed to create parser for {language}: {e}")
            return None

    def parse(self, content: str, language: str) -> Optional[Any]:
        """
        Parse source code content.
        
        Args:
            content: Source code content
            language: Programming language
            
        Returns:
            Tree-sitter tree object or None if parsing fails
        """
        parser = self._get_parser(language)
        if parser is None:
            return None
        
        try:
            # Convert content to bytes
            content_bytes = content.encode("utf-8")
            tree = parser.parse(content_bytes)
            return tree
        except Exception:
            return None

    def parse_file(self, file_path: Path, language: str) -> Optional[Any]:
        """
        Parse a source code file.
        
        Args:
            file_path: Path to the file
            language: Programming language
            
        Returns:
            Tree-sitter tree object or None if parsing fails
        """
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            return self.parse(content, language)
        except Exception:
            return None

    def extract_nodes(
        self, tree: Any, node_types: list[str], max_depth: int = 50
    ) -> list[Any]:
        """
        Extract nodes of specific types from the tree.
        
        Args:
            tree: Tree-sitter tree object
            node_types: List of node type names to extract
            max_depth: Maximum depth to traverse
            
        Returns:
            List of matching nodes
        """
        if tree is None:
            return []
        
        nodes = []
        
        def traverse(node: Any, depth: int = 0) -> None:
            """Recursively traverse the tree."""
            if depth > max_depth:
                return
            
            if node.type in node_types:
                nodes.append(node)
            
            for child in node.children:
                traverse(child, depth + 1)
        
        traverse(tree.root_node)
        return nodes

    def get_node_text(self, node: Any, content: bytes) -> str:
        """
        Get the text content of a node.
        
        Args:
            node: Tree-sitter node
            content: Source code content as bytes
            
        Returns:
            Text content of the node
        """
        try:
            return content[node.start_byte : node.end_byte].decode("utf-8")
        except Exception:
            return ""

    def is_language_supported(self, language: str) -> bool:
        """
        Check if a language is supported by tree-sitter.
        
        Args:
            language: Programming language name
            
        Returns:
            True if supported, False otherwise
        """
        return language in LANGUAGE_MAP


# Global parser instance
_parser_instance: Optional[ASTParser] = None


def get_parser() -> ASTParser:
    """
    Get the global parser instance.
    
    Returns:
        ASTParser instance
    """
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = ASTParser()
    return _parser_instance


def parse_file(file_path: Path, language: str) -> Optional[Any]:
    """
    Parse a file using the global parser instance.
    
    Args:
        file_path: Path to the file
        language: Programming language
        
    Returns:
        Tree-sitter tree object or None
    """
    parser = get_parser()
    return parser.parse_file(file_path, language)


def parse_content(content: str, language: str) -> Optional[Any]:
    """
    Parse content using the global parser instance.
    
    Args:
        content: Source code content
        language: Programming language
        
    Returns:
        Tree-sitter tree object or None
    """
    parser = get_parser()
    return parser.parse(content, language)

# Made with Bob
