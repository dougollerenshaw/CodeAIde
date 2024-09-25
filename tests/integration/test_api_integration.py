"""
This file contains integration tests for the API functionality of the CodeAide application.

These tests verify the correct operation of API clients, request sending, and response parsing
for both Anthropic and OpenAI APIs. They ensure that the application can successfully
communicate with these external services and handle their responses appropriately.

IMPORTANT: These tests use live API calls and will incur charges on your API accounts.
They are designed to complement the existing unit tests and are not part of the
continuous integration pipeline. These tests should be run manually and infrequently,
primarily to verify that the API functionality is working as expected with the live APIs.

To run these tests:
1. Ensure you have the necessary API keys set in your environment variables:
   - ANTHROPIC_API_KEY for Anthropic tests
   - OPENAI_API_KEY for OpenAI tests
2. Install pytest if not already installed: `pip install pytest`
3. Navigate to the project root directory
4. Run the tests using the command: `pytest -m integration`

Note: These tests are marked with the 'integration' marker and are specifically run
using the `-m integration` flag. This allows them to be easily separated from other
tests and run independently when needed.

Caution: Due to the use of live API calls, these tests should not be run frequently
or as part of automated CI/CD processes to avoid unnecessary API charges.
"""

import pytest
from codeaide.utils.api_utils import get_api_client, send_api_request, parse_response
from codeaide.utils.constants import SYSTEM_PROMPT

ANTHROPIC_MODEL = "claude-3-haiku-20240307"
OPENAI_MODEL = "gpt-3.5-turbo"

MINIMAL_PROMPT = """
Please respond with a JSON object containing the following fields:
- text: A brief description of the code.
- code: A piece of code that prints "Hello, World!".
- code_version: The version of the code.
- version_description: A brief description of the version.
- requirements: An empty list.
- questions: An empty list.
"""


@pytest.mark.integration
def test_anthropic_api():
    """
    Integration test for the Anthropic API.

    This test:
    1. Initializes the Anthropic API client
    2. Sends a request to the API with a minimal prompt
    3. Verifies that a non-empty response is received
    4. Checks that the response contains the word "Hello"
    5. Attempts to parse the response
    6. Verifies that all expected fields are present in the parsed response
    """
    api_client = get_api_client(provider="anthropic")
    assert api_client is not None, "Anthropic API client initialization failed"

    conversation_history = [{"role": "user", "content": MINIMAL_PROMPT}]
    response = send_api_request(
        api_client, conversation_history, 100, ANTHROPIC_MODEL, "anthropic"
    )
    assert response is not None, "Anthropic API request failed"
    assert "Hello" in response.content[0].text, "Unexpected response from Anthropic API"

    # Test parse_response function
    parsed_response = parse_response(response, "anthropic")
    assert parsed_response is not None, "Failed to parse response from Anthropic API"
    (
        text,
        questions,
        code,
        code_version,
        version_description,
        requirements,
    ) = parsed_response
    assert text is not None, "Parsed text is None"
    assert isinstance(questions, list), "Parsed questions is not a list"
    assert code is not None, "Parsed code is None"
    assert code_version is not None, "Parsed code_version is None"
    assert version_description is not None, "Parsed version_description is None"
    assert isinstance(requirements, list), "Parsed requirements is not a list"


@pytest.mark.integration
def test_openai_api():
    """
    Integration test for the OpenAI API.

    This test:
    1. Initializes the OpenAI API client
    2. Sends a request to the API with a minimal prompt
    3. Verifies that a non-empty response is received
    4. Checks that the response contains the word "Hello"
    5. Attempts to parse the response
    6. Verifies that all expected fields are present in the parsed response
    """
    api_client = get_api_client(provider="openai")
    assert api_client is not None, "OpenAI API client initialization failed"

    conversation_history = [{"role": "user", "content": MINIMAL_PROMPT}]
    response = send_api_request(
        api_client, conversation_history, 100, OPENAI_MODEL, "openai"
    )
    assert response is not None, "OpenAI API request failed"
    assert (
        "Hello" in response.choices[0].message.content
    ), "Unexpected response from OpenAI API"

    # Test parse_response function
    parsed_response = parse_response(response, "openai")
    assert parsed_response is not None, "Failed to parse response from OpenAI API"
    (
        text,
        questions,
        code,
        code_version,
        version_description,
        requirements,
    ) = parsed_response
    assert text is not None, "Parsed text is None"
    assert isinstance(questions, list), "Parsed questions is not a list"
    assert code is not None, "Parsed code is None"
    assert code_version is not None, "Parsed code_version is None"
    assert version_description is not None, "Parsed version_description is None"
    assert isinstance(requirements, list), "Parsed requirements is not a list"
