"""Pytest configuration and shared fixtures."""

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Return the test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_repo_dir(test_data_dir: Path) -> Path:
    """Return the sample repository directory."""
    return test_data_dir / "sample_repo"


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path: Path, monkeypatch):
    """Set up test environment variables."""
    # Use temporary directories for cache and chroma
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / ".cache"))
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / ".chroma"))
    
    # Set dummy Watsonx credentials for tests
    monkeypatch.setenv("WATSONX_API_KEY", "test-api-key")
    monkeypatch.setenv("WATSONX_URL", "https://test.watsonx.com")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "test-project-id")

# Made with Bob
