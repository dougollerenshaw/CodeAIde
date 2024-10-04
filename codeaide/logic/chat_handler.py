import json
import os
import sys
import re
import traceback
import logging
from codeaide.utils.api_utils import (
    parse_response,
    send_api_request,
    get_api_client,
    save_api_key,
    MissingAPIKeyException,
)
from codeaide.utils.constants import (
    MAX_RETRIES,
    AI_PROVIDERS,
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    INITIAL_MESSAGE,
)
from codeaide.utils.cost_tracker import CostTracker
from codeaide.utils.environment_manager import EnvironmentManager
from codeaide.utils.file_handler import FileHandler
from codeaide.utils.terminal_manager import TerminalManager
from codeaide.utils.general_utils import generate_session_id
from codeaide.utils.logging_config import get_logger, setup_logger
from PyQt5.QtWidgets import QMessageBox, QTextEdit
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QObject, QMetaObject, Qt, Q_ARG, pyqtSlot, pyqtSignal
from codeaide.ui.traceback_dialog import TracebackDialog


class ChatHandler(QObject):
    # Define custom signals for updating the chat and showing code
    update_chat_signal = pyqtSignal(
        str, str
    )  # Signal to update chat with (role, message)
    show_code_signal = pyqtSignal(str, str)  # Signal to show code with (code, version)
    traceback_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        """
        Initialize the ChatHandler class.

        Args:
            None

        Returns:
            None
        """
        self.session_id = generate_session_id()
        self.cost_tracker = CostTracker()
        self.file_handler = FileHandler(session_id=self.session_id)
        self.session_dir = (
            self.file_handler.session_dir
        )  # Store the specific session directory
        self.logger = get_logger()
        self.conversation_history = self.file_handler.load_chat_history()
        self.terminal_manager = TerminalManager(
            traceback_callback=self.emit_traceback_signal
        )
        self.latest_version = "0.0"
        self.api_client = None
        self.api_key_set = False
        self.current_provider = DEFAULT_PROVIDER
        self.current_model = DEFAULT_MODEL
        self.max_tokens = AI_PROVIDERS[self.current_provider]["models"][
            self.current_model
        ]["max_tokens"]

        self.api_key_valid, self.api_key_message = self.check_api_key()
        self.logger.info(f"New session started with ID: {self.session_id}")
        self.logger.info(f"Session directory: {self.session_dir}")
        self.chat_window = None

    def start_application(self):
        from codeaide.ui.chat_window import (
            ChatWindow,
        )  # Import here to avoid circular imports

        self.chat_window = ChatWindow(self)
        self.connect_signals()
        self.chat_window.show()

    def connect_signals(self):
        self.update_chat_signal.connect(self.chat_window.add_to_chat)
        self.show_code_signal.connect(self.chat_window.show_code)
        self.traceback_occurred.connect(self.chat_window.show_traceback_dialog)

    def check_api_key(self):
        """
        Check if the API key is set and valid.

        Returns:
            tuple: A tuple containing a boolean indicating if the API key is valid and a message.
        """
        self.api_client = get_api_client(self.current_provider, self.current_model)
        self.api_key_set = self.api_client is not None

        if not self.api_key_set:
            self.logger.warning("API key not set")
            return False, self.get_api_key_instructions(self.current_provider)
        self.logger.info("API key is valid")
        return True, None

    def get_api_key_instructions(self, provider):
        """
        Get instructions for setting up the API key for a given provider.

        Args:
            provider (str): The name of the provider.

        Returns:
            str: Instructions for setting up the API key.
        """
        if provider == "anthropic":
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
        elif provider == "openai":
            return (
                "It looks like you haven't set up your OpenAI API key yet. "
                "Here's how to get started:\n\n"
                "1. Go to https://platform.openai.com/api-keys and sign in to your OpenAI account or create an account if you don't have one.\n"
                "2. Generate a new API key.\n"
                "3. Add some funds to your account to cover the cost of using the API (start with as little as $1).\n"
                "4. Copy the API key and paste it here.\n\n"
                "Once you've pasted your API key, I'll save it securely in a .env file in the root of your project. "
                "This file is already in .gitignore, so it won't be shared if you push your code to a repository.\n\n"
                "Please paste your OpenAI API key now:"
            )
        else:
            return f"Please enter your API key for {provider.capitalize()}:"

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
        Handle the API key input from the user.

        Args:
            api_key (str): The API key entered by the user.

        Returns:
            tuple: A tuple containing a boolean indicating success, a message, and a boolean indicating if waiting for API key.
        """
        if save_api_key(self.current_provider, api_key):
            self.api_client = get_api_client(self.current_provider, self.current_model)
            self.api_key_set = self.api_client is not None
            if self.api_key_set:
                return (
                    True,
                    "Great! Your API key has been saved. What would you like to work on?",
                    False,
                )
            else:
                return (
                    False,
                    "Failed to initialize API client with the provided key.",
                    True,
                )
        else:
            return False, "Failed to save the API key.", True

    def process_input(self, user_input):
        """
        Process user input and generate a response.

        Args:
            user_input (str): The input provided by the user.

        Returns:
            dict: A response dictionary containing the type and content of the response.
        """
        self.logger.info(f"Processing input: {user_input}")
        try:
            if not self.api_key_set:
                return {
                    "type": "api_key_required",
                    "message": self.get_api_key_instructions(self.current_provider),
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
                    self.logger.error(f"ValueError: {str(e)}\n")
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
        self.file_handler.save_chat_history(self.conversation_history)

    def get_ai_response(self):
        """
        Send a request to the AI API and get a response.

        Args:
            None

        Returns:
            dict: The response from the AI API, or None if the request failed.
        """
        return send_api_request(
            self.api_client,
            self.conversation_history,
            self.max_tokens,
            self.current_model,
            self.current_provider,
        )

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
        try:
            parsed_response = parse_response(response, provider=self.current_provider)
        except (ValueError, json.JSONDecodeError) as e:
            error_message = (
                f"Failed to parse AI response: {str(e)}\nRaw response: {response}"
            )
            raise ValueError(error_message)

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
        if self.current_provider.lower() == "anthropic":
            self.conversation_history.append(
                {"role": "assistant", "content": response.content[0].text}
            )
        elif self.current_provider.lower() == "openai":
            self.conversation_history.append(
                {"role": "assistant", "content": response.choices[0].message.content}
            )
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        self.file_handler.save_chat_history(self.conversation_history)

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
        error_prompt = f"\n\nThere was an error in your last response: {error_message}. Please ensure you're using proper JSON formatting to avoid this error and others like it. Please don't apologize for the error because it will be hidden from the end user."
        self.conversation_history[-1]["content"] += error_prompt
        self.file_handler.save_chat_history(self.conversation_history)

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
        script_path = os.path.join(
            project_root, self.file_handler.session_dir, filename
        )
        req_path = os.path.join(
            project_root, self.file_handler.session_dir, requirements
        )

        self.terminal_manager.run_script(script_path, req_path)

    def is_task_in_progress(self):
        """
        Check if there's an ongoing task in the conversation.

        Args:
            None

        Returns:
            bool: True if there's an ongoing task, False otherwise.
        """
        return bool(self.conversation_history)

    def set_model(self, provider, model):
        self.logger.info(f"In set_model: provider: {provider}, model: {model}")
        if provider not in AI_PROVIDERS:
            self.logger.error(f"Invalid provider: {provider}")
            return False, None
        if model not in AI_PROVIDERS[provider]["models"]:
            self.logger.error(f"Invalid model {model} for provider {provider}")
            return False, None

        self.current_provider = provider
        self.current_model = model
        self.max_tokens = AI_PROVIDERS[self.current_provider]["models"][
            self.current_model
        ]["max_tokens"]

        # Check API key when setting a new model
        api_key_valid, message = self.check_api_key()
        if not api_key_valid:
            return False, message

        self.logger.info(f"Model {model} for provider {provider} set successfully.")
        return True, None

    def clear_conversation_history(self):
        """
        Clear the conversation history.

        Args:
            None

        Returns:
            None
        """
        self.conversation_history = []
        self.file_handler.save_chat_history(self.conversation_history)

    def get_latest_version(self):
        return self.latest_version

    def set_latest_version(self, version):
        self.latest_version = version

    def start_new_session(self, chat_window):
        self.logger.info("Starting new session")

        # Log the previous session path correctly
        self.logger.info(f"Previous session path: {self.session_dir}")

        # Generate new session ID
        new_session_id = generate_session_id()

        # Create new FileHandler with new session ID
        new_file_handler = FileHandler(session_id=new_session_id)

        # Copy existing log to new session and set up new logger
        self.file_handler.copy_log_to_new_session(new_session_id)
        setup_logger(new_file_handler.session_dir)

        # Update instance variables
        self.session_id = new_session_id
        self.file_handler = new_file_handler
        self.session_dir = new_file_handler.session_dir  # Update the session directory

        # Clear conversation history
        self.conversation_history = []

        # Clear chat display in UI
        chat_window.clear_chat_display()

        # Close code pop-up if it exists
        chat_window.close_code_popup()

        # Add system message about previous session
        system_message = f"A new session has been started. The previous chat will not be visible to the agent. Previous session data saved in: {self.session_dir}"
        chat_window.add_to_chat("System", system_message)
        chat_window.add_to_chat("AI", INITIAL_MESSAGE)

        self.logger.info(f"New session started with ID: {self.session_id}")
        self.logger.info(f"New session directory: {self.session_dir}")

    # New method to load a previous session
    def load_previous_session(self, session_id, chat_window):
        self.logger.info(f"Loading previous session: {session_id}")
        self.session_id = session_id
        self.file_handler = FileHandler(session_id=session_id)
        self.session_dir = self.file_handler.session_dir

        # Load chat contents
        chat_window.load_chat_contents()

        self.logger.info(f"Loaded previous session with ID: {self.session_id}")

    def emit_traceback_signal(self, traceback_text):
        self.logger.info(
            f"ChatHandler: Emitting traceback signal with text: {traceback_text[:50]}..."
        )
        self.traceback_occurred.emit(traceback_text)

    def send_traceback_to_agent(self, traceback_text):
        self.logger.info(
            f"ChatHandler: Sending traceback to agent: {traceback_text[:50]}..."
        )
        message = (
            "The following error occurred when running the code you just provided:\n\n"
            f"```\n{traceback_text}\n```\n\n"
            "Please provide a solution that avoids this error."
        )
        self.logger.info(f"ChatHandler: Setting input text in chat window")
        self.chat_window.input_text.setPlainText(message)
        self.logger.info(f"ChatHandler: Calling on_submit in chat window")
        self.chat_window.on_submit()
