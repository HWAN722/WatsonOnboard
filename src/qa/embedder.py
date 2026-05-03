"""Text embedding generation for semantic search."""

from typing import Any, Optional

import structlog

from src.config import settings
from src.watsonx.client import get_client

logger = structlog.get_logger()

# Try to import sentence-transformers as fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class Embedder:
    """Generate text embeddings for semantic search."""

    def __init__(
        self,
        use_watsonx: bool = True,
        fallback_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        """
        Initialize the embedder.
        
        Args:
            use_watsonx: Whether to use Watsonx for embeddings
            fallback_model: Fallback model if Watsonx unavailable
        """
        self.use_watsonx = use_watsonx
        self.fallback_model_name = fallback_model
        
        self._watsonx_client: Optional[Any] = None
        self._fallback_model: Optional[Any] = None
        
        # Try to initialize Watsonx
        if use_watsonx:
            try:
                self._watsonx_client = get_client()
                logger.info("embedder_init", backend="watsonx")
            except Exception as e:
                logger.warning("watsonx_init_failed", error=str(e))
                self.use_watsonx = False
        
        # Initialize fallback if needed
        if not self.use_watsonx:
            self._init_fallback()

    def _init_fallback(self) -> None:
        """Initialize fallback embedding model."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for fallback embeddings. "
                "Install with: pip install sentence-transformers"
            )
        
        try:
            self._fallback_model = SentenceTransformer(self.fallback_model_name)
            logger.info("embedder_init", backend="sentence-transformers")
        except Exception as e:
            logger.error("fallback_init_failed", error=str(e))
            raise

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            if self.use_watsonx and self._watsonx_client:
                return self._embed_watsonx(texts)
            else:
                return self._embed_fallback(texts)
        except Exception as e:
            logger.error("embed_failed", error=str(e), num_texts=len(texts))
            raise

    def _embed_watsonx(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Watsonx."""
        try:
            embeddings = self._watsonx_client.embed(texts)
            logger.debug(
                "embed_success",
                backend="watsonx",
                num_texts=len(texts),
                dim=len(embeddings[0]) if embeddings else 0,
            )
            return embeddings
        except Exception as e:
            logger.warning("watsonx_embed_failed", error=str(e))
            # Try fallback
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                logger.info("falling_back_to_local")
                self._init_fallback()
                self.use_watsonx = False
                return self._embed_fallback(texts)
            raise

    def _embed_fallback(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using sentence-transformers."""
        if not self._fallback_model:
            self._init_fallback()
        
        embeddings = self._fallback_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        
        # Convert to list of lists
        result = embeddings.tolist()
        
        logger.debug(
            "embed_success",
            backend="sentence-transformers",
            num_texts=len(texts),
            dim=len(result[0]) if result else 0,
        )
        
        return result

    def embed_single(self, text: str) -> list[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.embed([text])
        return embeddings[0] if embeddings else []

    def get_embedding_dim(self) -> int:
        """
        Get the dimensionality of embeddings.
        
        Returns:
            Embedding dimension
        """
        # Test with a dummy text
        test_embedding = self.embed_single("test")
        return len(test_embedding)


# Global embedder instance
_embedder_instance: Optional[Embedder] = None


def get_embedder(use_watsonx: bool = True) -> Embedder:
    """
    Get the global embedder instance.
    
    Args:
        use_watsonx: Whether to use Watsonx
        
    Returns:
        Embedder instance
    """
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = Embedder(use_watsonx=use_watsonx)
    return _embedder_instance


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using the global embedder.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    embedder = get_embedder()
    return embedder.embed(texts)


def embed_text(text: str) -> list[float]:
    """
    Generate embedding for a single text using the global embedder.
    
    Args:
        text: Text to embed
        
    Returns:
        Embedding vector
    """
    embedder = get_embedder()
    return embedder.embed_single(text)

# Made with Bob
