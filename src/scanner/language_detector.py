"""Language detection for source code files."""

from pathlib import Path

# Extension to language mapping
EXTENSION_MAP = {
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",
    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    # Java
    ".java": "java",
    # Go
    ".go": "go",
    # Rust
    ".rs": "rust",
    # C/C++
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",
    # C#
    ".cs": "csharp",
    # Ruby
    ".rb": "ruby",
    # PHP
    ".php": "php",
    # Swift
    ".swift": "swift",
    # Kotlin
    ".kt": "kotlin",
    ".kts": "kotlin",
    # Scala
    ".scala": "scala",
    # Shell
    ".sh": "shell",
    ".bash": "shell",
    # Web
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".vue": "vue",
    ".svelte": "svelte",
    # Other
    ".sql": "sql",
    ".r": "r",
    ".R": "r",
    ".m": "matlab",
    ".lua": "lua",
    ".pl": "perl",
    ".pm": "perl",
}

# Language families for grouping
LANGUAGE_FAMILIES = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "javascript",
    "java": "java",
    "go": "go",
    "rust": "rust",
    "c": "c_family",
    "cpp": "c_family",
    "csharp": "c_family",
    "ruby": "ruby",
    "php": "php",
    "swift": "swift",
    "kotlin": "kotlin",
    "scala": "scala",
}


def detect_language(file_path: Path) -> str:
    """
    Detect the programming language of a file based on its extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Language name (lowercase) or "unknown" if not recognized
    """
    extension = file_path.suffix.lower()
    return EXTENSION_MAP.get(extension, "unknown")


def detect_language_from_content(content: str, file_path: Path) -> str:
    """
    Detect language from file content as a fallback.
    
    This is a simple heuristic-based approach. For production use,
    consider using pygments.lexers.guess_lexer() for more accuracy.
    
    Args:
        content: File content
        file_path: Path to the file
        
    Returns:
        Language name or "unknown"
    """
    # First try extension-based detection
    lang = detect_language(file_path)
    if lang != "unknown":
        return lang
    
    # Simple heuristics for common patterns
    content_lower = content.lower()
    
    # Python indicators
    if any(
        pattern in content
        for pattern in ["def ", "import ", "from ", "class ", "if __name__"]
    ):
        return "python"
    
    # JavaScript/TypeScript indicators
    if any(
        pattern in content
        for pattern in ["function ", "const ", "let ", "var ", "=>", "console.log"]
    ):
        if "interface " in content or ": " in content and "type " in content:
            return "typescript"
        return "javascript"
    
    # Java indicators
    if any(
        pattern in content
        for pattern in ["public class ", "private ", "protected ", "package "]
    ):
        return "java"
    
    # Go indicators
    if any(pattern in content for pattern in ["package ", "func ", "import ("]):
        return "go"
    
    return "unknown"


def get_language_family(language: str) -> str:
    """
    Get the language family for a given language.
    
    Args:
        language: Language name
        
    Returns:
        Language family name
    """
    return LANGUAGE_FAMILIES.get(language, language)


def is_supported_language(language: str) -> bool:
    """
    Check if a language is supported for analysis.
    
    Args:
        language: Language name
        
    Returns:
        True if supported, False otherwise
    """
    return language in LANGUAGE_FAMILIES


def get_supported_languages() -> list[str]:
    """
    Get list of all supported languages.
    
    Returns:
        List of supported language names
    """
    return sorted(set(EXTENSION_MAP.values()))


def get_supported_extensions() -> list[str]:
    """
    Get list of all supported file extensions.
    
    Returns:
        List of supported extensions
    """
    return sorted(EXTENSION_MAP.keys())

# Made with Bob
