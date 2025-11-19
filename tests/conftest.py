"""Shared pytest fixtures for the test suite."""

from unittest.mock import Mock

import pytest

from llm_provider import LLMProviderManager


@pytest.fixture
def mock_llm_provider():
    """Create a reusable mock LLM provider."""
    mock_provider = Mock(spec=LLMProviderManager)
    mock_provider.get_provider.return_value = "gemini"
    mock_provider.validate_credentials.return_value = True
    mock_provider.get_api_credentials.return_value = {
        "api_key": "test-key",
        "model": "gemini-2.5-pro",
        "use_custom_endpoint": False,
    }
    return mock_provider
