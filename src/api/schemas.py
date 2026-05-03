"""Pydantic schemas for API request/response models."""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of an analysis job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """Request to analyze a repository."""

    repo_path: str = Field(
        ...,
        description="Path to the repository (local path or Git URL)",
        examples=["/path/to/repo", "https://github.com/user/repo.git"],
    )
    branch: str = Field(
        default="main",
        description="Git branch to analyze",
    )
    use_llm: bool = Field(
        default=True,
        description="Whether to use LLM for summaries",
    )
    use_cache: bool = Field(
        default=True,
        description="Whether to use response caching",
    )
    generate_embeddings: bool = Field(
        default=True,
        description="Whether to generate embeddings for Q&A",
    )


class AnalyzeResponse(BaseModel):
    """Response from analyze endpoint."""

    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Job creation timestamp")


class JobStatusResponse(BaseModel):
    """Response for job status check."""

    job_id: str = Field(..., description="Job identifier")
    status: JobStatus = Field(..., description="Current status")
    progress: float = Field(
        ...,
        description="Progress percentage (0-100)",
        ge=0,
        le=100,
    )
    message: str = Field(..., description="Status message")
    created_at: datetime = Field(..., description="Job creation time")
    updated_at: datetime = Field(..., description="Last update time")
    completed_at: Optional[datetime] = Field(
        None,
        description="Completion time (if completed)",
    )
    report_url: Optional[str] = Field(
        None,
        description="URL to download report (if completed)",
    )
    error: Optional[str] = Field(
        None,
        description="Error message (if failed)",
    )


class QueryRequest(BaseModel):
    """Request to query the codebase."""

    question: str = Field(
        ...,
        description="Question about the codebase",
        min_length=3,
        examples=["Where is authentication handled?", "How does the database connection work?"],
    )
    repo_id: Optional[str] = Field(
        None,
        description="Repository identifier (uses default if None)",
    )
    top_k: int = Field(
        default=5,
        description="Number of code chunks to retrieve",
        ge=1,
        le=20,
    )
    include_citations: bool = Field(
        default=True,
        description="Whether to include source citations",
    )


class Citation(BaseModel):
    """Source citation for an answer."""

    file_path: str = Field(..., description="Path to the source file")
    line_start: int = Field(..., description="Starting line number")
    line_end: int = Field(..., description="Ending line number")
    score: float = Field(..., description="Relevance score (0-1)")


class QueryResponse(BaseModel):
    """Response from query endpoint."""

    answer: str = Field(..., description="Generated answer")
    citations: list[Citation] = Field(
        default_factory=list,
        description="Source citations",
    )
    num_chunks_used: int = Field(
        ...,
        description="Number of code chunks used for context",
    )
    processing_time_ms: float = Field(
        ...,
        description="Processing time in milliseconds",
    )


class SearchRequest(BaseModel):
    """Request to search the codebase."""

    query: str = Field(
        ...,
        description="Search query",
        min_length=2,
    )
    repo_id: Optional[str] = Field(
        None,
        description="Repository identifier",
    )
    top_k: int = Field(
        default=10,
        description="Number of results to return",
        ge=1,
        le=50,
    )
    language: Optional[str] = Field(
        None,
        description="Filter by programming language",
    )


class SearchResult(BaseModel):
    """A single search result."""

    file_path: str = Field(..., description="Path to the file")
    language: str = Field(..., description="Programming language")
    line_start: int = Field(..., description="Starting line number")
    line_end: int = Field(..., description="Ending line number")
    content: str = Field(..., description="Code content")
    score: float = Field(..., description="Relevance score (0-1)")


class SearchResponse(BaseModel):
    """Response from search endpoint."""

    results: list[SearchResult] = Field(
        default_factory=list,
        description="Search results",
    )
    total_results: int = Field(..., description="Total number of results")
    processing_time_ms: float = Field(
        ...,
        description="Processing time in milliseconds",
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    watsonx: str = Field(..., description="Watsonx connectivity status")
    vector_store: Optional[str] = Field(
        None,
        description="Vector store status",
    )
    cache: Optional[str] = Field(
        None,
        description="Cache status",
    )


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[Any] = Field(
        None,
        description="Additional error details",
    )


class StatsResponse(BaseModel):
    """Statistics response."""

    total_files: int = Field(..., description="Total files analyzed")
    total_loc: int = Field(..., description="Total lines of code")
    languages: dict[str, int] = Field(
        ...,
        description="Language distribution",
    )
    vector_store_chunks: int = Field(
        ...,
        description="Number of chunks in vector store",
    )
    cache_size: int = Field(
        ...,
        description="Number of cached responses",
    )

# Made with Bob
