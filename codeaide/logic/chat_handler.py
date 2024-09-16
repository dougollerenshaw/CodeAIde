from codeaide.utils.api_utils import send_api_request, parse_response
from codeaide.utils.environment_manager import EnvironmentManager
from codeaide.utils.terminal_manager import TerminalManager
from codeaide.utils.file_handler import FileHandler
from codeaide.utils.cost_tracker import CostTracker
from codeaide.utils.constants import MAX_TOKENS, MAX_RETRIES
import os
import json

class ChatHandler:
    def __init__(self):
        self.cost_tracker = CostTracker()
        self.conversation_history = []
        self.file_handler = FileHandler()
        self.file_handler.clear_output_dir()
        self.env_manager = EnvironmentManager()
        self.terminal_manager = TerminalManager()
        self.latest_version = "0.0"

    def process_input(self, user_input):
        try:
            self.conversation_history.append({"role": "user", "content": user_input})
            
            for attempt in range(MAX_RETRIES):
                version_info = f"\n\nThe latest code version was {self.latest_version}. If you're making minor changes to the previous code, increment the minor version (e.g., 1.0 to 1.1). If you're creating entirely new code, increment the major version (e.g., 1.1 to 2.0). Ensure the new version is higher than {self.latest_version}."
                self.conversation_history[-1]["content"] += version_info

                response, is_truncated = send_api_request(self.conversation_history, MAX_TOKENS)
                print(f"Response (Attempt {attempt + 1}): {response}")
                
                if response is None:
                    if attempt == MAX_RETRIES - 1:
                        return {'type': 'error', 'message': "Failed to get a response from the AI. Please try again."}
                    continue
                
                self.cost_tracker.log_request(response)
                
                try:
                    text, questions, code, code_version, version_description, requirements = parse_response(response)
                    
                    if code and self.compare_versions(code_version, self.latest_version) <= 0:
                        raise ValueError(f"New version {code_version} is not higher than the latest version {self.latest_version}")
                    
                    if code:
                        self.latest_version = code_version
                    self.conversation_history.append({"role": "assistant", "content": response.content[0].text})
                    
                    if questions:
                        return {'type': 'questions', 'message': text, 'questions': questions}
                    elif code:
                        self.file_handler.save_code(code, code_version, version_description, requirements)
                        return {'type': 'code', 'message': f"{text} (Version {code_version})", 'code': code, 'requirements': requirements}
                    else:
                        return {'type': 'message', 'message': text}
                
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error processing response (Attempt {attempt + 1}): {e}")
                    if attempt < MAX_RETRIES - 1:
                        error_prompt = f"\n\nThere was an error in your response: {e}. Please ensure you're using proper JSON formatting and incrementing the version number correctly. The latest version was {self.latest_version}, so the new version must be higher than this."
                        self.conversation_history[-1]["content"] += error_prompt
                    else:
                        return {'type': 'error', 'message': f"There was an error processing the AI's response after {MAX_RETRIES} attempts. Please try again."}
            
            return {'type': 'error', 'message': f"Failed to get a valid response from the AI after {MAX_RETRIES} attempts. Please try again."}
        
        except Exception as e:
            print("Unexpected error in process_input")
            return {'type': 'error', 'message': f"An unexpected error occurred: {str(e)}"}

    @staticmethod
    def compare_versions(v1, v2):
        v1_parts = list(map(int, v1.split('.')))
        v2_parts = list(map(int, v2.split('.')))
        return (v1_parts > v2_parts) - (v1_parts < v2_parts)

    def run_generated_code(self, filename, requirements):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(project_root, self.file_handler.output_dir, filename)
        req_path = os.path.join(project_root, self.file_handler.output_dir, requirements)

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
        return bool(self.conversation_history)