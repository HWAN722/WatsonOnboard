"""Vector store for semantic search using ChromaDB."""

from pathlib import Path
from typing import Any, Optional

import structlog

from src.config import settings
from src.qa.embedder import get_embedder
from src.watsonx.chunker import CodeChunk

logger = structlog.get_logger()

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


class VectorStore:
    """Vector store for code chunks using ChromaDB."""

    def __init__(
        self,
        collection_name: str = "code_chunks",
        persist_directory: Optional[Path] = None,
    ) -> None:
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory for persistent storage
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb is required. Install with: pip install chromadb"
            )

        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.chroma_dir

        # Ensure directory exists
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Code chunks for semantic search"},
        )

        # Initialize embedder
        self.embedder = get_embedder()

        logger.info(
            "vector_store_init",
            collection=collection_name,
            persist_dir=str(self.persist_directory),
        )

    def upsert_chunks(self, chunks: list[CodeChunk]) -> None:
        """
        Add or update code chunks in the vector store.
        
        Args:
            chunks: List of code chunks to upsert
        """
        if not chunks:
            return

        # Prepare data
        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for i, chunk in enumerate(chunks):
            # Create unique ID
            chunk_id = f"{chunk.file_path}:{chunk.line_start}-{chunk.line_end}"
            ids.append(chunk_id)

            # Document is the code content
            documents.append(chunk.content)

            # Metadata
            metadatas.append({
                "file_path": chunk.file_path,
                "language": chunk.language,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "token_count": chunk.token_count,
            })

        # Generate embeddings
        try:
            embeddings = self.embedder.embed(documents)
        except Exception as e:
            logger.error("embedding_failed", error=str(e))
            raise

        # Upsert to collection
        try:
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )

            logger.info("chunks_upserted", count=len(chunks))

        except Exception as e:
            logger.error("upsert_failed", error=str(e))
            raise

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter_dict: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Query the vector store for similar code chunks.
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of results with content, metadata, and scores
        """
        # Generate query embedding
        try:
            query_embedding = self.embedder.embed_single(query_text)
        except Exception as e:
            logger.error("query_embedding_failed", error=str(e))
            raise

        # Query collection
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filter_dict,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            formatted_results = []

            if results and results["ids"]:
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "score": 1 / (1 + results["distances"][0][i]),  # Convert distance to similarity
                    })

            logger.info(
                "query_success",
                query_length=len(query_text),
                results_count=len(formatted_results),
            )

            return formatted_results

        except Exception as e:
            logger.error("query_failed", error=str(e))
            raise

    def delete_by_file(self, file_path: str) -> None:
        """
        Delete all chunks for a specific file.
        
        Args:
            file_path: Path to the file
        """
        try:
            self.collection.delete(
                where={"file_path": file_path}
            )
            logger.info("chunks_deleted", file_path=file_path)
        except Exception as e:
            logger.warning("delete_failed", file_path=file_path, error=str(e))

    def clear(self) -> None:
        """Clear all data from the collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Code chunks for semantic search"},
            )
            logger.info("collection_cleared")
        except Exception as e:
            logger.error("clear_failed", error=str(e))
            raise

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with stats
        """
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "persist_directory": str(self.persist_directory),
            }
        except Exception as e:
            logger.error("stats_failed", error=str(e))
            return {
                "collection_name": self.collection_name,
                "total_chunks": 0,
                "persist_directory": str(self.persist_directory),
            }


# Global vector store instance
_vector_store_instance: Optional[VectorStore] = None


def get_vector_store(collection_name: str = "code_chunks") -> VectorStore:
    """
    Get the global vector store instance.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        VectorStore instance
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(collection_name=collection_name)
    return _vector_store_instance


def upsert_code_chunks(chunks: list[CodeChunk]) -> None:
    """
    Upsert code chunks using the global vector store.
    
    Args:
        chunks: List of code chunks
    """
    store = get_vector_store()
    store.upsert_chunks(chunks)


def search_code(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Search for code chunks using the global vector store.
    
    Args:
        query: Search query
        top_k: Number of results
        
    Returns:
        List of search results
    """
    store = get_vector_store()
    return store.query(query, top_k=top_k)

# Made with Bob
