import json
import os
import sys
import re
import traceback
from codeaide.utils.api_utils import (
    parse_response,
    send_api_request,
    get_api_client,
    save_api_key,
    MissingAPIKeyException,
)
from codeaide.utils.constants import MAX_RETRIES, MAX_TOKENS
from codeaide.utils.cost_tracker import CostTracker
from codeaide.utils.environment_manager import EnvironmentManager
from codeaide.utils.file_handler import FileHandler
from codeaide.utils.terminal_manager import TerminalManager


class ChatHandler:
    def __init__(self):
        """
        Initialize the ChatHandler class.

        Args:
            None

        Returns:
            None
        """
        self.cost_tracker = CostTracker()
        self.conversation_history = []
        self.file_handler = FileHandler()
        self.file_handler.clear_output_dir()
        self.env_manager = EnvironmentManager()
        self.terminal_manager = TerminalManager()
        self.latest_version = "0.0"
        self.api_client = None
        self.api_key_set = False
        self.current_service = "anthropic"  # Default service

    def check_api_key(self):
        """
        Check if the API key is set and valid.

        Args:
            None

        Returns:
            tuple: A tuple containing a boolean indicating if the API key is valid and a message.
        """
        if self.api_client is None:
            self.api_client = get_api_client(self.current_service)

        if self.api_client:
            self.api_key_set = True
            return True, None
        else:
            self.api_key_set = False
            return False, self.get_api_key_instructions(self.current_service)

    def get_api_key_instructions(self, service):
        """
        Get instructions for setting up the API key for a given service.

        Args:
            service (str): The name of the service.

        Returns:
            str: Instructions for setting up the API key.
        """
        if service == "anthropic":
            return (
                "It looks like you haven't set up your Anthropic API key yet. "
                "Here's how to get started:\n\n"
                "1. Go to https://www.anthropic.com or https://console.anthropic.com to sign up or log in.\n"
                "2. Navigate to your account settings or API section.\n"
                "3. Generate a new API key.\n"
                "4. Add some funds to your account to cover the cost of using the API (start with as little as $1).\n"
                "5. Copy the API key and paste it here.\n\n"
                "Once you've pasted your API key, I'll save it securely in a .env file in the root of your project. "
                "This file is already in .gitignore, so it won't be shared if you push your code to a repository.\n\n"
                "Please paste your Anthropic API key now:"
            )
        else:
            return f"Please enter your API key for {service.capitalize()}:"

    def validate_api_key(self, api_key):
        """
        Validate the format of the API key.

        Args:
            api_key (str): The API key to validate.

        Returns:
            tuple: A tuple containing a boolean indicating if the API key is valid and an error message.
        """
        # Remove leading/trailing whitespace and quotes
        cleaned_key = api_key.strip().strip("'\"")

        # Check if the API key follows a general pattern for API keys
        pattern = r"^[a-zA-Z0-9_-]{32,}$"
        if len(cleaned_key) < 32:
            return False, "API key is too short (should be at least 32 characters)"
        elif not re.match(pattern, cleaned_key):
            return (
                False,
                "API key should only contain letters, numbers, underscores, and hyphens",
            )
        return True, ""

    def handle_api_key_input(self, api_key):
        """
        Handle the input of the API key.

        Args:
            api_key (str): The API key entered by the user.

        Returns:
            tuple: A tuple containing a boolean indicating if the API key was saved successfully and a message.
        """
        cleaned_key = api_key.strip().strip("'\"")  # Remove quotes and whitespace
        is_valid, error_message = self.validate_api_key(cleaned_key)
        if is_valid:
            if save_api_key(self.current_service, cleaned_key):
                # Try to get a new API client with the new key
                self.api_client = get_api_client(self.current_service)
                if self.api_client:
                    self.api_key_set = True
                    return True, "API key saved and verified successfully."
                else:
                    return (
                        False,
                        "API key saved, but verification failed. Please check your key and try again.",
                    )
            else:
                return (
                    False,
                    "Failed to save the API key. Please check your permissions and try again.",
                )
        else:
            return False, f"Invalid API key format: {error_message}. Please try again."

    def process_input(self, user_input):
        """
        Process user input and generate a response.

        Args:
            user_input (str): The input provided by the user.

        Returns:
            dict: A response dictionary containing the type and content of the response.
        """
        try:
            if not self.check_and_set_api_key():
                return {
                    "type": "api_key_required",
                    "message": self.get_api_key_instructions(self.current_service),
                }

            self.add_user_input_to_history(user_input)

            for attempt in range(MAX_RETRIES):
                response = self.get_ai_response()
                if response is None:
                    if self.is_last_attempt(attempt):
                        return self.create_error_response(
                            "Failed to get a response from the AI. Please try again."
                        )
                    continue

                self.cost_tracker.log_request(response)

                try:
                    return self.process_ai_response(response)
                except ValueError as e:
                    if not self.is_last_attempt(attempt):
                        self.add_error_prompt_to_history(str(e))
                    else:
                        return self.create_error_response(
                            f"There was an error processing the AI's response after {MAX_RETRIES} attempts. Please try again."
                        )

            return self.create_error_response(
                f"Failed to get a valid response from the AI after {MAX_RETRIES} attempts. Please try again."
            )

        except Exception as e:
            return self.handle_unexpected_error(e)

    def check_and_set_api_key(self):
        """
        Check if the API key is set and valid.

        Args:
            None

        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        api_key_valid, _ = self.check_api_key()
        return api_key_valid

    def add_user_input_to_history(self, user_input):
        """
        Add user input to the conversation history with version information.

        Args:
            user_input (str): The input provided by the user.

        Returns:
            None
        """
        version_info = f"\n\nThe latest code version was {self.latest_version}. If you're making minor changes to the previous code, increment the minor version (e.g., 1.0 to 1.1). If you're creating entirely new code, increment the major version (e.g., 1.1 to 2.0). Ensure the new version is higher than {self.latest_version}."
        self.conversation_history.append(
            {"role": "user", "content": user_input + version_info}
        )

    def get_ai_response(self):
        """
        Send a request to the AI API and get a response.

        Args:
            None

        Returns:
            dict: The response from the AI API, or None if the request failed.
        """
        return send_api_request(self.api_client, self.conversation_history, MAX_TOKENS)

    def is_last_attempt(self, attempt):
        """
        Check if the current attempt is the last one.

        Args:
            attempt (int): The current attempt number.

        Returns:
            bool: True if it's the last attempt, False otherwise.
        """
        return attempt == MAX_RETRIES - 1

    def process_ai_response(self, response):
        """
        Process the AI's response and create an appropriate response object.

        Args:
            response (dict): The response from the AI API.

        Returns:
            dict: A response dictionary containing the type and content of the response.

        Raises:
            ValueError: If the response cannot be parsed or the version is invalid.
        """
        parsed_response = parse_response(response)
        if parsed_response[0] is None:
            raise ValueError("Failed to parse JSON response")

        (
            text,
            questions,
            code,
            code_version,
            version_description,
            requirements,
        ) = parsed_response

        if code and self.compare_versions(code_version, self.latest_version) <= 0:
            raise ValueError(
                f"New version {code_version} is not higher than the latest version {self.latest_version}"
            )

        self.update_conversation_history(response)

        if questions:
            return self.create_questions_response(text, questions)
        elif code:
            return self.create_code_response(
                text, code, code_version, version_description, requirements
            )
        else:
            return self.create_message_response(text)

    def update_conversation_history(self, response):
        """
        Add the AI's response to the conversation history.

        Args:
            response (dict): The response from the AI API.

        Returns:
            None
        """
        self.conversation_history.append(
            {"role": "assistant", "content": response.content[0].text}
        )

    def create_questions_response(self, text, questions):
        """
        Create a response object for questions.

        Args:
            text (str): The text content of the response.
            questions (list): A list of follow-up questions.

        Returns:
            dict: A response dictionary with type 'questions'.
        """
        return {"type": "questions", "message": text, "questions": questions}

    def create_code_response(
        self, text, code, code_version, version_description, requirements
    ):
        """
        Create a response object for code generation.

        Args:
            text (str): The text content of the response.
            code (str): The generated code.
            code_version (str): The version of the generated code.
            version_description (str): A description of the code version.
            requirements (str): Any additional requirements for the code.

        Returns:
            dict: A response dictionary with type 'code'.
        """
        self.latest_version = code_version
        self.file_handler.save_code(
            code, code_version, version_description, requirements
        )
        return {
            "type": "code",
            "message": f"{text}\n\nOpening in the code window as v{code_version}...",
            "code": code,
            "requirements": requirements,
        }

    def create_message_response(self, text):
        """
        Create a response object for a simple message.

        Args:
            text (str): The text content of the message.

        Returns:
            dict: A response dictionary with type 'message'.
        """
        return {"type": "message", "message": text}

    def create_error_response(self, message):
        """
        Create a response object for an error message.

        Args:
            message (str): The error message.

        Returns:
            dict: A response dictionary with type 'error'.
        """
        return {"type": "error", "message": message}

    def add_error_prompt_to_history(self, error_message):
        """
        Add an error prompt to the conversation history.

        Args:
            error_message (str): The error message to be added.

        Returns:
            None
        """
        error_prompt = f"\n\nThere was an error in your response: {error_message}. Please ensure you're using proper JSON formatting and incrementing the version number correctly. The latest version was {self.latest_version}, so the new version must be higher than this."
        self.conversation_history[-1]["content"] += error_prompt

    def handle_unexpected_error(self, e):
        """
        Handle unexpected errors and create an appropriate response.

        Args:
            e (Exception): The exception that was raised.

        Returns:
            dict: A response dictionary with type 'internal_error'.
        """
        traceback.print_exc()
        return {
            "type": "internal_error",
            "message": f"An unexpected error occurred: {str(e)}. Please check the console window for the full traceback.",
        }

    @staticmethod
    def compare_versions(v1, v2):
        """
        Compare two version strings.

        Args:
            v1 (str): The first version string.
            v2 (str): The second version string.

        Returns:
            int: 1 if v1 > v2, -1 if v1 < v2, 0 if v1 == v2.
        """
        v1_parts = list(map(int, v1.split(".")))
        v2_parts = list(map(int, v2.split(".")))
        return (v1_parts > v2_parts) - (v1_parts < v2_parts)

    def run_generated_code(self, filename, requirements):
        """
        Run the generated code in a new environment.

        Args:
            filename (str): The name of the file containing the generated code.
            requirements (str): The name of the file containing the requirements.

        Returns:
            None
        """
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(project_root, self.file_handler.output_dir, filename)
        req_path = os.path.join(
            project_root, self.file_handler.output_dir, requirements
        )

        activation_command = self.env_manager.get_activation_command()
        new_packages = self.env_manager.install_requirements(req_path)

        script_content = f"""
        clear # Clear the terminal
        echo "Activating environment..."
        {activation_command}
        """

        if new_packages:
            script_content += 'echo "New dependencies installed:"\n'
            for package in new_packages:
                script_content += f'echo "  - {package}"\n'

        script_content += f"""
        echo "Running {filename}..."
        python "{script_path}"
        
        echo "Script execution completed."
        """

        self.terminal_manager.run_in_terminal(script_content)

    def is_task_in_progress(self):
        """
        Check if there's an ongoing task in the conversation.

        Args:
            None

        Returns:
            bool: True if there's an ongoing task, False otherwise.
        """
        return bool(self.conversation_history)
