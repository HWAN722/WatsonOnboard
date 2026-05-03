"""
Unit tests for API routes.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


@patch("src.api.routes.analyze.FileWalker")
@patch("src.api.routes.analyze.LanguageDetector")
@patch("src.api.routes.analyze.ASTParser")
def test_analyze_endpoint(mock_parser, mock_detector, mock_walker, client):
    """Test the analyze endpoint."""
    # Mock the scanner components
    mock_walker.return_value.walk.return_value = []
    mock_detector.return_value.detect.return_value = "python"
    mock_parser.return_value.parse.return_value = None
    
    response = client.post(
        "/api/analyze",
        json={"repo_path": "/test/path"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"


def test_analyze_endpoint_invalid_path(client):
    """Test analyze endpoint with invalid path."""
    response = client.post(
        "/api/analyze",
        json={"repo_path": "/nonexistent/path"}
    )
    
    # Should still create a job, validation happens in background
    assert response.status_code == 200


def test_get_job_status_not_found(client):
    """Test getting status of non-existent job."""
    response = client.get("/api/analyze/nonexistent-job-id")
    assert response.status_code == 404


@patch("src.api.routes.query.VectorStore")
@patch("src.api.routes.query.Retriever")
def test_query_endpoint(mock_retriever_class, mock_vector_store, client):
    """Test the query endpoint."""
    # Mock the retriever
    mock_retriever = Mock()
    mock_retriever.answer_question.return_value = "Test answer"
    mock_retriever_class.return_value = mock_retriever
    
    # Mock vector store to have data
    mock_store = Mock()
    mock_store.collection.count.return_value = 10
    mock_vector_store.return_value = mock_store
    
    response = client.post(
        "/api/query",
        json={"question": "How does this work?", "top_k": 5}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["answer"] == "Test answer"


def test_query_endpoint_no_index(client):
    """Test query endpoint when no codebase is indexed."""
    with patch("src.api.routes.query.VectorStore") as mock_vector_store:
        mock_store = Mock()
        mock_store.collection.count.return_value = 0
        mock_vector_store.return_value = mock_store
        
        response = client.post(
            "/api/query",
            json={"question": "How does this work?"}
        )
        
        assert response.status_code == 400


@patch("src.api.routes.query.VectorStore")
@patch("src.api.routes.query.Embedder")
def test_search_endpoint(mock_embedder_class, mock_vector_store, client):
    """Test the semantic search endpoint."""
    # Mock embedder
    mock_embedder = Mock()
    mock_embedder.embed.return_value = [0.1] * 768
    mock_embedder_class.return_value = mock_embedder
    
    # Mock vector store
    mock_store = Mock()
    mock_store.collection.count.return_value = 10
    mock_store.search.return_value = []
    mock_vector_store.return_value = mock_store
    
    response = client.post(
        "/api/search",
        json={"query": "database connection", "top_k": 5}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert isinstance(data["results"], list)


def test_list_jobs_endpoint(client):
    """Test listing all jobs."""
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


def test_delete_job_endpoint(client):
    """Test deleting a job."""
    # First create a job
    with patch("src.api.routes.analyze.FileWalker"):
        response = client.post(
            "/api/analyze",
            json={"repo_path": "/test/path"}
        )
        job_id = response.json()["job_id"]
    
    # Then delete it
    response = client.delete(f"/api/analyze/{job_id}")
    assert response.status_code == 200
    
    # Verify it's deleted
    response = client.get(f"/api/analyze/{job_id}")
    assert response.status_code == 404


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.options("/health")
    assert "access-control-allow-origin" in response.headers


def test_api_validation():
    """Test API request validation."""
    client = TestClient(app)
    
    # Missing required field
    response = client.post("/api/analyze", json={})
    assert response.status_code == 422
    
    # Invalid type
    response = client.post(
        "/api/query",
        json={"question": 123}  # Should be string
    )
    assert response.status_code == 422

# Made with Bob
