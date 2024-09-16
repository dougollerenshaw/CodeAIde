from codeaide.utils.api_utils import send_api_request, parse_response
from codeaide.logic.code_runner import run_code
from codeaide.utils.constants import MAX_TOKENS, MAX_RETRIES
from codeaide.utils.file_handler import FileHandler  # Add this import

class ChatHandler:
    def __init__(self, cost_tracker):
        self.cost_tracker = cost_tracker
        self.conversation_history = []
        self.file_handler = FileHandler()
        self.file_handler.clear_output_dir()

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
        run_code(filename, requirements)

    def is_task_in_progress(self):
        return bool(self.conversation_history)