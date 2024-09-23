import os
import json
import re
import anthropic
from anthropic import APIError
from decouple import config, AutoConfig

from codeaide.utils.constants import (
    AI_PROVIDERS,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    SYSTEM_PROMPT,
)


class MissingAPIKeyException(Exception):
    def __init__(self, service):
        self.service = service
        super().__init__(
            f"{service.upper()}_API_KEY not found in environment variables"
        )


def get_api_client(provider=DEFAULT_PROVIDER, model=DEFAULT_MODEL):
    try:
        # Force a reload of the configuration
        auto_config = AutoConfig(
            search_path=os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        )
        api_key_name = AI_PROVIDERS[provider]["api_key_name"]
        api_key = auto_config(api_key_name, default=None)
        if api_key is None or api_key.strip() == "":
            return None  # Return None if API key is missing or empty

        if provider.lower() == "anthropic":
            return anthropic.Anthropic(api_key=api_key)
        elif provider.lower() == "openai":
            # You'll need to import the OpenAI client and implement this part
            # For now, we'll just raise an error
            raise NotImplementedError("OpenAI client not yet implemented")
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        print(f"Error initializing {provider.capitalize()} API client: {str(e)}")
        return None


def save_api_key(service, api_key):
    try:
        cleaned_key = api_key.strip().strip("'\"")  # Remove quotes and whitespace
        root_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        env_path = os.path.join(root_dir, ".env")

        if os.path.exists(env_path):
            with open(env_path, "r") as file:
                lines = file.readlines()

            key_exists = False
            for i, line in enumerate(lines):
                if line.startswith(f"{service.upper()}_API_KEY="):
                    lines[i] = f'{service.upper()}_API_KEY="{cleaned_key}"\n'
                    key_exists = True
                    break

            if not key_exists:
                lines.append(f'{service.upper()}_API_KEY="{cleaned_key}"\n')
        else:
            lines = [f'{service.upper()}_API_KEY="{cleaned_key}"\n']

        with open(env_path, "w") as file:
            file.writelines(lines)

        return True
    except Exception as e:
        print(f"Error saving API key: {str(e)}")
        return False


def send_api_request(api_client, conversation_history, max_tokens):
    system_prompt = SYSTEM_PROMPT

    print(f"Sending API request with max_tokens: {max_tokens}")
    print(f"Conversation history: {conversation_history}\n")

    try:
        response = api_client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=max_tokens,
            messages=conversation_history,
            system=system_prompt,
        )
        if not response.content:
            return None
        return response
    except Exception as e:
        print(f"Error in API request: {str(e)}")
        return None


def parse_response(response):
    if not response or not response.content:
        raise ValueError("Empty or invalid response received")

    print(f"Received response: {response}\n")

    # Extract the JSON string
    json_str = response.content[0].text

    # Escape newlines within the "code" field
    json_str = re.sub(
        r'("code"\s*:\s*")(.+?)(")',
        lambda m: m.group(1) + m.group(2).replace("\n", "\\n") + m.group(3),
        json_str,
        flags=re.DOTALL,
    )

    try:
        # Parse the outer structure
        outer_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON: {str(e)}\nProblematic JSON string: {json_str}"
        )

    text = outer_json.get("text")
    code = outer_json.get("code")
    code_version = outer_json.get("code_version")
    version_description = outer_json.get("version_description")
    requirements = outer_json.get("requirements", [])
    questions = outer_json.get("questions", [])

    return text, questions, code, code_version, version_description, requirements


def check_api_connection():
    client = get_api_client()
    if client is None:
        return False, "API key is missing or invalid"
    try:
        response = client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": "Hi Claude, are we communicating?"}],
        )
        return True, response.content[0].text.strip()
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    success, message = check_api_connection()
    print(f"Connection {'successful' if success else 'failed'}: {message}")
