import json
import re
import anthropic
from anthropic import APIError
from decouple import config
from codeaide.utils.constants import MAX_TOKENS, AI_MODEL, SYSTEM_PROMPT

def get_anthropic_client():
    try:
        api_key = config('ANTHROPIC_API_KEY', default=None)
        if api_key is None:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        return anthropic.Anthropic(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Anthropic API client: {str(e)}")
        return None

client = get_anthropic_client()

def send_api_request(conversation_history, max_tokens=MAX_TOKENS):
    system_prompt = SYSTEM_PROMPT
    try:
        print(f"\n\n{'='*50}\n")
        print(f"Sending API request. The max tokens is {max_tokens}. Here's the conversation history:")
        for message in conversation_history:
            print(f"{message['role']}: {message['content']}")
        print("\n")
        
        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=max_tokens,
            messages=conversation_history,
            system=system_prompt
        )
        
        content = response.content[0].text if response.content else ""
        
        if not content:
            print("Warning: Received empty response from API")
            return None, True
        
        return response
    
    except Exception as e:
        print(f"Error in API request: {str(e)}")
        return None, True

def parse_response(response):
    if not response or not response.content:
        return None, None, None, None, None, None

    try:
        content = json.loads(response.content[0].text)
        
        text = content.get('text')
        code = content.get('code')
        code_version = content.get('code_version')
        version_description = content.get('version_description')
        requirements = content.get('requirements', [])
        questions = content.get('questions', [])

        return text, questions, code, code_version, version_description, requirements
    except json.JSONDecodeError:
        print("Error: Received malformed JSON from the API")
        return None, None, None, None, None, None

def check_api_connection():
    try:
        response = client.messages.create(
            model=AI_MODEL,
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Hi Claude, are we communicating?"}
            ]
        )
        return True, response.content[0].text.strip()
    except Exception as e:
        return False, str(e)
    
if __name__ == "__main__":
    success, message = check_api_connection()
    print(f"Connection {'successful' if success else 'failed'}: {message}")