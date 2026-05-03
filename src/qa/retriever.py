"""Retrieve and answer questions about code using RAG."""

from typing import Any, Optional

import structlog

from src.qa.vector_store import get_vector_store
from src.watsonx.client import get_client
from src.watsonx.prompts import create_qa_answer_prompt

logger = structlog.get_logger()


class CodeRetriever:
    """Retrieve code context and answer questions using RAG."""

    def __init__(
        self,
        collection_name: str = "code_chunks",
        top_k: int = 5,
    ) -> None:
        """
        Initialize the retriever.
        
        Args:
            collection_name: ChromaDB collection name
            top_k: Number of chunks to retrieve
        """
        self.collection_name = collection_name
        self.top_k = top_k

        # Initialize components
        self.vector_store = get_vector_store(collection_name)
        
        try:
            self.llm_client = get_client()
        except Exception as e:
            logger.warning("llm_init_failed", error=str(e))
            self.llm_client = None

    def answer(
        self,
        question: str,
        top_k: Optional[int] = None,
        include_citations: bool = True,
    ) -> dict[str, Any]:
        """
        Answer a question about the codebase.
        
        Args:
            question: User's question
            top_k: Number of chunks to retrieve (uses default if None)
            include_citations: Whether to include source citations
            
        Returns:
            Dictionary with answer and optional citations
        """
        k = top_k or self.top_k

        logger.info("answer_start", question=question, top_k=k)

        # Step 1: Retrieve relevant code chunks
        try:
            results = self.vector_store.query(question, top_k=k)
        except Exception as e:
            logger.error("retrieval_failed", error=str(e))
            return {
                "answer": "Sorry, I encountered an error while searching the codebase.",
                "citations": [],
                "error": str(e),
            }

        if not results:
            logger.info("no_results_found")
            return {
                "answer": "I couldn't find any relevant information in the codebase to answer your question.",
                "citations": [],
            }

        # Step 2: Prepare context for LLM
        context_chunks = []
        citations = []

        for result in results:
            metadata = result["metadata"]
            context_chunks.append({
                "file_path": metadata["file_path"],
                "language": metadata["language"],
                "line_start": metadata["line_start"],
                "line_end": metadata["line_end"],
                "content": result["content"],
            })

            if include_citations:
                citations.append({
                    "file_path": metadata["file_path"],
                    "line_start": metadata["line_start"],
                    "line_end": metadata["line_end"],
                    "score": result["score"],
                })

        # Step 3: Generate answer with LLM
        if self.llm_client:
            try:
                answer = self._generate_answer(question, context_chunks)
            except Exception as e:
                logger.error("answer_generation_failed", error=str(e))
                answer = self._fallback_answer(context_chunks)
        else:
            answer = self._fallback_answer(context_chunks)

        logger.info("answer_complete", answer_length=len(answer))

        return {
            "answer": answer,
            "citations": citations if include_citations else [],
            "num_chunks_used": len(context_chunks),
        }

    def _generate_answer(
        self, question: str, context_chunks: list[dict[str, Any]]
    ) -> str:
        """Generate answer using LLM."""
        # Create prompt
        prompt = create_qa_answer_prompt(
            question=question,
            context_chunks=context_chunks,
        )

        # Generate answer
        answer = self.llm_client.generate(
            prompt,
            max_new_tokens=500,
            temperature=0.3,
        )

        return answer.strip()

    def _fallback_answer(self, context_chunks: list[dict[str, Any]]) -> str:
        """Generate fallback answer without LLM."""
        if not context_chunks:
            return "No relevant code found."

        # Simple fallback: list the relevant files
        files = set(chunk["file_path"] for chunk in context_chunks)
        
        answer = "Based on the codebase, here are the relevant files:\n\n"
        for file_path in sorted(files):
            answer += f"- `{file_path}`\n"

        answer += "\nPlease review these files for more information."

        return answer

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """
        Search for code chunks without generating an answer.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of search results
        """
        k = top_k or self.top_k

        try:
            results = self.vector_store.query(query, top_k=k)
            logger.info("search_complete", query=query, results=len(results))
            return results
        except Exception as e:
            logger.error("search_failed", error=str(e))
            return []

    def get_file_context(
        self,
        file_path: str,
        max_chunks: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get all chunks for a specific file.
        
        Args:
            file_path: Path to the file
            max_chunks: Maximum chunks to return
            
        Returns:
            List of chunks from the file
        """
        try:
            results = self.vector_store.query(
                query_text=file_path,  # Use file path as query
                top_k=max_chunks,
                filter_dict={"file_path": file_path},
            )
            return results
        except Exception as e:
            logger.error("get_file_context_failed", error=str(e))
            return []


# Global retriever instance
_retriever_instance: Optional[CodeRetriever] = None


def get_retriever(collection_name: str = "code_chunks") -> CodeRetriever:
    """
    Get the global retriever instance.
    
    Args:
        collection_name: ChromaDB collection name
        
    Returns:
        CodeRetriever instance
    """
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = CodeRetriever(collection_name=collection_name)
    return _retriever_instance


def ask_question(question: str, top_k: int = 5) -> dict[str, Any]:
    """
    Ask a question about the codebase using the global retriever.
    
    Args:
        question: User's question
        top_k: Number of chunks to retrieve
        
    Returns:
        Dictionary with answer and citations
    """
    retriever = get_retriever()
    return retriever.answer(question, top_k=top_k)


def search_codebase(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Search the codebase using the global retriever.
    
    Args:
        query: Search query
        top_k: Number of results
        
    Returns:
        List of search results
    """
    retriever = get_retriever()
    return retriever.search(query, top_k=top_k)

# Made with Bob
