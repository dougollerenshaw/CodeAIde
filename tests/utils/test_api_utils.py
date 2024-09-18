import json
from codeaide.utils.api_utils import parse_response
from collections import namedtuple

# Mock Response object
Response = namedtuple('Response', ['content'])
TextBlock = namedtuple('TextBlock', ['text'])

def test_parse_response_empty():
    result = parse_response(None)
    assert result == (None, None, None, None, None, None)

def test_parse_response_no_content():
    response = Response(content=[])
    result = parse_response(response)
    assert result == (None, None, None, None, None, None)

def test_parse_response_valid():
    content = {
        "text": "Sample text",
        "code": "print('Hello, World!')",
        "code_version": "1.0",
        "version_description": "Initial version",
        "requirements": ["pytest"],
        "questions": ["What does this code do?"]
    }
    response = Response(content=[TextBlock(text=json.dumps(content))])
    text, questions, code, code_version, version_description, requirements = parse_response(response)
    
    assert text == "Sample text"
    assert questions == ["What does this code do?"]
    assert code == "print('Hello, World!')"
    assert code_version == "1.0"
    assert version_description == "Initial version"
    assert requirements == ["pytest"]

def test_parse_response_missing_fields():
    content = {
        "text": "Sample text",
        "code": "print('Hello, World!')"
    }
    response = Response(content=[TextBlock(text=json.dumps(content))])
    text, questions, code, code_version, version_description, requirements = parse_response(response)
    
    assert text == "Sample text"
    assert questions == []
    assert code == "print('Hello, World!')"
    assert code_version is None
    assert version_description is None
    assert requirements == []

def test_parse_response_complex_code():
    content = {
        "text": "Complex code example",
        "code": 'def hello():\n    print("Hello, World!")',
        "code_version": "1.1",
        "version_description": "Added function",
        "requirements": [],
        "questions": []
    }
    response = Response(content=[TextBlock(text=json.dumps(content))])
    text, questions, code, code_version, version_description, requirements = parse_response(response)
    
    assert text == "Complex code example"
    assert code == 'def hello():\n    print("Hello, World!")'
    assert code_version == "1.1"
    assert version_description == "Added function"

def test_parse_response_escaped_quotes():
    content = {
        "text": 'Text with "quotes"',
        "code": 'print("Hello, \\"World!\\"")\nprint(\'Single quotes\')',
        "code_version": "1.2",
        "version_description": "Added escaped quotes",
        "requirements": [],
        "questions": []
    }
    response = Response(content=[TextBlock(text=json.dumps(content))])
    text, questions, code, code_version, version_description, requirements = parse_response(response)
    
    assert text == 'Text with "quotes"'
    assert code == 'print("Hello, \\"World!\\"")\nprint(\'Single quotes\')'
    assert code_version == "1.2"
    assert version_description == "Added escaped quotes"

def test_parse_response_malformed_json():
    response = Response(content=[TextBlock(text="This is not JSON")])
    result = parse_response(response)
    assert result == (None, None, None, None, None, None)