from unittest.mock import Mock

import anthropic
import pytest


@pytest.fixture
def mock_anthropic_client(monkeypatch):
    mock_client = Mock(spec=anthropic.Anthropic)
    mock_messages = Mock()
    mock_client.messages = mock_messages
    monkeypatch.setattr("codeaide.utils.api_utils.client", mock_client)
    return mock_client
