import signal
import sys
import traceback

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from codeaide.ui.code_popup import CodePopup
from codeaide.ui.example_selection_dialog import show_example_dialog
from codeaide.utils import general_utils
from codeaide.utils.constants import (
    AI_EMOJI,
    AI_FONT,
    AI_MESSAGE_COLOR,
    CHAT_WINDOW_BG,
    CHAT_WINDOW_FG,
    CHAT_WINDOW_HEIGHT,
    CHAT_WINDOW_WIDTH,
    INITIAL_MESSAGE,
    USER_FONT,
    USER_MESSAGE_COLOR,
)


class ChatWindow(QMainWindow):
    def __init__(self, chat_handler):
        super().__init__()
        self.setWindowTitle("🤖 CodeAIde 🤖")
        self.setGeometry(0, 0, CHAT_WINDOW_WIDTH, CHAT_WINDOW_HEIGHT)
        self.chat_handler = chat_handler
        self.cost_tracker = chat_handler.cost_tracker
        self.code_popup = None
        self.waiting_for_api_key = False
        self.setup_ui()
        self.add_to_chat("AI", INITIAL_MESSAGE)
        self.check_api_key()

        self.input_text.setTextColor(QColor(CHAT_WINDOW_FG))

        signal.signal(signal.SIGINT, self.sigint_handler)
        self.timer = QTimer()
        self.timer.start(500)
        self.timer.timeout.connect(lambda: None)

    def setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(8, 8, 8, 8)

        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(
            f"background-color: {CHAT_WINDOW_BG}; color: {CHAT_WINDOW_FG}; border: 1px solid #ccc; padding: 5px;"
        )
        main_layout.addWidget(self.chat_display, stretch=3)

        self.input_text = QTextEdit(self)
        self.input_text.setStyleSheet(
            f"""
            background-color: {CHAT_WINDOW_BG};
            color: {CHAT_WINDOW_FG};
            border: 1px solid #ccc;
            padding: 5px;
        """
        )
        self.input_text.setAcceptRichText(False)  # Add this line
        self.input_text.setFont(general_utils.set_font(USER_FONT))
        self.input_text.setFixedHeight(100)
        self.input_text.textChanged.connect(self.on_modify)
        self.input_text.installEventFilter(self)
        main_layout.addWidget(self.input_text, stretch=1)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.on_submit)
        button_layout.addWidget(self.submit_button)

        self.example_button = QPushButton("Use Example")
        self.example_button.clicked.connect(self.load_example)
        button_layout.addWidget(self.example_button)

        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.on_exit)
        button_layout.addWidget(self.exit_button)

        main_layout.addLayout(button_layout)

    def eventFilter(self, obj, event):
        if obj == self.input_text and event.type() == event.KeyPress:
            if (
                event.key() == Qt.Key_Return
                and not event.modifiers() & Qt.ShiftModifier
            ):
                self.on_submit()
                return True
            elif event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
                return False
        return super().eventFilter(obj, event)

    def on_submit(self):
        user_input = self.input_text.toPlainText().strip()
        if user_input:
            self.add_to_chat("User", user_input)
            self.input_text.clear()
            self.display_thinking()
            self.disable_ui_elements()
            QTimer.singleShot(100, lambda: self.process_input(user_input))
        else:
            print("ChatWindow: Empty input, not submitting")

    def on_modify(self):
        self.input_text.ensureCursorVisible()

    def add_to_chat(self, sender, message):
        color = USER_MESSAGE_COLOR if sender == "User" else AI_MESSAGE_COLOR
        font = USER_FONT if sender == "User" else AI_FONT
        sender = AI_EMOJI if sender == "AI" else sender
        html_message = general_utils.format_chat_message(sender, message, font, color)
        self.chat_display.append(html_message + "<br>")
        self.chat_display.ensureCursorVisible()

    def display_thinking(self):
        self.add_to_chat("AI", "Thinking... 🤔")

    def process_input(self, user_input):
        try:
            if self.waiting_for_api_key:
                self.handle_api_key_input(user_input)
            else:
                response = self.chat_handler.process_input(user_input)
                self.handle_response(response)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}. Please check the console window for the full traceback."
            self.add_to_chat("AI", error_message)
            print("Unexpected error in ChatWindow process_input:", file=sys.stderr)
            traceback.print_exc()
        finally:
            self.enable_ui_elements()

    def check_api_key(self):
        api_key_valid, message = self.chat_handler.check_api_key()
        if not api_key_valid:
            self.add_to_chat("AI", message)
            self.waiting_for_api_key = True
        else:
            self.waiting_for_api_key = False

    def handle_api_key_input(self, api_key):
        success, message = self.chat_handler.handle_api_key_input(api_key)
        self.remove_thinking_messages()
        if success:
            self.waiting_for_api_key = False
            self.add_to_chat(
                "AI",
                "Great! Your API key has been saved. What would you like to work on?",
            )
        else:
            self.add_to_chat("AI", message)
        self.enable_ui_elements()

    def handle_response(self, response):
        self.enable_ui_elements()

        if response["type"] == "message":
            self.add_to_chat("AI", response["message"])
        elif response["type"] == "questions":
            message = response["message"]
            questions = response["questions"]
            combined_message = f"{message}\n" + "\n".join(
                f"  * {question}" for question in questions
            )
            self.add_to_chat("AI", combined_message)
            if self.chat_handler.is_task_in_progress():
                self.add_to_chat(
                    "AI", "Please provide answers to these questions to continue."
                )
        elif response["type"] == "code":
            self.add_to_chat("AI", response["message"])
            self.update_or_create_code_popup(response)
        elif response["type"] in ["error", "internal_error"]:
            self.add_to_chat("AI", response["message"])
        elif response["type"] == "api_key_required":
            self.waiting_for_api_key = True
            self.add_to_chat("AI", response["message"])

    def remove_thinking_messages(self):
        cursor = self.chat_display.textCursor()
        cursor.setPosition(0)
        while not cursor.atEnd():
            cursor.select(cursor.BlockUnderCursor)
            if "Thinking... 🤔" in cursor.selectedText():
                cursor.removeSelectedText()
                cursor.deleteChar()
            else:
                cursor.movePosition(cursor.NextBlock)

    def disable_ui_elements(self):
        self.input_text.setEnabled(False)
        self.submit_button.setEnabled(False)
        self.example_button.setEnabled(False)

    def enable_ui_elements(self):
        self.input_text.setEnabled(True)
        self.submit_button.setEnabled(True)
        self.example_button.setEnabled(True)

    def update_or_create_code_popup(self, response):
        if self.code_popup and not self.code_popup.isHidden():
            self.code_popup.update_with_new_version(
                response["code"], response.get("requirements", [])
            )
        else:
            self.code_popup = CodePopup(
                None,
                self.chat_handler.file_handler,
                response["code"],
                response.get("requirements", []),
                self.chat_handler.run_generated_code,
            )
            self.code_popup.show()

    def load_example(self):
        example = show_example_dialog(self)
        if example:
            self.input_text.setPlainText(example)
            self.input_text.moveCursor(self.input_text.textCursor().End)
        else:
            QMessageBox.information(self, "No Selection", "No example was selected.")

    def on_exit(self):
        reply = QMessageBox.question(
            self,
            "Quit",
            "Do you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.close()

    def closeEvent(self, event):
        self.cost_tracker.print_summary()
        if self.code_popup:
            self.code_popup.close()
        super().closeEvent(event)

    def sigint_handler(self, *args):
        QApplication.quit()
