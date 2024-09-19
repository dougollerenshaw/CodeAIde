import os
import json
import re
import anthropic
from anthropic import APIError
from decouple import config, AutoConfig

from codeaide.utils.constants import AI_MODEL, MAX_TOKENS, SYSTEM_PROMPT


class MissingAPIKeyException(Exception):
    def __init__(self, service):
        self.service = service
        super().__init__(
            f"{service.upper()}_API_KEY not found in environment variables"
        )


def get_api_client(service="anthropic"):
    try:
        # Force a reload of the configuration
        auto_config = AutoConfig(
            search_path=os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        )
        api_key = auto_config(f"{service.upper()}_API_KEY", default=None)
        if api_key is None:
            raise MissingAPIKeyException(service)

        if service == "anthropic":
            return anthropic.Anthropic(api_key=api_key)
        # Add more elif blocks here for other API services
        else:
            raise ValueError(f"Unsupported service: {service}")
    except MissingAPIKeyException:
        # If the API key is missing, return None instead of raising the exception
        return None
    except Exception as e:
        print(f"Error initializing {service.capitalize()} API client: {str(e)}")
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


def send_api_request(client, conversation_history, max_tokens=MAX_TOKENS):
    system_prompt = SYSTEM_PROMPT
    try:
        print(f"\n\n{'='*50}\n")
        print(
            f"Sending API request. The max tokens is {max_tokens}. Here's the conversation history:"
        )
        for message in conversation_history:
            print(f"{message['role']}: {message['content']}")
        print("\n")

        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=max_tokens,
            messages=conversation_history,
            system=system_prompt,
        )

        content = response.content[0].text if response.content else ""

        if not content:
            print("Warning: Received empty response from API")
            return None

        return response

    except Exception as e:
        print(f"Error in API request: {str(e)}")
        return None


def parse_response(response):
    if not response or not response.content:
        return None, None, None, None, None, None

    try:
        content = json.loads(response.content[0].text)

        text = content.get("text")
        code = content.get("code")
        code_version = content.get("code_version")
        version_description = content.get("version_description")
        requirements = content.get("requirements", [])
        questions = content.get("questions", [])

        return text, questions, code, code_version, version_description, requirements
    except json.JSONDecodeError:
        print("Error: Received malformed JSON from the API")
        return None, None, None, None, None, None


def check_api_connection(service="anthropic"):
    client = get_api_client(service)
    try:
        if service == "anthropic":
            response = client.messages.create(
                model=AI_MODEL,
                max_tokens=100,
                messages=[{"role": "user", "content": "Hi, are we communicating?"}],
            )
            return True, response.content[0].text.strip()
        # Add more elif blocks here for other API services
        else:
            raise ValueError(f"Unsupported service: {service}")
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    success, message = check_api_connection()
    print(f"Connection {'successful' if success else 'failed'}: {message}")
