import os
import yaml
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
from codeaide.utils.logging_config import get_logger
import sys

logger = get_logger()

# Store the path of the general_utils.py file
UTILS_DIR = os.path.dirname(os.path.abspath(__file__))


def get_project_root():
    """Get the project root directory."""
    return os.path.abspath(os.path.join(UTILS_DIR, "..", ".."))


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = get_project_root()
    return os.path.join(base_path, relative_path)


def get_examples_file_path():
    """Get the path to the examples.yaml file."""
    return get_resource_path("codeaide/examples.yaml")


def load_examples():
    """Load and return all examples from the YAML file."""
    examples_file = get_examples_file_path()
    logger.info(f"Attempting to load examples from: {examples_file}")
    if not os.path.exists(examples_file):
        logger.error(f"Examples file not found: {examples_file}")
        return []

    try:
        with open(examples_file, "r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
        examples = data.get("examples", [])
        logger.info(f"Loaded {len(examples)} examples")
        return examples
    except yaml.YAMLError as e:
        logger.error(f"YAML Error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return []


def set_font(font_tuple):
    if len(font_tuple) == 2:
        font_family, font_size = font_tuple
        font_style = "normal"
    elif len(font_tuple) == 3:
        font_family, font_size, font_style = font_tuple
    else:
        logger.error("Invalid font tuple length")
        raise ValueError("Font tuple must be of length 2 or 3")

    qfont = QFont(font_family, font_size)

    if font_style == "italic":
        qfont.setStyle(QFont.StyleItalic)
    elif font_style == "bold":
        qfont.setWeight(QFont.Bold)
    # "normal" is the default, so we don't need to do anything for it

    return qfont


def get_dimmer_color(color, factor=0.6):
    """
    Generate a dimmer version of the given color.
    Works for both light and dark backgrounds.
    """
    color = QColor(color)
    if color.lightnessF() > 0.5:
        # For light colors, make it darker
        return color.darker(int(100 / factor))
    else:
        # For dark colors, make it lighter
        return color.lighter(int(100 * factor))


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


def increment_version(version, increment=1, major_or_minor="minor"):
    major, minor = map(int, version.split("."))
    if major_or_minor == "major":
        return f"{major + increment}.{minor}"
    else:
        return f"{major}.{minor + increment}"


def generate_session_id():
    """
    Generate a unique session ID based on the current timestamp.
    Format: YYYYMMDD_HHMMSS
    """
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Generated new session ID: {session_id}")
    return session_id
