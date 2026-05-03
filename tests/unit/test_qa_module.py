"""
Unit tests for Q&A module (embedder, vector store, retriever).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from src.qa.embedder import Embedder
from src.qa.vector_store import VectorStore
from src.qa.retriever import Retriever
from src.scanner.models import CodeChunk


@pytest.fixture
def mock_watsonx_client():
    """Create a mock Watsonx client."""
    client = Mock()
    client.embed.return_value = [0.1] * 768
    client.generate.return_value = "Test response"
    return client


@pytest.fixture
def sample_chunk():
    """Create a sample code chunk."""
    return CodeChunk(
        file_path="test.py",
        start_line=1,
        end_line=10,
        content="def test():\n    pass",
        chunk_type="function",
        language="python",
    )


class TestEmbedder:
    """Tests for the Embedder class."""
    
    def test_embed_single_text(self, mock_watsonx_client):
        """Test embedding a single text."""
        embedder = Embedder(mock_watsonx_client)
        
        text = "This is a test"
        embedding = embedder.embed(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        mock_watsonx_client.embed.assert_called_once()
    
    def test_embed_multiple_texts(self, mock_watsonx_client):
        """Test embedding multiple texts."""
        embedder = Embedder(mock_watsonx_client)
        
        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = embedder.embed_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
    
    def test_embed_empty_text(self, mock_watsonx_client):
        """Test embedding empty text."""
        embedder = Embedder(mock_watsonx_client)
        
        with pytest.raises(ValueError):
            embedder.embed("")
    
    def test_embed_with_cache(self, mock_watsonx_client):
        """Test that embeddings are cached."""
        embedder = Embedder(mock_watsonx_client)
        
        text = "Test text"
        
        # First call
        embedding1 = embedder.embed(text)
        
        # Second call should use cache
        embedding2 = embedder.embed(text)
        
        assert embedding1 == embedding2
        # Should only call the client once
        assert mock_watsonx_client.embed.call_count == 1


class TestVectorStore:
    """Tests for the VectorStore class."""
    
    @patch("src.qa.vector_store.chromadb")
    def test_initialization(self, mock_chromadb):
        """Test vector store initialization."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        store = VectorStore()
        
        assert store.collection == mock_collection
        mock_chromadb.PersistentClient.assert_called_once()
    
    @patch("src.qa.vector_store.chromadb")
    def test_add_chunk(self, mock_chromadb, sample_chunk):
        """Test adding a chunk to the vector store."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        store = VectorStore()
        embedding = [0.1] * 768
        
        store.add_chunk(sample_chunk, embedding)
        
        mock_collection.add.assert_called_once()
        call_args = mock_collection.add.call_args
        assert "ids" in call_args[1]
        assert "embeddings" in call_args[1]
        assert "documents" in call_args[1]
        assert "metadatas" in call_args[1]
    
    @patch("src.qa.vector_store.chromadb")
    def test_search(self, mock_chromadb):
        """Test searching the vector store."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.query.return_value = {
            "ids": [["id1", "id2"]],
            "distances": [[0.1, 0.2]],
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"file_path": "test.py"}, {"file_path": "test2.py"}]],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        store = VectorStore()
        query_embedding = [0.1] * 768
        
        results = store.search(query_embedding, top_k=2)
        
        assert len(results) == 2
        assert all("chunk" in r for r in results)
        assert all("score" in r for r in results)
        mock_collection.query.assert_called_once()
    
    @patch("src.qa.vector_store.chromadb")
    def test_get_chunks_by_file(self, mock_chromadb):
        """Test getting all chunks for a specific file."""
        mock_client = Mock()
        mock_collection = Mock()
        mock_collection.get.return_value = {
            "ids": ["id1", "id2"],
            "documents": ["doc1", "doc2"],
            "metadatas": [
                {"file_path": "test.py", "start_line": 1},
                {"file_path": "test.py", "start_line": 10},
            ],
        }
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        store = VectorStore()
        chunks = store.get_chunks_by_file("test.py")
        
        assert len(chunks) == 2
        mock_collection.get.assert_called_once()


class TestRetriever:
    """Tests for the Retriever class."""
    
    @patch("src.qa.retriever.VectorStore")
    def test_answer_question(self, mock_vector_store_class, mock_watsonx_client):
        """Test answering a question."""
        # Mock vector store
        mock_store = Mock()
        mock_store.search.return_value = [
            {
                "chunk": CodeChunk(
                    file_path="test.py",
                    start_line=1,
                    end_line=5,
                    content="def test(): pass",
                    chunk_type="function",
                    language="python",
                ),
                "score": 0.9,
            }
        ]
        mock_vector_store_class.return_value = mock_store
        
        retriever = Retriever(mock_store, mock_watsonx_client)
        
        question = "How does the test function work?"
        answer = retriever.answer_question(question, top_k=5)
        
        assert isinstance(answer, str)
        assert len(answer) > 0
        mock_store.search.assert_called_once()
        mock_watsonx_client.generate.assert_called_once()
    
    @patch("src.qa.retriever.VectorStore")
    def test_answer_question_no_results(self, mock_vector_store_class, mock_watsonx_client):
        """Test answering when no relevant chunks are found."""
        mock_store = Mock()
        mock_store.search.return_value = []
        mock_vector_store_class.return_value = mock_store
        
        retriever = Retriever(mock_store, mock_watsonx_client)
        
        question = "How does this work?"
        answer = retriever.answer_question(question, top_k=5)
        
        assert "no relevant" in answer.lower() or "not found" in answer.lower()
    
    @patch("src.qa.retriever.VectorStore")
    def test_search_similar_code(self, mock_vector_store_class, mock_watsonx_client):
        """Test searching for similar code."""
        mock_store = Mock()
        mock_store.search.return_value = [
            {
                "chunk": CodeChunk(
                    file_path="test.py",
                    start_line=1,
                    end_line=5,
                    content="def test(): pass",
                    chunk_type="function",
                    language="python",
                ),
                "score": 0.9,
            }
        ]
        mock_vector_store_class.return_value = mock_store
        
        retriever = Retriever(mock_store, mock_watsonx_client)
        
        query = "database connection"
        results = retriever.search_similar_code(query, top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        mock_store.search.assert_called_once()


def test_integration_embedder_vector_store(mock_watsonx_client, sample_chunk):
    """Integration test for embedder and vector store."""
    with patch("src.qa.vector_store.chromadb") as mock_chromadb:
        # Setup mocks
        mock_client = Mock()
        mock_collection = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.PersistentClient.return_value = mock_client
        
        # Create components
        embedder = Embedder(mock_watsonx_client)
        vector_store = VectorStore()
        
        # Embed and store
        embedding = embedder.embed(sample_chunk.content)
        vector_store.add_chunk(sample_chunk, embedding)
        
        # Verify
        mock_collection.add.assert_called_once()
        assert mock_watsonx_client.embed.called

# Made with Bob
