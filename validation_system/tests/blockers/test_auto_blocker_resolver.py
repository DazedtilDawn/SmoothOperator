import pytest
from unittest.mock import Mock, patch
from validation_system.blockers.auto_blocker_resolver import BlockerResolver


@pytest.fixture
def resolver():
    return BlockerResolver()


@pytest.fixture
def mock_lmstudio_client():
    with patch('validation_system.blockers.auto_blocker_resolver.LMStudioClient') as mock:
        client = Mock()
        mock.return_value = client
        yield client


def test_resolve_blockers_empty_list(resolver):
    """Test that an empty list of blockers returns an empty list."""
    assert resolver.resolve_blockers([]) == []


def test_resolve_blockers_no_diagnostics(resolver):
    """Test resolving blockers without diagnostics."""
    blockers = [
        {
            "type": "TestBlocker",
            "resolution": {
                "required_experts": []
            }
        }
    ]
    assert resolver.resolve_blockers(blockers) == []


def test_resolve_blockers_with_failed_diagnostics(resolver):
    """Test resolving blockers with failing diagnostics."""
    blockers = [
        {
            "type": "TestBlocker",
            "resolution": {
                "diagnostics": "exit 1"
            }
        }
    ]
    unresolved = resolver.resolve_blockers(blockers)
    assert len(unresolved) == 1
    assert unresolved[0]["type"] == "TestBlocker"


def test_resolve_blockers_with_successful_diagnostics(resolver):
    """Test resolving blockers with successful diagnostics."""
    blockers = [
        {
            "type": "TestBlocker",
            "resolution": {
                "diagnostics": "echo '{\"status\": \"success\"}'"
            }
        }
    ]
    assert resolver.resolve_blockers(blockers) == []


def test_resolve_blockers_with_lmstudio_prompt(resolver, mock_lmstudio_client):
    """Test resolving blockers using LMStudio prompts."""
    mock_lmstudio_client.generate_prompt.return_value = "Task resolved successfully"

    blockers = [
        {
            "type": "TestBlocker",
            "resolution": {
                "lmstudio_prompt": "Test prompt"
            }
        }
    ]
    assert resolver.resolve_blockers(blockers) == []

    mock_lmstudio_client.generate_prompt.assert_called_once()


def test_resolve_blockers_with_required_experts(resolver):
    """Test resolving blockers that require experts."""
    blockers = [
        {
            "type": "TestBlocker",
            "resolution": {
                "required_experts": ["Python Developer"]
            }
        }
    ]
    unresolved = resolver.resolve_blockers(blockers)
    assert len(unresolved) == 1
    assert unresolved[0]["type"] == "TestBlocker"
