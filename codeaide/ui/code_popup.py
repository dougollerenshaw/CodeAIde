import os
from PyQt5.QtCore import QRect, Qt, QRegExp, QSize
from PyQt5.QtGui import (
    QFont,
    QTextCharFormat,
    QColor,
    QSyntaxHighlighter,
    QPainter,
    QPen,
)
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QDialog,
)

from codeaide.utils import general_utils
from codeaide.utils.constants import (
    CODE_FONT,
    CODE_WINDOW_BG,
    CODE_WINDOW_FG,
    CODE_WINDOW_HEIGHT,
    CODE_WINDOW_WIDTH,
)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.update_line_number_area_width(0)

        # Set editor background color
        self.setStyleSheet(
            f"background-color: {CODE_WINDOW_BG}; color: {CODE_WINDOW_FG};"
        )

        # Add extra space at the bottom for the horizontal scrollbar
        self.setViewportMargins(0, 0, 0, self.horizontalScrollBar().height())

    def line_number_area_width(self):
        digits = len(str(max(1, self.blockCount())))
        space = 3 + self.fontMetrics().horizontalAdvance("9") * (digits + 1)
        return min(space, 50)  # Cap the width at 50 pixels

    def update_line_number_area_width(self, _):
        self.setViewportMargins(
            self.line_number_area_width(), 0, 0, self.horizontalScrollBar().height()
        )

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

        # Update the bottom margin when the widget is resized
        self.setViewportMargins(
            self.line_number_area_width(), 0, 0, self.horizontalScrollBar().height()
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)

        # Set the background color to match the editor
        painter.fillRect(event.rect(), QColor(CODE_WINDOW_BG))

        # Get a dimmer version of the text color for line numbers and box
        dimmer_color = general_utils.get_dimmer_color(CODE_WINDOW_FG)

        # Draw a subtle box around the line number area
        painter.setPen(QPen(dimmer_color, 1))
        painter.drawRect(event.rect().adjusted(0, 0, -1, -1))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(dimmer_color)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Define color scheme for dark background
        self.colors = {
            "keyword": QColor("#ff79c6"),  # Pink
            "operator": QColor("#ff79c6"),  # Pink
            "brace": QColor("#f8f8f2"),  # White
            "defclass": QColor("#50fa7b"),  # Green
            "string": QColor("#f1fa8c"),  # Yellow
            "string2": QColor("#f1fa8c"),  # Yellow
            "comment": QColor("#6272a4"),  # Blue-grey
            "self": QColor("#bd93f9"),  # Purple
            "numbers": QColor("#bd93f9"),  # Purple
            "boolean": QColor("#ff5555"),  # Red
            "identifier": QColor("#f8f8f2"),  # White
        }

        # Keyword, operator, and brace rules
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(self.colors["keyword"])
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "and",
            "assert",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "exec",
            "finally",
            "for",
            "from",
            "global",
            "if",
            "import",
            "in",
            "is",
            "lambda",
            "not",
            "or",
            "pass",
            "print",
            "raise",
            "return",
            "try",
            "while",
            "yield",
            "None",
            "True",
            "False",
        ]

        for word in keywords:
            pattern = QRegExp("\\b" + word + "\\b")
            self.highlighting_rules.append((pattern, keyword_format))

        # Class name
        class_format = QTextCharFormat()
        class_format.setFontWeight(QFont.Bold)
        class_format.setForeground(self.colors["defclass"])
        self.highlighting_rules.append((QRegExp("\\bclass\\b\\s*(\\w+)"), class_format))

        # Function name
        function_format = QTextCharFormat()
        function_format.setFontItalic(True)
        function_format.setForeground(self.colors["defclass"])
        self.highlighting_rules.append(
            (QRegExp("\\bdef\\b\\s*(\\w+)"), function_format)
        )

        # String
        string_format = QTextCharFormat()
        string_format.setForeground(self.colors["string"])
        self.highlighting_rules.append((QRegExp('".*"'), string_format))
        self.highlighting_rules.append((QRegExp("'.*'"), string_format))

        # Comment
        comment_format = QTextCharFormat()
        comment_format.setForeground(self.colors["comment"])
        self.highlighting_rules.append((QRegExp("#[^\n]*"), comment_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(self.colors["numbers"])
        self.highlighting_rules.append((QRegExp("\\b[0-9]+\\b"), number_format))

        # Self
        self_format = QTextCharFormat()
        self_format.setForeground(self.colors["self"])
        self_format.setFontItalic(True)
        self.highlighting_rules.append((QRegExp("\\bself\\b"), self_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)


class CodePopup(QDialog):
    def __init__(
        self,
        parent,
        file_handler,
        terminal_manager,
        code,
        requirements,
        run_callback,
        chat_handler,
    ):
        super().__init__(parent)
        self.setWindowTitle("💻 Generated Code 💻")
        self.resize(CODE_WINDOW_WIDTH, CODE_WINDOW_HEIGHT)
        self.file_handler = file_handler
        self.terminal_manager = terminal_manager
        self.run_callback = run_callback
        self.setup_ui()
        self.load_versions()
        self.show_code(code, requirements)
        self.position_window()
        self.loading_versions = False
        self.show()

        # Use the chat_handler passed as an argument, or try to get it from the parent
        self.chat_handler = chat_handler or (parent.chat_handler if parent else None)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(8, 8, 8, 8)

        self.text_area = CodeEditor(self)
        self.text_area.setReadOnly(True)
        self.text_area.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.text_area.setStyleSheet(
            f"""
            background-color: {CODE_WINDOW_BG};
            color: {CODE_WINDOW_FG};
            border: 1px solid #ccc;
            padding: 5px;
        """
        )
        self.text_area.setFont(general_utils.set_font(CODE_FONT))
        self.highlighter = PythonHighlighter(self.text_area.document())
        layout.addWidget(self.text_area)

        controls_layout = QVBoxLayout()

        version_label = QLabel("Choose a version to display/run:")
        controls_layout.addWidget(version_label)

        self.version_dropdown = QComboBox(self)
        self.version_dropdown.currentIndexChanged.connect(self.on_version_change)
        controls_layout.addWidget(self.version_dropdown)

        button_layout = QHBoxLayout()
        buttons = [
            ("Run Code", self.on_run),
            ("Copy Code", self.on_copy_code),
            ("Save Code", self.on_save_code),
            ("Copy Requirements", self.on_copy_requirements),
            ("Close", self.close),
        ]

        for text, callback in buttons:
            button = QPushButton(text)
            button.clicked.connect(callback)
            button_layout.addWidget(button)

        controls_layout.addLayout(button_layout)
        layout.addLayout(controls_layout)

    def bring_to_front(self):
        self.raise_()
        self.activateWindow()

    def update_with_new_version(self, code, requirements):
        self.load_versions()
        self.show_code(code, requirements)

    def load_versions(self):
        self.loading_versions = (
            True  # Set flag before loading to prevent on_version_change from running
        )
        self.versions_dict = self.file_handler.get_versions_dict()
        version_values = [
            f"v{version}: {data['version_description']}"
            for version, data in self.versions_dict.items()
        ]
        self.version_dropdown.clear()
        self.version_dropdown.addItems(version_values)
        if version_values:
            self.version_dropdown.setCurrentIndex(len(version_values) - 1)
        self.loading_versions = (
            False  # Reset flag after loading to allow on_version_change to run
        )

    def show_code(self, code, requirements):
        self.text_area.setPlainText(code)
        self.current_requirements = requirements
        self.bring_to_front()

    def on_version_change(self):
        if self.loading_versions:
            return  # Exit early if we're still loading versions

        selected = self.version_dropdown.currentText()
        version = selected.split(":")[0].strip("v")
        version_data = self.versions_dict[version]
        code_path = version_data["code_path"]
        with open(code_path, "r") as file:
            code = file.read()
        requirements = version_data["requirements"]
        self.show_code(code, requirements)

    def on_run(self):
        selected = self.version_dropdown.currentText()
        version = selected.split(":")[0].strip("v")
        version_data = self.versions_dict[version]
        code_path = version_data["code_path"]
        requirements = version_data["requirements"]

        req_file_name = f"requirements_{version}.txt"
        req_path = os.path.join(os.path.dirname(code_path), req_file_name)
        with open(req_path, "w") as f:
            f.write("\n".join(requirements))

        self.terminal_manager.run_script(code_path, req_path)

    def on_copy_code(self):
        QApplication.clipboard().setText(self.text_area.toPlainText())

    def on_save_code(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Code", "", "Python Files (*.py)"
        )
        if file_path:
            with open(file_path, "w") as file:
                file.write(self.text_area.toPlainText())

    def on_copy_requirements(self):
        QApplication.clipboard().setText("\n".join(self.current_requirements))

    def position_window(self):
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - self.width(), 0)
