import pytest
from pathlib import Path
import json
import os
from unittest.mock import patch, MagicMock
from cursor_ai.core import (
    CursorAIClient,
    AIServiceType,
    AIRequestType,
    AIRequest,
    AIResponse
)


@pytest.fixture
def client(tmp_path):
    """Create a CursorAIClient instance with a temporary config directory."""
    config_dir = tmp_path / ".cursor_ai"
    with patch.dict(os.environ, {"CURSOR_AI_API_KEY": "test_key"}):
        return CursorAIClient(str(config_dir))


@pytest.fixture
def sample_code():
    """Sample code for testing."""
    return """
def add(a: int, b: int) -> int:
    return a + b
"""


@pytest.fixture
def mock_response():
    """Mock successful API response."""
    return {
        "content": "Code looks good!",
        "suggestions": ["Add docstring", "Add type hints"],
        "confidence": 0.95,
        "metadata": {"time_taken": 0.5}
    }


def test_client_initialization(client):
    """Test CursorAIClient initialization."""
    assert client.config_dir.exists()
    assert client.config_dir.is_dir()
    assert client.default_service == AIServiceType.CURSOR


def test_save_service_config(client):
    """Test saving service configuration."""
    config = {
        "model": "gpt-4",
        "temperature": 0.7
    }

    assert client.save_service_config(AIServiceType.OPENAI, config)

    config_file = client.config_dir / "services.json"
    assert config_file.exists()

    with open(config_file) as f:
        saved_config = json.load(f)
        assert saved_config["openai"] == config


def test_validate_code_no_api_key():
    """Test code validation without API key."""
    with patch.dict(os.environ, {}, clear=True):
        client = CursorAIClient()
        response = client.validate_code("test code")

        assert not response.success
        assert "API key not configured" in response.content
        assert response.confidence == 0.0


@patch("requests.post")
def test_validate_code_success(mock_post, client, sample_code, mock_response):
    """Test successful code validation."""
    # Set up mock
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: mock_response
    )

    response = client.validate_code(sample_code)

    assert response.success
    assert response.content == mock_response["content"]
    assert response.suggestions == mock_response["suggestions"]
    assert response.confidence == mock_response["confidence"]
    assert response.metadata == mock_response["metadata"]

    # Verify request
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0].endswith("/validation")
    assert call_args[1]["headers"]["Authorization"] == "Bearer test_key"


@patch("requests.post")
def test_review_code(mock_post, client, sample_code, mock_response):
    """Test code review functionality."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: mock_response
    )

    response = client.review_code(sample_code)

    assert response.success
    assert response.content == mock_response["content"]

    mock_post.assert_called_once()
    assert mock_post.call_args[0][0].endswith("/code_review")


@patch("requests.post")
def test_get_suggestions(mock_post, client, mock_response):
    """Test getting suggestions."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: mock_response
    )

    response = client.get_suggestions("How to improve this code?")

    assert response.success
    assert response.suggestions == mock_response["suggestions"]

    mock_post.assert_called_once()
    assert mock_post.call_args[0][0].endswith("/suggestion")


@patch("requests.post")
def test_generate_documentation(mock_post, client, sample_code, mock_response):
    """Test documentation generation."""
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: mock_response
    )

    response = client.generate_documentation(sample_code)

    assert response.success
    assert response.content == mock_response["content"]

    mock_post.assert_called_once()
    assert mock_post.call_args[0][0].endswith("/documentation")


def test_context_caching(client, tmp_path):
    """Test context file caching functionality."""
    # Create test files
    file1 = tmp_path / "test1.py"
    file2 = tmp_path / "test2.py"

    file1.write_text("def test1(): pass")
    file2.write_text("def test2(): pass")

    files = [str(file1), str(file2)]

    # Cache context
    cache_id = client.cache_context(files)
    assert cache_id

    # Retrieve cached context
    cached_data = client.get_cached_context(cache_id)
    assert len(cached_data) == 2
    assert cached_data[str(file1)] == "def test1(): pass"
    assert cached_data[str(file2)] == "def test2(): pass"


def test_error_handling(client):
    """Test error handling in requests."""
    with patch("requests.post") as mock_post:
        # Simulate network error
        mock_post.side_effect = Exception("Network error")

        response = client.validate_code("test code")

        assert not response.success
        assert "Network error" in response.content
        assert response.confidence == 0.0


def test_invalid_cache_id(client):
    """Test retrieving non-existent cached context."""
    cached_data = client.get_cached_context("nonexistent")
    assert cached_data == {}
