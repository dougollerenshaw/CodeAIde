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

    def preprocess_json(content):
        # Use a regex to find the "code" field and preserve its formatting
        code_match = re.search(r'"code"\s*:\s*"((?:\\.|[^"\\])*)"', content)
        if code_match:
            code = code_match.group(1)
            # Replace the code field with a placeholder
            content = content.replace(code_match.group(0), '"code": "CODE_PLACEHOLDER"')
        
        # Preprocess the rest of the content
        content = re.sub(r'\n(?=(?:[^"]*"[^"]*")*[^"]*$)', ' ', content)
        content = re.sub(r'(?<!\\)(\n)(?=(?:[^"]*"[^"]*")*[^"]*$)', r'\\n', content)
        content = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', content)
        
        # Replace the placeholder with the original code
        if code_match:
            content = content.replace('"CODE_PLACEHOLDER"', json.dumps(code)[1:-1])
        
        return content

    # Preprocess the content
    preprocessed_content = preprocess_json(content)

    try:
        parsed = json.loads(preprocessed_content)
    except json.JSONDecodeError:
        # If preprocessing didn't help, try to parse the original content
        # This will raise a JSONDecodeError if it fails
        parsed = json.loads(content)

    # Unescape the code field without changing its formatting
    if 'code' in parsed and parsed['code'] is not None and parsed['code'] != "null":
        parsed['code'] = parsed['code'].encode().decode('unicode_escape')

    return (
        parsed.get('text', ''),
        parsed.get('questions', []),
        parsed.get('code'),
        parsed.get('code_version'),
        parsed.get('version_description'),
        parsed.get('requirements', [])
    )
    
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