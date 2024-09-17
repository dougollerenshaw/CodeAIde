import json
import re
import anthropic
from anthropic import APIError
from decouple import config
from codeaide.utils.constants import MAX_TOKENS, AI_MODEL, SYSTEM_PROMPT

ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY')

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

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

    content = response.content[0].text

    def extract_json_field(field_name, content, is_code=False):
        pattern = rf'"{field_name}"\s*:\s*"((?:\\.|[^"\\])*)"'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            field_content = match.group(1)
            if is_code:
                # For code, replace escaped newlines with actual newlines, but only within strings
                field_content = re.sub(r'(?<!\\)\\n', '\n', field_content)
                field_content = re.sub(r'\\(?=["\'])', '', field_content)
            else:
                # For non-code fields, unescape all content
                field_content = field_content.encode().decode('unicode_escape')
            return field_content
        return None

    def extract_json_array(field_name, content):
        pattern = rf'"{field_name}"\s*:\s*(\[[^\]]*\])'
        match = re.search(pattern, content)
        if match:
            return json.loads(match.group(1))
        return []

    text = extract_json_field('text', content)
    code = extract_json_field('code', content, is_code=True)
    code_version = extract_json_field('code_version', content)
    version_description = extract_json_field('version_description', content)
    requirements = extract_json_array('requirements', content)

    questions_match = re.search(r'"questions"\s*:\s*(\[(?:\s*"(?:\\.|[^"\\])*"\s*,?\s*)*\])', content)
    questions = json.loads(questions_match.group(1)) if questions_match else []

    return text, questions, code, code_version, version_description, requirements

def test_api_connection():
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