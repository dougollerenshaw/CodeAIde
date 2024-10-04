import os
import shutil
import json
from codeaide.utils.logging_config import setup_logger, get_logger


class FileHandler:
    def __init__(self, base_dir=None, session_id=None):
        if base_dir is None:
            self.base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        else:
            self.base_dir = base_dir
        self.output_dir = os.path.join(self.base_dir, "session_data")
        self.session_id = session_id
        self.session_dir = (
            os.path.join(self.output_dir, self.session_id) if self.session_id else None
        )
        self.versions_dict = {}
        self.chat_history_file = (
            os.path.join(self.session_dir, "chat_history.json")
            if self.session_dir
            else None
        )
        self.chat_window_log_file = (
            os.path.join(self.session_dir, "chat_window_log.json")
            if self.session_dir
            else None
        )
        self._ensure_output_dirs_exist()

        if self.session_dir:
            setup_logger(self.session_dir)
        self.logger = get_logger()

    def _ensure_output_dirs_exist(self):
        os.makedirs(self.output_dir, exist_ok=True)
        if self.session_dir:
            os.makedirs(self.session_dir, exist_ok=True)

    def save_code(self, code, version, version_description, requirements=[]):
        if not self.session_dir:
            raise ValueError("Session directory not set. Cannot save code.")

        code_path = os.path.join(self.session_dir, f"generated_script_{version}.py")
        requirements_path = os.path.join(
            self.session_dir, f"requirements_{version}.txt"
        )
        abs_code_path = os.path.abspath(code_path)
        abs_req_path = os.path.abspath(requirements_path)
        self.logger.info(f"Attempting to save code to: {abs_code_path}")
        try:
            with open(abs_code_path, "w") as file:
                file.write(code)
            self.logger.info(f"Code saved successfully to: {abs_code_path}")
            self.logger.info(f"Saving associated requirements to: {abs_req_path}")
            self.save_requirements(requirements, version)
        except Exception as e:
            self.logger.error(f"Error saving file: {str(e)}")
        self.logger.info(f"Adding version {version} to versions_dict")
        self.versions_dict[version] = {
            "version_description": version_description,
            "requirements": requirements,
            "code_path": abs_code_path,
            "requirements_path": abs_req_path,
        }
        self.logger.debug(f"Current versions dict: {self.versions_dict}")
        return code_path

    def save_requirements(self, requirements, version):
        if not self.session_dir:
            raise ValueError("Session directory not set. Cannot save requirements.")

        file_path = os.path.join(self.session_dir, f"requirements_{version}.txt")
        with open(file_path, "w") as file:
            for req in requirements:
                file.write(f"{req}\n")
        return file_path

    def get_versions_dict(self):
        return self.versions_dict

    def get_code(self, version):
        if not self.session_dir:
            raise ValueError("Session directory not set. Cannot retrieve code.")

        file_path = os.path.join(self.session_dir, f"generated_script_{version}.py")
        with open(file_path, "r") as file:
            return file.read()

    def get_requirements(self, version):
        if not self.session_dir:
            raise ValueError("Session directory not set. Cannot retrieve requirements.")

        file_path = os.path.join(self.session_dir, f"requirements_{version}.txt")
        with open(file_path, "r") as file:
            return file.read().splitlines()

    def save_chat_history(self, conversation_history):
        if not self.session_dir:
            raise ValueError("Session directory not set. Cannot save chat history.")

        try:
            with open(self.chat_history_file, "w", encoding="utf-8") as f:
                json.dump(conversation_history, f, ensure_ascii=False, indent=2)
            self.logger.info(
                f"Chat history saved successfully to: {self.chat_history_file}"
            )
        except Exception as e:
            self.logger.error(f"Error saving chat history: {str(e)}")

    def load_chat_history(self):
        if not self.session_dir or not os.path.exists(self.chat_history_file):
            return []

        try:
            with open(self.chat_history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading chat history: {str(e)}")
            return []

    def save_chat_contents(self, chat_contents):
        if not self.session_dir:
            self.logger.error("Session directory not set. Cannot save chat contents.")
            return

        try:
            with open(self.chat_window_log_file, "w", encoding="utf-8") as f:
                json.dump(chat_contents, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Chat contents saved to {self.chat_window_log_file}")
        except Exception as e:
            self.logger.error(f"Error saving chat contents: {str(e)}")

    def load_chat_contents(self):
        if not os.path.exists(self.chat_window_log_file):
            self.logger.info(f"No chat log file found at {self.chat_window_log_file}")
            return []

        try:
            with open(self.chat_window_log_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading chat contents: {str(e)}")
            return []

    def set_session_id(self, session_id):
        self.session_id = session_id
        self.session_dir = os.path.join(self.output_dir, self.session_id)
        self.chat_history_file = os.path.join(self.session_dir, "chat_history.json")
        self._ensure_output_dirs_exist()
        setup_logger(self.session_dir)
        self.logger = get_logger()

    def copy_log_to_new_session(self, new_session_id):
        new_session_dir = os.path.join(self.output_dir, new_session_id)
        os.makedirs(new_session_dir, exist_ok=True)

        old_log_file = os.path.join(self.session_dir, "codeaide.log")
        new_log_file = os.path.join(new_session_dir, "codeaide.log")

        os.makedirs(os.path.dirname(new_log_file), exist_ok=True)

        if os.path.exists(old_log_file):
            shutil.copy2(old_log_file, new_log_file)

            # Append a message to the old log file
            with open(old_log_file, "a") as f:
                f.write("\nNew session created. Log continued in new file.\n")

            self.logger.info(f"Copied log file to new session: {new_session_id}")
        else:
            self.logger.warning(
                f"No existing log file found to copy for new session: {new_session_id}"
            )
