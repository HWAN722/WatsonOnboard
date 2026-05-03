"""Token-aware file chunking for LLM context windows."""

import re
from dataclasses import dataclass
from typing import Optional

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False

from src.config import settings
from src.scanner.models import FileMetadata


@dataclass
class CodeChunk:
    """A chunk of code with metadata."""

    content: str
    file_path: str
    language: str
    line_start: int
    line_end: int
    token_count: int


class Chunker:
    """Token-aware code chunker."""

    def __init__(self, max_tokens: Optional[int] = None) -> None:
        """
        Initialize the chunker.
        
        Args:
            max_tokens: Maximum tokens per chunk (uses config if None)
        """
        self.max_tokens = max_tokens or (settings.context_window // 2)
        
        # Initialize tokenizer if available
        if TIKTOKEN_AVAILABLE:
            try:
                # Use cl100k_base encoding (GPT-4, similar to Granite)
                self.encoding = tiktoken.get_encoding("cl100k_base")
            except Exception:
                self.encoding = None
        else:
            self.encoding = None

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Approximate token count
        """
        if self.encoding:
            return len(self.encoding.encode(text))
        else:
            # Rough approximation: 1 token ≈ 4 characters
            return len(text) // 4

    def split_file(
        self, file_meta: FileMetadata, content: str
    ) -> list[CodeChunk]:
        """
        Split a file into chunks that fit within token limits.
        
        Args:
            file_meta: File metadata
            content: File content
            
        Returns:
            List of code chunks
        """
        lines = content.split("\n")
        chunks = []
        
        current_chunk_lines = []
        current_chunk_start = 1
        current_tokens = 0
        
        for i, line in enumerate(lines, start=1):
            line_tokens = self.count_tokens(line + "\n")
            
            # If adding this line would exceed limit, save current chunk
            if current_tokens + line_tokens > self.max_tokens and current_chunk_lines:
                chunk_content = "\n".join(current_chunk_lines)
                chunks.append(
                    CodeChunk(
                        content=chunk_content,
                        file_path=file_meta.path,
                        language=file_meta.language,
                        line_start=current_chunk_start,
                        line_end=i - 1,
                        token_count=current_tokens,
                    )
                )
                
                # Start new chunk
                current_chunk_lines = [line]
                current_chunk_start = i
                current_tokens = line_tokens
            else:
                current_chunk_lines.append(line)
                current_tokens += line_tokens
        
        # Add final chunk if any lines remain
        if current_chunk_lines:
            chunk_content = "\n".join(current_chunk_lines)
            chunks.append(
                CodeChunk(
                    content=chunk_content,
                    file_path=file_meta.path,
                    language=file_meta.language,
                    line_start=current_chunk_start,
                    line_end=len(lines),
                    token_count=current_tokens,
                )
            )
        
        return chunks

    def signature_only(self, file_meta: FileMetadata, content: str) -> str:
        """
        Extract only function/class signatures from a file.
        
        This creates a compact summary by removing function bodies.
        
        Args:
            file_meta: File metadata
            content: File content
            
        Returns:
            Signature-only version of the file
        """
        if file_meta.language == "python":
            return self._python_signatures(content)
        elif file_meta.language in ["javascript", "typescript"]:
            return self._javascript_signatures(content)
        else:
            # For other languages, just return first N lines
            lines = content.split("\n")
            return "\n".join(lines[:50])

    def _python_signatures(self, content: str) -> str:
        """Extract Python function and class signatures."""
        lines = content.split("\n")
        result = []
        in_function = False
        indent_level = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Keep imports, class definitions, and function definitions
            if (
                stripped.startswith("import ")
                or stripped.startswith("from ")
                or stripped.startswith("class ")
                or stripped.startswith("def ")
                or stripped.startswith("async def ")
            ):
                result.append(line)
                
                # Track if we're entering a function
                if stripped.startswith(("def ", "async def ")):
                    in_function = True
                    indent_level = len(line) - len(line.lstrip())
                    
                    # Add docstring if next line is one
                    continue
            
            # Keep docstrings
            elif in_function and (stripped.startswith('"""') or stripped.startswith("'''")):
                result.append(line)
                # If docstring ends on same line, we're done
                if stripped.count('"""') == 2 or stripped.count("'''") == 2:
                    in_function = False
                    result.append("")  # Add blank line
            
            # Exit function body
            elif in_function and line and not line[0].isspace():
                in_function = False
        
        return "\n".join(result)

    def _javascript_signatures(self, content: str) -> str:
        """Extract JavaScript/TypeScript function signatures."""
        lines = content.split("\n")
        result = []
        
        for line in lines:
            stripped = line.strip()
            
            # Keep imports, exports, class, and function declarations
            if any(
                keyword in stripped
                for keyword in [
                    "import ",
                    "export ",
                    "class ",
                    "function ",
                    "const ",
                    "let ",
                    "var ",
                    "interface ",
                    "type ",
                ]
            ):
                # For function declarations, only keep the signature
                if "function" in stripped or "=>" in stripped:
                    # Keep line up to opening brace
                    if "{" in line:
                        result.append(line.split("{")[0] + "{ ... }")
                    else:
                        result.append(line)
                else:
                    result.append(line)
        
        return "\n".join(result)

    def chunk_for_summary(
        self, file_meta: FileMetadata, content: str
    ) -> str:
        """
        Create an optimal chunk for summarization.
        
        If file is small enough, return full content.
        Otherwise, return signature-only version.
        
        Args:
            file_meta: File metadata
            content: File content
            
        Returns:
            Content optimized for summarization
        """
        token_count = self.count_tokens(content)
        
        if token_count <= self.max_tokens:
            return content
        else:
            return self.signature_only(file_meta, content)


# Global chunker instance
_chunker_instance: Optional[Chunker] = None


def get_chunker() -> Chunker:
    """
    Get the global chunker instance.
    
    Returns:
        Chunker instance
    """
    global _chunker_instance
    if _chunker_instance is None:
        _chunker_instance = Chunker()
    return _chunker_instance


def split_file(file_meta: FileMetadata, content: str) -> list[CodeChunk]:
    """
    Split a file using the global chunker.
    
    Args:
        file_meta: File metadata
        content: File content
        
    Returns:
        List of code chunks
    """
    chunker = get_chunker()
    return chunker.split_file(file_meta, content)


def count_tokens(text: str) -> int:
    """
    Count tokens using the global chunker.
    
    Args:
        text: Text to count
        
    Returns:
        Token count
    """
    chunker = get_chunker()
    return chunker.count_tokens(text)

# Made with Bob
