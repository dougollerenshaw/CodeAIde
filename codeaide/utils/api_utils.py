import anthropic
import openai
import google.generativeai as genai
import hjson
import re
from google.generativeai.types import GenerationConfig
from google.api_core import exceptions as google_exceptions
from codeaide.utils.config_manager import ConfigManager

from codeaide.utils.constants import (
    AI_PROVIDERS,
    DEFAULT_PROVIDER,
    SYSTEM_PROMPT,
)
from codeaide.utils.logging_config import get_logger

logger = get_logger()
config_manager = ConfigManager()


class MissingAPIKeyException(Exception):
    def __init__(self, service):
        self.service = service
        super().__init__(
            f"{service.upper()}_API_KEY not found in environment variables"
        )


def get_api_client(provider=DEFAULT_PROVIDER, model=None):
    try:
        api_key = config_manager.get_api_key(provider)
        logger.info(f"Attempting to get API key for {provider}")
        logger.info(f"API key found: {'Yes' if api_key else 'No'}")

        if api_key is None or api_key.strip() == "":
            logger.warning(f"API key for {provider} is missing or empty")
            return None

        if provider.lower() == "anthropic":
            return anthropic.Anthropic(api_key=api_key)
        elif provider.lower() == "openai":
            return openai.OpenAI(api_key=api_key)
        elif provider.lower() == "google":
            genai.configure(api_key=api_key)
            client = genai.GenerativeModel(model, system_instruction=SYSTEM_PROMPT)
            return client
        else:
            raise ValueError(f"In get_api_client, unsupported provider: {provider}")
    except Exception as e:
        logger.error(f"Error initializing {provider.capitalize()} API client: {str(e)}")
        return None


def save_api_key(service, api_key):
    try:
        cleaned_key = api_key.strip().strip("'\"")  # Remove quotes and whitespace
        config_manager.set_api_key(service, cleaned_key)
        return True
    except Exception as e:
        logger.error(f"Error saving API key: {str(e)}")
        return False


def send_api_request(api_client, conversation_history, max_tokens, model, provider):
    logger.info(f"Sending API request with model: {model} and max_tokens: {max_tokens}")
    logger.debug(f"Conversation history: {conversation_history}")

    try:
        if provider.lower() == "anthropic":
            response = api_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=conversation_history,
                system=SYSTEM_PROMPT,
            )
            if not response.content:
                return None
        elif provider.lower() == "openai":
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + conversation_history
            response = api_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
            if not response.choices:
                return None
        elif provider.lower() == "google":
            try:
                prompt = ""
                for message in conversation_history:
                    role = message["role"]
                    content = message["content"]
                    prompt += f"{role.capitalize()}: {content}\n\n"

                # Create a GenerationConfig object
                generation_config = GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,  # You can adjust this as needed
                    top_p=0.95,  # You can adjust this as needed
                    top_k=40,  # You can adjust this as needed
                )

                response = api_client.generate_content(
                    contents=prompt, generation_config=generation_config
                )
            except google_exceptions.ResourceExhausted:
                logger.error("Google API quota exceeded")
                raise QuotaExceededException(
                    "Your quota has been exceeded. You might need to wait briefly before trying again or try using a different model."
                )
        else:
            raise NotImplementedError(f"API request for {provider} not implemented")

        logger.info(f"Received response from {provider}")
        logger.debug(f"Response object: {response}")
        return response
    except Exception as e:
        logger.error(f"Error in API request to {provider}: {str(e)}")
        if isinstance(e, QuotaExceededException):
            raise
        return None


def parse_response(response, provider):
    if not response:
        raise ValueError("Empty or invalid response received")

    logger.info(f"Received response: {response}")

    if provider.lower() == "anthropic":
        if not response.content:
            raise ValueError("Empty or invalid response received")
        json_str = response.content[0].text
    elif provider.lower() == "openai":
        if not response.choices:
            raise ValueError("Empty or invalid response received")
        json_str = response.choices[0].message.content
    elif provider.lower() == "google":
        json_str = response.candidates[0].content.parts[0].text
    else:
        raise ValueError(f"In parse_response, unsupported provider: {provider}")

    # Remove the triple backticks and language identifier if present
    if json_str.startswith("```json"):
        json_str = json_str[7:-3].strip()
    elif json_str.startswith("```"):
        json_str = json_str[3:-3].strip()

    try:
        # Parse the outer structure using hjson
        outer_json = hjson.loads(json_str)
    except hjson.HjsonDecodeError as e:
        raise ValueError(
            f"Failed to parse response: {str(e)}\nProblematic string: {json_str}"
        )

    if not isinstance(outer_json, dict):
        raise ValueError("Parsed response is not a valid JSON object")

    text = outer_json.get("text")
    code = outer_json.get("code")
    code_version = outer_json.get("code_version")
    version_description = outer_json.get("version_description")
    requirements = outer_json.get("requirements", [])
    questions = outer_json.get("questions", [])

    # Clean the code if it exists
    if code:
        code = clean_code(code)

    return text, questions, code, code_version, version_description, requirements


def clean_code(code):
    """
    Clean the code by removing triple backticks and language identifiers.

    Args:
        code (str): The code string to clean.

    Returns:
        str: The cleaned code string.
    """
    # Remove triple backticks and language identifier at the start
    code = re.sub(r"^```[\w-]*\n", "", code, flags=re.MULTILINE)

    # Remove triple backticks at the end
    code = re.sub(r"\n```$", "", code, flags=re.MULTILINE)

    # Trim any leading or trailing whitespace
    code = code.strip()

    return code


def check_api_connection():
    client = get_api_client()
    if client is None:
        return False, "API key is missing or invalid"
    try:
        provider = DEFAULT_PROVIDER
        model = list(AI_PROVIDERS[provider]["models"].keys())[0]
        response = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": "Are we communicating?"}],
        )
        return True, response.content[0].text.strip()
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    success, message = check_api_connection()
    logger.info(f"Connection {'successful' if success else 'failed'}: {message}")


# Add this new exception class at the end of the file
class QuotaExceededException(Exception):
    pass
