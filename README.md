# CodeAIde

CodeAIde is an AI-powered coding assistant that helps developers write, test, and optimize code through natural language interactions. By leveraging the power of large language models, CodeAIde aims to streamline the coding process and boost productivity.

## Features

- Natural language code generation
- Interactive clarification process for precise code output
- Local code execution and testing
- Cost tracking for API usage (not yet implemented)

## Installation

### Prerequisites

- Python 3.8 or higher
- Conda (for environment management)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/CodeAIde.git
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
   - Create a `.env` file in the project root
   - Add your API key to the file:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```

## Usage

To test the API connection, run:

```
python codeaide.py test
```

To start CodeAIde, run:

```
python codeaide.py
```

Follow the prompts to interact with the AI assistant. You can:
- Enter coding tasks or questions
- Review and approve generated code
- Execute code locally
- Check API usage and costs (not yet implemented)

## Contributing

Contributions to CodeAIde are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

CodeAIde is an experimental tool and should be used with caution. Always review and test generated code before using it in production environments. And since code is executed locally, be careful what you ask for! For example, if you ask for a program that will wipe the entire contents of your harddrive, you might well get exactly what you asked for.

## Acknowledgments

- This project uses the Anthropic API to interact with the Claude AI model.

## Contact

For any questions or feedback, please open an issue on the GitHub repository.

---

**Note:** This project is currently in development. Features and usage may change as the project evolves.