import os

import yaml
from PyQt5.QtGui import QFont

# Store the path of the general_utils.py file
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_project_root():
    """Get the project root directory."""
    # Always use UTILS_DIR as the starting point
    return os.path.abspath(os.path.join(UTILS_DIR, "..", ".."))


def get_examples_file_path():
    """Get the path to the examples.yaml file."""
    return os.path.join(get_project_root(), "codeaide", "examples.yaml")


def load_examples():
    """Load and return all examples from the YAML file."""
    examples_file = get_examples_file_path()
    if not os.path.exists(examples_file):
        print(f"Examples file not found: {examples_file}")
        return []

    try:
        with open(examples_file, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        return data.get("examples", [])
    except yaml.YAMLError as e:
        print(f"YAML Error: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return []


def set_font(font_tuple):
    if len(font_tuple) == 2:
        font_family, font_size = font_tuple
        font_style = "normal"
    elif len(font_tuple) == 3:
        font_family, font_size, font_style = font_tuple
    else:
        raise ValueError("Font tuple must be of length 2 or 3")

    qfont = QFont(font_family, font_size)

    if font_style == "italic":
        qfont.setStyle(QFont.StyleItalic)
    elif font_style == "bold":
        qfont.setWeight(QFont.Bold)
    # "normal" is the default, so we don't need to do anything for it

    return qfont


def format_chat_message(sender, message, font, color):
    qfont = set_font(font)
    font_family = qfont.family()
    font_size = qfont.pointSize()
    font_style = "italic" if qfont.style() == QFont.StyleItalic else "normal"

    formatted_message = message.replace("\n", "<br>")

    html_message = f"""
    <span style="color:{color}; font-family:'{font_family}'; font-size:{font_size}pt; font-style:{font_style};">
    <b>{sender}:</b> {formatted_message}
    </span>
    """

    return html_message
