from codeaide.utils.api_utils import send_api_request, parse_response
from codeaide.utils.environment_manager import EnvironmentManager
from codeaide.utils.terminal_manager import TerminalManager
from codeaide.utils.file_handler import FileHandler
from codeaide.utils.constants import MAX_TOKENS
import os

class ChatHandler:
    def __init__(self, cost_tracker):
        self.cost_tracker = cost_tracker
        self.conversation_history = []
        self.file_handler = FileHandler()
        self.file_handler.clear_output_dir()
        self.env_manager = EnvironmentManager()
        self.terminal_manager = TerminalManager()

    def process_input(self, user_input):
        self.conversation_history.append({"role": "user", "content": user_input})
        
        response, is_truncated = send_api_request(self.conversation_history, MAX_TOKENS)
        print("Response: ", response)
        print('\n')
        if response is None:
            return {'type': 'error', 'content': "Failed to get a response from the AI. Please try again."}
        
        self.cost_tracker.log_request(response)
        
        text, questions, code, requirements = parse_response(response)
        
        # Append the full response to the conversation history
        self.conversation_history.append({"role": "assistant", "content": response.content[0].text})
        
        if questions:
            print("The response contains questions.")
            return {'type': 'questions', 'message': text, 'questions': questions}
        if code:
            print("The response contains code.")
            # Save the code and requirements
            self.file_handler.save_code(code)
            self.file_handler.save_requirements(requirements)
            version = self.file_handler.get_current_version()
            return {'type': 'code', 'message': f"{text} (Version {version})", 'code': code, 'requirements': requirements}
        
        return {'type': 'message', 'message': text}

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