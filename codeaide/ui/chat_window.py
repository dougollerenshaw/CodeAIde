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
    QComboBox,
    QLabel,
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
    AI_PROVIDERS,
    DEFAULT_PROVIDER,
    DEFAULT_MODEL,
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

        # Check API key status
        if not self.chat_handler.api_key_valid:
            self.waiting_for_api_key = True
            self.add_to_chat("AI", self.chat_handler.api_key_message)
        else:
            self.add_to_chat("AI", INITIAL_MESSAGE)

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

        # Create a widget for the dropdowns
        dropdown_widget = QWidget()
        dropdown_layout = QHBoxLayout(dropdown_widget)
        dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_layout.setSpacing(5)  # Minimal spacing between items

        # Provider dropdown
        self.provider_dropdown = QComboBox()
        self.provider_dropdown.addItems(AI_PROVIDERS.keys())
        self.provider_dropdown.setCurrentText(DEFAULT_PROVIDER)
        self.provider_dropdown.currentTextChanged.connect(self.update_model_dropdown)
        dropdown_layout.addWidget(QLabel("Provider:"))
        dropdown_layout.addWidget(self.provider_dropdown)

        # Model dropdown
        self.model_dropdown = QComboBox()
        self.update_model_dropdown(DEFAULT_PROVIDER)
        self.model_dropdown.setCurrentText(DEFAULT_MODEL)
        self.model_dropdown.currentTextChanged.connect(self.update_chat_handler)
        dropdown_layout.addWidget(QLabel("Model:"))
        dropdown_layout.addWidget(self.model_dropdown)

        # Add stretch to push everything to the left
        dropdown_layout.addStretch(1)

        # Add the dropdown widget to the main layout
        main_layout.addWidget(dropdown_widget)

        # Chat display
        self.chat_display = QTextEdit(self)
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet(
            f"background-color: {CHAT_WINDOW_BG}; color: {CHAT_WINDOW_FG}; border: 1px solid #ccc; padding: 5px;"
        )
        main_layout.addWidget(self.chat_display, stretch=3)

        # Input text area
        self.input_text = QTextEdit(self)
        self.input_text.setStyleSheet(
            f"background-color: {CHAT_WINDOW_BG}; color: {CHAT_WINDOW_FG}; border: 1px solid #ccc; padding: 5px;"
        )
        self.input_text.setAcceptRichText(False)  # Add this line
        self.input_text.setFont(general_utils.set_font(USER_FONT))
        self.input_text.setFixedHeight(100)
        self.input_text.textChanged.connect(self.on_modify)
        self.input_text.installEventFilter(self)
        main_layout.addWidget(self.input_text, stretch=1)

        # Buttons
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.on_submit)
        button_layout.addWidget(self.submit_button)

        self.example_button = QPushButton("Load Example", self)
        self.example_button.clicked.connect(self.load_example)
        button_layout.addWidget(self.example_button)

        self.exit_button = QPushButton("Exit", self)
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
        if not user_input:
            return

        if self.waiting_for_api_key:
            (
                success,
                message,
                self.waiting_for_api_key,
            ) = self.chat_handler.handle_api_key_input(user_input)
            self.remove_thinking_messages()
            self.add_to_chat("AI", message)
            if success:
                self.enable_ui_elements()
        else:
            self.process_input(user_input)

        self.input_text.clear()

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
            response = self.chat_handler.process_input(user_input)
            self.handle_response(response)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}. Please check the console window for the full traceback."
            self.add_to_chat("AI", error_message)
            print("Unexpected error in ChatWindow process_input:", file=sys.stderr)
            traceback.print_exc()
        finally:
            self.enable_ui_elements()

    def handle_response(self, response):
        self.enable_ui_elements()
        self.remove_thinking_messages()

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

    def update_model_dropdown(self, provider):
        self.model_dropdown.clear()
        models = AI_PROVIDERS[provider]["models"].keys()
        self.model_dropdown.addItems(models)

        # Set the current item to the first model in the list
        if models:
            self.model_dropdown.setCurrentText(list(models)[0])
        else:
            print(f"No models available for provider {provider}")

    def update_chat_handler(self):
        provider = self.provider_dropdown.currentText()
        model = self.model_dropdown.currentText()

        # Check if a valid model is selected
        if not model:
            print(f"No valid model selected for provider {provider}")
            return

        current_version = self.chat_handler.get_latest_version()
        success, message = self.chat_handler.set_model(provider, model)

        if not success:
            if message:  # This indicates that an API key is required
                self.waiting_for_api_key = True
                self.add_to_chat("AI", message)
            else:
                self.add_to_chat(
                    "System",
                    f"Failed to set model {model} for provider {provider}. Please check your API key.",
                )
            return

        self.chat_handler.clear_conversation_history()
        self.chat_handler.set_latest_version(
            current_version
        )  # Maintain the version number

        # Add a message about switching models and the current version
        self.add_to_chat(
            "System",
            f"""
{'='*50}
Switched to {provider} - {model}
Starting a new conversation with this model.
Current code version: {current_version}
Any new code will be versioned starting from {self.increment_version(current_version)}
{'='*50}
""",
        )

    def increment_version(self, version):
        major, minor = map(int, version.split("."))
        return f"{major}.{minor + 1}"
