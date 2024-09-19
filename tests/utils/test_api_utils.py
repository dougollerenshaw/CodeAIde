import json
from collections import namedtuple
from unittest.mock import Mock

import pytest
from anthropic import APIError

from codeaide.utils.api_utils import (
    check_api_connection,
    parse_response,
    send_api_request,
)
from codeaide.utils.constants import AI_MODEL, MAX_TOKENS, SYSTEM_PROMPT

# Mock Response object
Response = namedtuple("Response", ["content"])
TextBlock = namedtuple("TextBlock", ["text"])

pytestmark = [
    pytest.mark.send_api_request,
    pytest.mark.parse_response,
    pytest.mark.api_connection,
]


class TestSendAPIRequest:
    def test_send_api_request_success(self, mock_anthropic_client):
        conversation_history = [{"role": "user", "content": "Hello, Claude!"}]
        mock_response = Mock()
        mock_response.content = [Mock(text="Hello! How can I assist you today?")]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = send_api_request(conversation_history)

        mock_anthropic_client.messages.create.assert_called_once_with(
            model=AI_MODEL,
            max_tokens=MAX_TOKENS,
            messages=conversation_history,
            system=SYSTEM_PROMPT,
        )
        assert result == mock_response

    def test_send_api_request_empty_response(self, mock_anthropic_client):
        conversation_history = [{"role": "user", "content": "Hello, Claude!"}]
        mock_response = Mock()
        mock_response.content = []
        mock_anthropic_client.messages.create.return_value = mock_response

        result = send_api_request(conversation_history)

        assert result == (None, True)

    def test_send_api_request_api_error(self, mock_anthropic_client):
        conversation_history = [{"role": "user", "content": "Hello, Claude!"}]
        mock_request = Mock()
        mock_anthropic_client.messages.create.side_effect = APIError(
            request=mock_request,
            message="API Error",
            body={"error": {"message": "API Error"}},
        )

        result = send_api_request(conversation_history)

        assert result == (None, True)

    def test_send_api_request_custom_max_tokens(self, mock_anthropic_client):
        conversation_history = [{"role": "user", "content": "Hello, Claude!"}]
        custom_max_tokens = 500
        mock_response = Mock()
        mock_response.content = [Mock(text="Hello! How can I assist you today?")]
        mock_anthropic_client.messages.create.return_value = mock_response

        result = send_api_request(conversation_history, max_tokens=custom_max_tokens)

        mock_anthropic_client.messages.create.assert_called_once_with(
            model=AI_MODEL,
            max_tokens=custom_max_tokens,
            messages=conversation_history,
            system=SYSTEM_PROMPT,
        )
        assert result == mock_response


class TestParseResponse:
    def test_parse_response_empty(self):
        result = parse_response(None)
        assert result == (None, None, None, None, None, None)

    def test_parse_response_no_content(self):
        response = Response(content=[])
        result = parse_response(response)
        assert result == (None, None, None, None, None, None)

    def test_parse_response_valid(self):
        content = {
            "text": "Sample text",
            "code": "print('Hello, World!')",
            "code_version": "1.0",
            "version_description": "Initial version",
            "requirements": ["pytest"],
            "questions": ["What does this code do?"],
        }
        response = Response(content=[TextBlock(text=json.dumps(content))])
        (
            text,
            questions,
            code,
            code_version,
            version_description,
            requirements,
        ) = parse_response(response)

        assert text == "Sample text"
        assert questions == ["What does this code do?"]
        assert code == "print('Hello, World!')"
        assert code_version == "1.0"
        assert version_description == "Initial version"
        assert requirements == ["pytest"]

    def test_parse_response_missing_fields(self):
        content = {"text": "Sample text", "code": "print('Hello, World!')"}
        response = Response(content=[TextBlock(text=json.dumps(content))])
        (
            text,
            questions,
            code,
            code_version,
            version_description,
            requirements,
        ) = parse_response(response)

        assert text == "Sample text"
        assert questions == []
        assert code == "print('Hello, World!')"
        assert code_version is None
        assert version_description is None
        assert requirements == []

    def test_parse_response_complex_code(self):
        content = {
            "text": "Complex code example",
            "code": 'def hello():\n    print("Hello, World!")',
            "code_version": "1.1",
            "version_description": "Added function",
            "requirements": [],
            "questions": [],
        }
        response = Response(content=[TextBlock(text=json.dumps(content))])
        (
            text,
            questions,
            code,
            code_version,
            version_description,
            requirements,
        ) = parse_response(response)

        assert text == "Complex code example"
        assert code == 'def hello():\n    print("Hello, World!")'
        assert code_version == "1.1"
        assert version_description == "Added function"

    def test_parse_response_escaped_quotes(self):
        content = {
            "text": 'Text with "quotes"',
            "code": 'print("Hello, \\"World!\\"")\nprint(\'Single quotes\')',
            "code_version": "1.2",
            "version_description": "Added escaped quotes",
            "requirements": [],
            "questions": [],
        }
        response = Response(content=[TextBlock(text=json.dumps(content))])
        (
            text,
            questions,
            code,
            code_version,
            version_description,
            requirements,
        ) = parse_response(response)

        assert text == 'Text with "quotes"'
        assert code == 'print("Hello, \\"World!\\"")\nprint(\'Single quotes\')'
        assert code_version == "1.2"
        assert version_description == "Added escaped quotes"

    def test_parse_response_malformed_json(self):
        response = Response(content=[TextBlock(text="This is not JSON")])
        result = parse_response(response)
        assert result == (None, None, None, None, None, None)


class TestAPIConnection:
    def check_api_connection_success(self, mock_anthropic_client):
        mock_response = Mock()
        mock_response.content = [Mock(text="Yes, we are communicating.")]
        mock_anthropic_client.messages.create.return_value = mock_response
        result = check_api_connection()
        assert result[0] == True
        assert result[1] == "Yes, we are communicating."

    def check_api_connection_failure(self, mock_anthropic_client):
        mock_anthropic_client.messages.create.side_effect = Exception(
            "Connection failed"
        )
        result = check_api_connection()
        assert result[0] == False
        assert "Connection failed" in result[1]
