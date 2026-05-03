"""API routes for codebase Q&A and search."""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    Citation,
    QueryRequest,
    QueryResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from src.qa.retriever import get_retriever

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_codebase(request: QueryRequest) -> QueryResponse:
    """
    Ask a question about the codebase using RAG.
    
    Args:
        request: Query request
        
    Returns:
        Query response with answer and citations
        
    Raises:
        HTTPException: If query fails
    """
    start_time = time.time()

    try:
        # Get retriever
        collection_name = request.repo_id or "code_chunks"
        retriever = get_retriever(collection_name=collection_name)

        # Answer question
        result = retriever.answer(
            question=request.question,
            top_k=request.top_k,
            include_citations=request.include_citations,
        )

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Format citations
        citations = []
        if request.include_citations:
            for citation_data in result.get("citations", []):
                citations.append(
                    Citation(
                        file_path=citation_data["file_path"],
                        line_start=citation_data["line_start"],
                        line_end=citation_data["line_end"],
                        score=citation_data["score"],
                    )
                )

        return QueryResponse(
            answer=result["answer"],
            citations=citations,
            num_chunks_used=result.get("num_chunks_used", 0),
            processing_time_ms=processing_time,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}",
        )


@router.post("/search", response_model=SearchResponse)
async def search_codebase(request: SearchRequest) -> SearchResponse:
    """
    Search the codebase for relevant code chunks.
    
    Args:
        request: Search request
        
    Returns:
        Search response with results
        
    Raises:
        HTTPException: If search fails
    """
    start_time = time.time()

    try:
        # Get retriever
        collection_name = request.repo_id or "code_chunks"
        retriever = get_retriever(collection_name=collection_name)

        # Search
        results = retriever.search(
            query=request.query,
            top_k=request.top_k,
        )

        # Filter by language if specified
        if request.language:
            results = [
                r for r in results
                if r["metadata"].get("language") == request.language
            ]

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        # Format results
        search_results = []
        for result in results:
            metadata = result["metadata"]
            search_results.append(
                SearchResult(
                    file_path=metadata["file_path"],
                    language=metadata["language"],
                    line_start=metadata["line_start"],
                    line_end=metadata["line_end"],
                    content=result["content"],
                    score=result["score"],
                )
            )

        return SearchResponse(
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=processing_time,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/file/{file_path:path}")
async def get_file_chunks(
    file_path: str,
    repo_id: Optional[str] = None,
    max_chunks: int = 10,
) -> dict:
    """
    Get all chunks for a specific file.
    
    Args:
        file_path: Path to the file
        repo_id: Repository identifier
        max_chunks: Maximum chunks to return
        
    Returns:
        File chunks
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Get retriever
        collection_name = repo_id or "code_chunks"
        retriever = get_retriever(collection_name=collection_name)

        # Get file context
        chunks = retriever.get_file_context(
            file_path=file_path,
            max_chunks=max_chunks,
        )

        return {
            "file_path": file_path,
            "total_chunks": len(chunks),
            "chunks": [
                {
                    "line_start": chunk["metadata"]["line_start"],
                    "line_end": chunk["metadata"]["line_end"],
                    "content": chunk["content"],
                    "score": chunk["score"],
                }
                for chunk in chunks
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get file chunks: {str(e)}",
        )

# Made with Bob
