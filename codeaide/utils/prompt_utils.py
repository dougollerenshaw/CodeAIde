import os
import random

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'examples')

def get_example_prompts():
    """Return a list of available example prompt names."""
    return [f.replace('.txt', '') for f in os.listdir(EXAMPLES_DIR) if f.endswith('.txt')]

def load_example_prompt(name):
    """Load and return the content of a specific example prompt."""
    file_path = os.path.join(EXAMPLES_DIR, f"{name}.txt")
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r') as file:
        return file.read()

def get_random_example():
    """Return a random example prompt."""
    examples = get_example_prompts()
    if not examples:
        return None
    return load_example_prompt(random.choice(examples))