"""Data models for code scanning and metadata extraction."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FunctionInfo:
    """Information about a function or method."""

    name: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    parameters: list[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    decorators: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    """Information about a class."""

    name: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    methods: list[FunctionInfo] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)


@dataclass
class FileMetadata:
    """Metadata extracted from a source code file."""

    path: str
    language: str
    loc: int  # Lines of code
    imports: list[str] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[FunctionInfo] = field(default_factory=list)
    top_docstring: Optional[str] = None
    sha256: str = ""

    @property
    def relative_path(self) -> str:
        """Get the relative path from the repository root."""
        return self.path

    @property
    def file_name(self) -> str:
        """Get the file name."""
        return Path(self.path).name

    @property
    def extension(self) -> str:
        """Get the file extension."""
        return Path(self.path).suffix

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "language": self.language,
            "loc": self.loc,
            "imports": self.imports,
            "classes": [
                {
                    "name": cls.name,
                    "line_start": cls.line_start,
                    "line_end": cls.line_end,
                    "docstring": cls.docstring,
                    "methods": [
                        {
                            "name": m.name,
                            "line_start": m.line_start,
                            "line_end": m.line_end,
                            "parameters": m.parameters,
                        }
                        for m in cls.methods
                    ],
                    "base_classes": cls.base_classes,
                }
                for cls in self.classes
            ],
            "functions": [
                {
                    "name": func.name,
                    "line_start": func.line_start,
                    "line_end": func.line_end,
                    "parameters": func.parameters,
                    "is_async": func.is_async,
                }
                for func in self.functions
            ],
            "top_docstring": self.top_docstring,
            "sha256": self.sha256,
        }


@dataclass
class RepositoryMetadata:
    """Metadata for an entire repository."""

    root_path: str
    files: list[FileMetadata] = field(default_factory=list)
    total_files: int = 0
    total_loc: int = 0
    languages: dict[str, int] = field(default_factory=dict)  # language -> file count

    def add_file(self, file_meta: FileMetadata) -> None:
        """Add a file to the repository metadata."""
        self.files.append(file_meta)
        self.total_files += 1
        self.total_loc += file_meta.loc
        self.languages[file_meta.language] = self.languages.get(file_meta.language, 0) + 1

    def get_files_by_language(self, language: str) -> list[FileMetadata]:
        """Get all files of a specific language."""
        return [f for f in self.files if f.language == language]

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "root_path": self.root_path,
            "total_files": self.total_files,
            "total_loc": self.total_loc,
            "languages": self.languages,
            "files": [f.to_dict() for f in self.files],
        }

# Made with Bob
