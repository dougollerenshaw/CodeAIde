import os
import random
from PyQt5.QtGui import QFont

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
    
    formatted_message = message.replace('\n', '<br>')
    
    html_message = f'''
    <span style="color:{color}; font-family:'{font_family}'; font-size:{font_size}pt; font-style:{font_style};">
    <b>{sender}:</b> {formatted_message}
    </span>
    '''
    
    return html_message