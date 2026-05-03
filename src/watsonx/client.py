"""IBM Watsonx API client wrapper."""

import time
from typing import Any, Optional

import structlog

from src.config import settings

logger = structlog.get_logger()

# Try to import IBM Watsonx SDK
try:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.foundation_models.embeddings import Embeddings
    
    WATSONX_AVAILABLE = True
except ImportError:
    WATSONX_AVAILABLE = False
    logger.warning("ibm-watsonx-ai not installed. Install with: pip install ibm-watsonx-ai")


class WatsonxClient:
    """Client for IBM Watsonx API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        url: Optional[str] = None,
        project_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> None:
        """
        Initialize Watsonx client.
        
        Args:
            api_key: IBM Watsonx API key (uses config if None)
            url: Watsonx service URL (uses config if None)
            project_id: Project ID (uses config if None)
            model_id: Model ID to use (uses config if None)
        """
        if not WATSONX_AVAILABLE:
            raise ImportError(
                "ibm-watsonx-ai is required. Install with: pip install ibm-watsonx-ai"
            )

        self.api_key = api_key or settings.watsonx_api_key
        self.url = url or settings.watsonx_url
        self.project_id = project_id or settings.watsonx_project_id
        self.model_id = model_id or settings.watsonx_model

        # Initialize credentials
        self.credentials = Credentials(
            url=self.url,
            api_key=self.api_key,
        )

        # Initialize model inference
        self._model: Optional[Any] = None
        self._embeddings: Optional[Any] = None

    def _get_model(self) -> Any:
        """Get or create model inference instance."""
        if self._model is None:
            params = {
                "max_new_tokens": settings.max_new_tokens,
                "temperature": settings.temperature,
            }

            self._model = ModelInference(
                model_id=self.model_id,
                credentials=self.credentials,
                project_id=self.project_id,
                params=params,
            )

        return self._model

    def _get_embeddings(self) -> Any:
        """Get or create embeddings instance."""
        if self._embeddings is None:
            self._embeddings = Embeddings(
                model_id=settings.watsonx_embedding_model,
                credentials=self.credentials,
                project_id=self.project_id,
            )

        return self._embeddings

    def generate(
        self,
        prompt: str,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        max_retries: int = 3,
    ) -> str:
        """
        Generate text using Watsonx LLM.
        
        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            max_retries: Maximum number of retries on failure
            
        Returns:
            Generated text
            
        Raises:
            Exception: If generation fails after retries
        """
        model = self._get_model()

        # Override parameters if provided
        params = {}
        if max_new_tokens is not None:
            params["max_new_tokens"] = max_new_tokens
        if temperature is not None:
            params["temperature"] = temperature

        # Retry logic with exponential backoff
        for attempt in range(max_retries):
            try:
                if params:
                    # Update model params temporarily
                    original_params = model.params
                    model.params = {**original_params, **params}

                response = model.generate_text(prompt=prompt)

                if params:
                    # Restore original params
                    model.params = original_params

                logger.info(
                    "watsonx_generate_success",
                    prompt_length=len(prompt),
                    response_length=len(response),
                )

                return response

            except Exception as e:
                logger.warning(
                    "watsonx_generate_error",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    error=str(e),
                )

                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    raise

        return ""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
            
        Raises:
            Exception: If embedding fails
        """
        if not texts:
            return []

        embeddings_model = self._get_embeddings()

        try:
            # Generate embeddings
            result = embeddings_model.embed_documents(texts)

            logger.info(
                "watsonx_embed_success",
                num_texts=len(texts),
                embedding_dim=len(result[0]) if result else 0,
            )

            return result

        except Exception as e:
            logger.error("watsonx_embed_error", error=str(e))
            raise

    def ping(self) -> bool:
        """
        Test connection to Watsonx.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try a minimal generation request
            self.generate("test", max_new_tokens=1)
            return True
        except Exception as e:
            logger.error("watsonx_ping_failed", error=str(e))
            return False


# Global client instance
_client_instance: Optional[WatsonxClient] = None


def get_client() -> WatsonxClient:
    """
    Get the global Watsonx client instance.
    
    Returns:
        WatsonxClient instance
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = WatsonxClient()
    return _client_instance


def generate_text(prompt: str, **kwargs: Any) -> str:
    """
    Generate text using the global client.
    
    Args:
        prompt: Input prompt
        **kwargs: Additional arguments for generate()
        
    Returns:
        Generated text
    """
    client = get_client()
    return client.generate(prompt, **kwargs)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using the global client.
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    client = get_client()
    return client.embed(texts)

# Made with Bob
