import json
import re
import anthropic
from anthropic import APIError
from decouple import config
from codeaide.utils.constants import MAX_TOKENS, AI_MODEL

ANTHROPIC_API_KEY = config('ANTHROPIC_API_KEY')

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def send_api_request(conversation_history, max_tokens=MAX_TOKENS):
    system_prompt = """
    You are an AI assistant specialized in providing coding advice and solutions. Your primary goal is to offer practical, working code examples while balancing the need for clarification with the ability to make reasonable assumptions. Follow these guidelines:
    * Prioritize providing functional code: When asked for code solutions, aim to deliver complete, runnable Python code whenever possible.
    * Always return complete, fully functional code. Never use ellipses (...) or comments like "other methods remain unchanged" to indicate omitted parts. Every method, function, and class must be fully implemented in each response.    
    * Ensure that all necessary imports are included: If the code requires specific libraries or modules, include the necessary import statements.
    * If the code uses matplotlib, please make the code object oriented (e.g. using `fig, ax = plt.subplots()`, `ax.set_title(...)`, etc.).
    * Make reasonable assumptions: If certain details are missing from the user's query, make logical assumptions based on common practices and standards.
    * Explain key assumptions: Briefly mention any significant assumptions you've made that might affect the code's functionality or use case.
    * Provide context and explanations: After presenting the code, offer a brief explanation of its key components, functionality, and any important considerations.
    * Try to provide useful and relevant text responses along with code snippets to enhance the user's understanding of the approach and the code itself.
    * Ask clarifying questions when necessary: If critical information is missing or if there are multiple possible interpretations of the request, ask for clarification. However, lean towards making assumptions if the missing information is not crucial.
    * Suggest improvements or alternatives: If relevant, mention potential optimizations, alternative approaches, or best practices that could enhance the solution.
    * Be adaptive: If the user provides feedback or additional requirements, be ready to modify the code accordingly.
    * Handle edge cases: Consider and address common edge cases or potential issues in your code solutions.
    * Maintain a problem-solving attitude: If the initial request is unclear or seems impossible, try to interpret the user's intent and provide the closest possible solution, explaining your reasoning.
    * Use appropriate formatting: Present code in properly formatted code blocks and use markdown for improved readability.
    * Make sure that the JSON object that you return is properly formatted so that it can be parsed correctly without errors. We want to avoid errors like "Error parsing JSON: Invalid control character at: line 4 column 446 (char 447)".
    * If a user asks you to generate code that performs some action, don't tell them you can't do it. Instead, provide the best code you can to accomplish the task they are requesting based on the information provided. They can run the code and see the results for themselves.
    * Try to maintain as much consistency as possible across responses. If a user asks you to make changes to a code snippet you've provided, try to make only the requested changes without altering the rest of the code.
    * When modifying existing code, include the entire updated codebase in your response, not just the changed parts. Ensure all previously implemented features and methods are preserved unless explicitly asked to remove them.
    * If providing a complete rewrite or entirely new implementation, increment the major version number (e.g., from 1.x to 2.0). For minor changes or additions, increment the minor version number (e.g., from 1.1 to 1.2).
    * Ensure all explanations are complete: If you mention that you will provide a list, explanation, or breakdown of changes, always include the full content in your response. Never leave explanations incomplete or implied.
    * Double-check your responses: Before finalizing your answer, review your 'text' field to ensure all promised explanations, lists, or breakdowns are fully included.
    * For longer explanations or lists, use appropriate formatting within the 'text' field. Use newline characters (\n) and proper indentation to structure your response clearly within the JSON format.

    Remember, the goal is to provide valuable, working code solutions while maintaining a balance between making reasonable assumptions and seeking clarification when truly necessary.
    Format your responses as a JSON object with six keys: 
    * 'text': a string that contains any natural language explanations or comments that you think are helpful for the user. This should never be null or incomplete. If you mention providing a list or explanation, ensure it is fully included here. If you have no text response, provide a brief explanation of the code or the assumptions made.
    * 'questions': an array of strings that pose necessary follow-up questions to the user
    * 'code': a string with the properly formatted, complete code block. This must include all necessary components for the code to run, including any previously implemented methods or classes. This should be null only if you have questions or text responses but no code to provide.    
    * 'code_version': a string that represents the version of the code. Start at 1.0 and increment for each new version of the code you provide. Use your judgement on whether to increment the minor or major component of the version. It is critical that version numbers never be reused during a chat and that the numbers always increment upward. This field should be null if you have no code to provide.
    * 'version_description': a very short string that describes the purpose of the code and/or changes made in this version of the code since the last version. This should be null if you have questions or text responses but no code to provide.
    * 'requirements': an array of strings listing any required Python packages or modules that are necessary to run the code. This should be null if no additional requirements are needed beyond the standard Python libraries.
    Do not include any text outside of the JSON object.
    """
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
        
        is_truncated = False 
        # NOTE: The truncation check is disabled for now. It's giving me all sorts of problems.
        # is_truncated = check_truncation(content)
        # if is_truncated:
        #     print("Warning: Response appears to be truncated")
        # else:
        #     try:
        #         # Try to parse the JSON, but don't use the result
        #         json.loads(content)
        #     except json.JSONDecodeError as e:
        #         print(f"Warning: Response is not truncated but failed to parse as JSON: {e}")
        
        return response, is_truncated
    
    except Exception as e:
        print(f"Error in API request: {str(e)}")
        return None, True

def check_truncation(content):
    """Check if the content is obviously truncated."""
    # Remove whitespace and newlines from the end
    content = content.strip()
    # Check if it ends with a closing brace
    if not content.endswith('}'):
        print("The response does not end with a closing brace '}'. This indicates a trucated response.")
        return True
    # Check if we have an equal number of opening and closing braces
    if content.count('{') != content.count('}'):
        print("The response has an unequal number of opening and closing braces. This indicates a trucated response.")
        return True
    return False

def parse_response(response):
    if not response or not response.content:
        return None, None, None, None
    
    content = response.content[0].text
    
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        # If that fails, apply our newline handling
        # Replace newlines in the entire content with \\n, except within the "code" field
        content = re.sub(r'(?<!\\)\\n', r'\\n', content)
        # Now replace literal \n (newline char) with \\n in the "code" field
        content = re.sub(r'("code": ")(.+?)(")', lambda m: m.group(1) + m.group(2).replace('\n', '\\n') + m.group(3), content, flags=re.DOTALL)
        parsed = json.loads(content)
    
    # Ensure newlines in the code field are properly unescaped for display
    if 'code' in parsed and parsed['code'] is not None and parsed['code'] != "null":
        parsed['code'] = parsed['code'].replace('\\n', '\n')
    
    return (
        parsed.get('text', ''),
        parsed.get('questions', []),
        parsed.get('code'),
        parsed.get('code_version'),
        parsed.get('version_description'),
        parsed.get('requirements', [])
    )
    
    
def handle_truncation(current_max_tokens):
    truncation_message = (
        f"My response exceeded the maximum number of tokens designated for responses ({current_max_tokens}). "
        "I'm going to try formulating a shorter response. If you want to increase the maximum number of tokens, "
        "you can do so in the settings, but you'll need to restart the program for it to take effect."
    )
    
    concise_request = f"The previous response was too long. Can you provide a more concise solution? Note that the maximum response length is currently set to {current_max_tokens} tokens."
    
    return truncation_message, concise_request
    
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