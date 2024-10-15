import json
from collections import namedtuple
from unittest.mock import Mock, patch

import pytest
from anthropic import APIError

from codeaide.utils.api_utils import (
    check_api_connection,
    parse_response,
    send_api_request,
)
from codeaide.utils.constants import (
    SYSTEM_PROMPT,
    AI_PROVIDERS,
)

# Mock Response object
Response = namedtuple("Response", ["content"])
TextBlock = namedtuple("TextBlock", ["text"])

pytestmark = [
    pytest.mark.send_api_request,
    pytest.mark.parse_response,
    pytest.mark.api_connection,
]

MAX_TOKENS = 100  # Define this at the top of the file for use in tests


@pytest.fixture
def mock_anthropic_client():
    """
    A pytest fixture that mocks the Anthropic API client.

    This fixture patches the 'anthropic.Anthropic' class and returns a mock client.
    The mock client includes a 'messages' attribute, which is also a mock object.

    Returns:
        Mock: A mock object representing the Anthropic API client.
    """
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = Mock()
        mock_messages = Mock()
        mock_client.messages = mock_messages
        mock_anthropic.return_value = mock_client
        yield mock_client


class TestSendAPIRequest:
    """
    A test class for the send_api_request function.

    This class contains test methods to verify the behavior of the send_api_request function
    under various scenarios, including successful API calls, empty responses, and API errors.
    It tests the function's interaction with both OpenAI and Anthropic APIs.

    Test methods:
    - test_send_api_request_success_openai: Verifies successful OpenAI API requests.
    - test_send_api_request_empty_response: Checks handling of empty responses from Anthropic API.
    - test_send_api_request_api_error: Tests error handling for API errors.

    Each test method uses mocking to simulate API responses and errors, ensuring
    that the send_api_request function behaves correctly in different scenarios.
    """

    @patch("openai.OpenAI")
    def test_send_api_request_success_openai(self, mock_openai):
        """
        Test that send_api_request successfully sends a request to OpenAI API
        and returns a non-None response.
        """
        conversation_history = [{"role": "user", "content": "Hello, GPT!"}]
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Hello! How can I assist you today?"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        model = list(AI_PROVIDERS["openai"]["models"].keys())[0]
        result = send_api_request(
            mock_client, conversation_history, MAX_TOKENS, model, "openai"
        )

        mock_client.chat.completions.create.assert_called_once_with(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}]
            + conversation_history,
        )
        assert result is not None

    @patch("anthropic.Anthropic")
    def test_send_api_request_empty_response(self, mock_anthropic):
        """
        Test that send_api_request returns None when receiving an empty response
        from the Anthropic API.
        """
        conversation_history = [{"role": "user", "content": "Hello, Claude!"}]
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = []  # Empty content
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        model = list(AI_PROVIDERS["anthropic"]["models"].keys())[0]
        result = send_api_request(
            mock_client, conversation_history, MAX_TOKENS, model, "anthropic"
        )

        mock_client.messages.create.assert_called_once_with(
            model=model,
            max_tokens=MAX_TOKENS,
            messages=conversation_history,
            system=SYSTEM_PROMPT,
        )
        assert result is None, "Expected None for empty response content"

    def test_send_api_request_api_error(self, mock_anthropic_client):
        """
        Test that send_api_request handles API errors correctly.

        This test simulates an APIError being raised by the Anthropic client
        and verifies that the function returns None in this case.

        Args:
            mock_anthropic_client (Mock): A mocked Anthropic client object.

        The test:
        1. Sets up a conversation history.
        2. Configures the mock client to raise an APIError.
        3. Calls send_api_request with the mocked client.
        4. Asserts that the function returns None when an APIError occurs.
        """
        conversation_history = [{"role": "user", "content": "Hello, Claude!"}]
        mock_request = Mock()
        mock_anthropic_client.messages.create.side_effect = APIError(
            request=mock_request,
            message="API Error",
            body={"error": {"message": "API Error"}},
        )

        model = list(AI_PROVIDERS["anthropic"]["models"].keys())[0]
        result = send_api_request(
            mock_anthropic_client,
            conversation_history,
            MAX_TOKENS,
            model,
            "anthropic",
        )

        assert result is None

    def test_send_api_request_custom_max_tokens(self, mock_anthropic_client):
        """
        Test the send_api_request function with a custom max_tokens value.

        This test verifies that:
        1. The function correctly uses a custom max_tokens value.
        2. The Anthropic client is called with the correct parameters.
        3. The function returns the expected mock response.

        Args:
            mock_anthropic_client (Mock): A mocked Anthropic client object.

        The test:
        1. Sets up a conversation history and custom max_tokens value.
        2. Creates a mock response from the Anthropic API.
        3. Calls send_api_request with the custom parameters.
        4. Asserts that the Anthropic client was called with the correct arguments.
        5. Verifies that the function returns the expected mock response.
        """
        conversation_history = [{"role": "user", "content": "Hello, Claude!"}]
        custom_max_tokens = 500
        mock_response = Mock()
        mock_response.content = [Mock(text="Hello! How can I assist you today?")]
        mock_anthropic_client.messages.create.return_value = mock_response

        model = list(AI_PROVIDERS["anthropic"]["models"].keys())[0]
        result = send_api_request(
            mock_anthropic_client,
            conversation_history,
            custom_max_tokens,
            model,
            "anthropic",
        )

        mock_anthropic_client.messages.create.assert_called_once_with(
            model=model,
            max_tokens=custom_max_tokens,
            messages=conversation_history,
            system=SYSTEM_PROMPT,
        )
        assert result == mock_response


class TestParseResponse:
    """
    A test class for the parse_response function in the api_utils module.

    This class contains various test methods to ensure the correct behavior
    of the parse_response function under different scenarios, including:
    - Handling of empty or invalid responses
    - Parsing of valid responses from different AI providers (Anthropic and OpenAI)
    - Correct extraction of fields from the parsed JSON
    - Handling of responses with missing fields

    Each test method in this class focuses on a specific aspect of the
    parse_response function's behavior, helping to ensure its robustness
    and correctness across various input conditions.
    """

    def test_parse_response_empty(self):
        """
        Test that parse_response raises a ValueError when given an empty response.

        This test verifies that the parse_response function correctly handles
        the case of an empty (None) response for the Anthropic provider.

        It checks that:
        1. A ValueError is raised when parse_response is called with None.
        2. The error message matches the expected string.

        This helps ensure that the function fails gracefully and provides
        appropriate error information when given invalid input.
        """
        with pytest.raises(ValueError, match="Empty or invalid response received"):
            parse_response(None, "anthropic")

    def test_parse_response_no_content(self):
        """
        Test that parse_response raises a ValueError when given an Anthropic
        response with no content.
        """
        response = Mock(content=[])
        with pytest.raises(ValueError, match="Empty or invalid response received"):
            parse_response(response, "anthropic")

    def test_parse_response_no_choices(self):
        """
        Test that parse_response raises a ValueError when given an OpenAI
        response with no choices.
        """
        response = Mock(choices=[])
        with pytest.raises(ValueError, match="Empty or invalid response received"):
            parse_response(response, "openai")

    def test_parse_response_valid(self):
        """
        Test that parse_response correctly handles a valid Anthropic response.

        This test verifies that the parse_response function correctly parses
        a valid JSON response from the Anthropic API. It checks that:
        1. The function correctly extracts all fields from the JSON.
        2. The extracted values match the expected values.
        3. The function handles various data types (strings, lists) correctly.

        This test helps ensure that the parse_response function can accurately
        process and return the structured data from a well-formed API response.
        """
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
        ) = parse_response(response, "anthropic")

        assert text == "Sample text"
        assert questions == ["What does this code do?"]
        assert code == "print('Hello, World!')"
        assert code_version == "1.0"
        assert version_description == "Initial version"
        assert requirements == ["pytest"]

    def test_parse_response_missing_fields(self):
        """
        Test that parse_response correctly handles a response with missing fields.

        This test verifies that the parse_response function:
        1. Correctly extracts the fields that are present in the response.
        2. Sets default values (None or empty list) for missing fields.
        3. Doesn't raise an exception when optional fields are missing.

        It helps ensure that the function is robust and can handle incomplete
        responses without breaking.
        """
        content = {"text": "Sample text", "code": "print('Hello, World!')"}
        response = Response(content=[TextBlock(text=json.dumps(content))])
        (
            text,
            questions,
            code,
            code_version,
            version_description,
            requirements,
        ) = parse_response(response, "anthropic")

        assert text == "Sample text"
        assert questions == []
        assert code == "print('Hello, World!')"
        assert code_version is None
        assert version_description is None
        assert requirements == []

    def test_parse_response_complex_code(self):
        """
        Test parse_response function with a complex code example.

        This test verifies that the parse_response function correctly handles
        a response containing a more complex code structure. It checks that:
        1. The function correctly extracts all fields from the response.
        2. The extracted code maintains its structure and indentation.
        3. Version information and descriptions are correctly parsed.
        4. Empty lists for requirements and questions are handled properly.

        This test ensures that the parse_response function can handle
        responses with multi-line code snippets and various metadata fields.
        """
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
        ) = parse_response(response, "anthropic")

        assert text == "Complex code example"
        assert code == 'def hello():\n    print("Hello, World!")'
        assert code_version == "1.1"
        assert version_description == "Added function"
        assert questions == []
        assert requirements == []

    def test_parse_response_escaped_quotes(self):
        """
        Test parse_response function with escaped quotes in the content.

        This test verifies that the parse_response function correctly handles
        a response containing escaped quotes in various fields. It checks that:
        1. The function correctly extracts all fields from the response.
        2. The extracted text and code maintain their escaped quotes.
        3. Version information is correctly parsed.
        4. Empty lists for requirements and questions are handled properly.

        This test ensures that the parse_response function can handle
        responses with complex string content, including escaped quotes.
        """
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
        ) = parse_response(response, "anthropic")

        assert text == 'Text with "quotes"'
        assert code == 'print("Hello, \\"World!\\"")\nprint(\'Single quotes\')'
        assert code_version == "1.2"
        assert version_description == "Added escaped quotes"

    def test_parse_response_malformed_json(self):
        """
        Test parse_response function with malformed JSON input.

        This test verifies that the parse_response function correctly handles
        a response containing invalid JSON. It checks that:
        1. The function raises a ValueError when given non-JSON content.
        2. The error message specifically mentions that the parsed response
           is not a valid JSON object.

        This test ensures that the parse_response function fails gracefully
        and provides meaningful error messages when given invalid input.
        """
        response = Response(content=[TextBlock(text="This is not JSON")])
        with pytest.raises(
            ValueError, match="Parsed response is not a valid JSON object"
        ):
            parse_response(response, "anthropic")


class TestAPIConnection:
    """
    Test suite for the API connection functionality.

    This class contains tests to verify the behavior of the check_api_connection function
    under various scenarios, including successful connections, connection failures,
    and missing API keys.
    """

    @patch("codeaide.utils.api_utils.get_api_client")
    def test_check_api_connection_success(self, mock_get_api_client):
        """
        Test successful API connection.

        This test verifies that the check_api_connection function returns a successful
        result when the API client is properly initialized and responds correctly.
        """
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Yes, we are communicating.")]
        mock_client.messages.create.return_value = mock_response
        mock_get_api_client.return_value = mock_client

        result = check_api_connection()

        assert result[0] is True
        assert result[1] == "Yes, we are communicating."

    @patch("codeaide.utils.api_utils.get_api_client")
    def test_check_api_connection_failure(self, mock_get_api_client):
        """
        Test API connection failure.

        This test ensures that the check_api_connection function handles connection
        failures gracefully and returns an appropriate error message.
        """
        mock_client = Mock()
        mock_client.messages.create.side_effect = Exception("Connection failed")
        mock_get_api_client.return_value = mock_client

        result = check_api_connection()

        assert result[0] is False
        assert "Connection failed" in result[1]

    @patch("codeaide.utils.api_utils.get_api_client")
    def test_check_api_connection_missing_key(self, mock_get_api_client):
        """
        Test API connection with missing API key.

        This test verifies that the check_api_connection function correctly handles
        the scenario where the API key is missing or invalid.
        """
        mock_get_api_client.return_value = None

        result = check_api_connection()

        assert result[0] is False
        assert result[1] == "API key is missing or invalid"
