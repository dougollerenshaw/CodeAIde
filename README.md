# CodeAIde

CodeAIde is an AI-powered coding assistant that automates the process of writing and running code with natural language interactions. This tool wraps around an LLM API client so that you can interact with the LLM in a chat window to request code or changes to previously generated code. Users can then execute the code directly from the application without the need to manage environments, install dependencies, etc. Errors in the code execution are caught automatically and users have the option to share the error with the LLM to request a fix.

This is designed to be a simple, intuitive tool for writing, running, and refining simple Python scripts. It is not meant to be a full IDE or code editing environment and isn't a replacement for a tool like Cursor or the Github Copilot extension in VSCode. Instead, it is intended to be a simple tool for quickly writing code and getting it working without the need to worry about setting up environments, installing dependencies, etc. This is ideal for simple tasks and for beginners who want to try out an idea without the need to set up a complex development environment.

Currently, CodeAIde supports OpenAI and Anthropic APIs. Users can select the model provider and the specific model in the chat window. The chat agent will prompt the user to enter the associated API key if it is not already set in the `.env` file.

## Features

- Natural language code generation
- Support for OpenAI and Anthropic APIs
- Version control for generated code
- Local code execution and testing
- Automatic error handling and sharing with LLM for fixes

## Examples

Here are some example videos demonstrating use. Example prompts can be accessed by clicking "Use Example" and selecting from available examples.

First, a simple matplotlib plot with followup requests to modify aesthetics.

https://github.com/user-attachments/assets/8aa729ff-c431-4a61-a9ef-d17050a27d02

## Installation

### Prerequisites

- Python 3.9 or higher

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/dougollerenshaw/CodeAIde.git
   cd CodeAIde
   ```

2. Create a Conda environment:
   ```
   conda create -n codeaide python=3.8
   conda activate codeaide
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Anthropic API key:
   - Set up a developer account with Anthropic and get an API key at https://console.anthropic.com/dashboard
   - You'll need to pre-fund your account to cover API costs. Current costs (as of Sept 15, 2024) are $0.003 and $0.015 per 1000 tokens for input and output, respectively. Long conversations will obviously cost more. Fund your account with something small (maybe $5) to start with, then add more if you find this tool useful.
   - Create a `.env` file in the project root
   - Add your API key to the file:
     ```
     ANTHROPIC_API_KEY="your_api_key_here"  # make sure the key is in quotes
     ```

## Usage

To start CodeAIde for actual code generation, run:

```
python codeaide.py
```
This will bring up a chat window where you can start your conversation.

Follow the prompts to interact with the AI assistant. You can:
- Enter coding tasks or questions
- Read the generated code in a popup before running
- Execute code locally
- Request changes or improvements from the LLM (the previous code will remain in the model's context window)
- Copy the code to your clipboard or save it as a standalone file
- Select and re-run any previous version of the code form the current conversation.


To test the API connection, run:

```
python codeaide.py test
```
This will send a simple "Hi Claude, are we communicating?" prompt to the API. If your API key is set up properly and you have an internet connection, you'll see a response at the command line that looks something like this:
```
Connection successful!
Claude says: Yes, we are communicating! I'm Claude, an AI assistant. How can I help you today?
```

## Future feature roadmap

The following features do not currently exist, but adding them in the future would make this project more useful:

* Support for more code languages. Currently only Python is supported. Additional language support would require backend support for automatically compiling/running generated code in that language.
* Chat history support. Currently, when a session ends, the chat history is lost. Ideally it would be possible to keep the chat history and associated code and make it searchable across sessions.
* API usage tracking. The API messages contain information with the number of prompt and response tokens. We can track these during a session to estimate the total cost of all API requests.

## Contributing

Contributions to CodeAIde are welcome! Please feel free to submit a Pull Request.

## Building a standalone application

For detailed instructions on how to build CodeAide as a standalone application, please refer to the [BUILD.md](BUILD.md) file in the root of this repository.

## License

This project is licensed under the MIT License - see the license file for details.

## Disclaimer

CodeAIde is an experimental tool and should be used with caution. Always review and test generated code before using it in production environments. And since code is executed locally, be careful what you ask for! For example, if you ask for a program that will wipe the entire contents of your hard drive, you might well get exactly what you asked for.

## Contact

For any questions or feedback, please [open an issue](https://github.com/dougollerenshaw/CodeAIde/issues) on the GitHub repository or email me directly at [d.ollerenshaw@gmail.com](mailto:d.ollerenshaw@gmail.com).


**Note:** This project is currently in development. Features and usage may change as the project evolves.
