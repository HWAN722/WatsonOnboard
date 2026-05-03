"""Configuration management using pydantic-settings."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # IBM Watsonx Configuration
    watsonx_api_key: str = Field(
        ...,
        description="IBM Watsonx API key",
    )
    watsonx_url: str = Field(
        ...,
        description="IBM Watsonx service URL",
    )
    watsonx_project_id: Optional[str] = Field(
        None,
        description="IBM Watsonx project ID",
    )
    watsonx_model: str = Field(
        default="ibm/granite-20b-code-instruct",
        description="Default LLM model to use",
    )
    watsonx_embedding_model: str = Field(
        default="ibm/slate-30m-english-rtrvr",
        description="Embedding model for vector search",
    )

    # Model Parameters
    max_new_tokens: int = Field(
        default=1024,
        description="Maximum tokens to generate",
    )
    temperature: float = Field(
        default=0.2,
        description="Sampling temperature",
    )
    top_k: int = Field(
        default=5,
        description="Top-k results for retrieval",
    )
    context_window: int = Field(
        default=8192,
        description="Model context window size",
    )

    # Cache Configuration
    cache_dir: Path = Field(
        default=Path(".cache"),
        description="Directory for caching LLM responses",
    )
    cache_ttl_days: int = Field(
        default=30,
        description="Cache time-to-live in days",
    )

    # Vector Store Configuration
    chroma_dir: Path = Field(
        default=Path(".chroma"),
        description="Directory for ChromaDB persistent storage",
    )

    # Application Settings
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    max_file_size_mb: int = Field(
        default=1,
        description="Maximum file size to process in MB",
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host",
    )
    api_port: int = Field(
        default=8000,
        description="API server port",
    )

    def __init__(self, **kwargs):  # type: ignore
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Made with Bob
