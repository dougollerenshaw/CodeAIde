import signal
import sys  # Add this import
from PyQt5.QtCore import (
    Qt,
    QTimer,
    QThread,
    pyqtSignal,
    QSize,  # Add QSize here
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QLabel,
    QProgressDialog,
    QAction,
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
    MODEL_SWITCH_MESSAGE,
)
from codeaide.utils.logging_config import get_logger
from codeaide.ui.traceback_dialog import TracebackDialog
import time
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import whisper
import tempfile
from codeaide.utils.general_utils import get_resource_path
import os
import traceback
import subprocess
from codeaide.utils.general_utils import get_most_recent_log_file


class AudioRecorder(QThread):
    finished = pyqtSignal(str, float)

    def __init__(self, filename, logger):
        super().__init__()
        self.filename = filename
        self.is_recording = False
        self.start_time = None
        self.logger = logger

    def run(self):
        RATE = 16000  # 16kHz to match Whisper's expected input
        self.is_recording = True
        self.start_time = time.time()
        self.logger.info(f"Starting audio recording with rate: {RATE}")

        try:
            with sd.InputStream(samplerate=RATE, channels=1) as stream:
                self.logger.info("Audio stream opened successfully")
                frames = []
                while self.is_recording:
                    data, overflowed = stream.read(RATE)
                    if overflowed:
                        self.logger.warning("Audio buffer overflowed")
                    frames.append(data)
                    self.logger.debug(f"Recorded frame with shape: {data.shape}")

            self.logger.info(f"Recording stopped. Total frames: {len(frames)}")
            audio_data = np.concatenate(frames, axis=0)
            self.logger.info(f"Raw audio data shape: {audio_data.shape}")
            self.logger.info(
                f"Raw audio data range: {audio_data.min()} to {audio_data.max()}"
            )
            self.logger.info(f"Raw audio data mean: {audio_data.mean()}")

            # Ensure audio data is in the correct range for int16
            audio_data = np.clip(audio_data * 32768, -32768, 32767).astype(np.int16)
            self.logger.info(
                f"Processed audio data range: {audio_data.min()} to {audio_data.max()}"
            )

            wavfile.write(self.filename, RATE, audio_data)
            self.logger.info(f"Audio file written to: {self.filename}")

            end_time = time.time()
            self.finished.emit(self.filename, end_time - self.start_time)
        except Exception as e:
            self.logger.error(f"Error during audio recording: {str(e)}")
            self.logger.error(traceback.format_exc())

    def stop(self):
        self.is_recording = False
        self.logger.info("Stop recording requested")


class TranscriptionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, whisper_model, filename, logger):
        super().__init__()
        self.whisper_model = whisper_model
        self.filename = filename
        self.logger = logger

    def run(self):
        try:
            self.logger.info("Starting transcription")
            read_start = time.time()
            # Read the WAV file
            sample_rate, audio_data = wavfile.read(self.filename)
            read_end = time.time()
            self.logger.info(
                f"Time to read WAV file: {read_end - read_start:.2f} seconds"
            )

            self.logger.info(
                f"Audio shape: {audio_data.shape}, Sample rate: {sample_rate}"
            )
            self.logger.info(
                f"Audio duration: {len(audio_data) / sample_rate:.2f} seconds"
            )

            # Convert to float32 and normalize
            audio_data = audio_data.astype(np.float32) / 32768.0

            self.logger.info(
                f"Audio data range: {audio_data.min()} to {audio_data.max()}"
            )

            # Transcribe
            transcribe_start = time.time()
            result = self.whisper_model.transcribe(audio_data)
            transcribe_end = time.time()
            self.logger.info(
                f"Time to transcribe: {transcribe_end - transcribe_start:.2f} seconds"
            )

            transcribed_text = result["text"]
            self.logger.info(f"Transcribed text: {transcribed_text}")
            self.finished.emit(transcribed_text)
        except Exception as e:
            self.logger.error(f"Error in transcription: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.error.emit(str(e))


class ChatWindow(QMainWindow):
    def __init__(self, chat_handler):
        super().__init__()
        self.logger = get_logger()
        self.setWindowTitle("🤖 CodeAIde 🤖")
        self.setGeometry(0, 0, CHAT_WINDOW_WIDTH, CHAT_WINDOW_HEIGHT)
        self.chat_handler = chat_handler
        self.cost_tracker = getattr(chat_handler, "cost_tracker", None)
        self.code_popup = None
        self.waiting_for_api_key = False
        self.chat_contents = []
        self.is_recording = False

        # Load microphone icons
        self.green_mic_icon = QIcon(get_resource_path("codeaide/assets/green_mic.png"))
        self.red_mic_icon = QIcon(get_resource_path("codeaide/assets/red_mic.png"))

        self.setup_ui()
        self.setup_input_placeholder()
        self.update_submit_button_state()

        # Initialize Whisper model
        QTimer.singleShot(100, self.load_whisper_model)

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

        self.logger.info("Chat window initialized")

        # Create menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        # Add "Show Logs" to the File menu
        show_logs_action = QAction("Show Logs", self)
        show_logs_action.triggered.connect(self.show_logs)
        file_menu.addAction(show_logs_action)

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
        dropdown_layout.setSpacing(5)

        # Provider dropdown
        self.provider_dropdown = QComboBox()
        self.provider_dropdown.addItems(AI_PROVIDERS.keys())
        self.provider_dropdown.setCurrentText(DEFAULT_PROVIDER)
        self.provider_dropdown.currentTextChanged.connect(self.update_model_dropdown)
        dropdown_layout.addWidget(QLabel("Provider:"))
        dropdown_layout.addWidget(self.provider_dropdown)

        # Model dropdown
        self.model_dropdown = QComboBox()
        self.update_model_dropdown(DEFAULT_PROVIDER, add_message_to_chat=False)
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
        self.input_text.setAcceptRichText(False)
        self.input_text.setFont(general_utils.set_font(USER_FONT))
        self.input_text.setFixedHeight(100)
        self.input_text.textChanged.connect(self.on_modify)
        self.input_text.installEventFilter(self)

        # Add record button
        self.record_button = QPushButton()
        self.record_button.setIcon(self.green_mic_icon)
        self.record_button.setIconSize(QSize(50, 100))  # Adjust size as needed
        self.record_button.setFixedSize(60, 110)  # Adjust size as needed
        self.record_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 25px;
            }
            QPushButton:hover {
                background-color: rgba(200, 200, 200, 50);
            }
        """
        )
        self.record_button.clicked.connect(self.toggle_recording)

        # Modify the input layout to include the record button
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.record_button)
        input_layout.addWidget(self.input_text)
        main_layout.addLayout(input_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit", self)
        self.submit_button.clicked.connect(self.on_submit)
        button_layout.addWidget(self.submit_button)

        self.example_button = QPushButton("Load Example", self)
        self.example_button.clicked.connect(self.load_example)
        button_layout.addWidget(self.example_button)

        self.new_session_button = QPushButton("New Session")
        self.new_session_button.clicked.connect(self.on_new_session_clicked)
        button_layout.addWidget(self.new_session_button)

        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(self.on_exit)
        button_layout.addWidget(self.exit_button)

        main_layout.addLayout(button_layout)

        self.logger.info("Chat window UI initialized")

        # After creating all buttons and dropdowns, add them to the list
        self.widgets_to_disable_when_recording = [
            self.submit_button,
            self.example_button,
            self.new_session_button,
            self.provider_dropdown,
            self.model_dropdown,
            self.input_text,  # Disable the input text area as well
        ]

    def setup_input_placeholder(self):
        self.placeholder_text = "Enter text here..."
        self.input_text.setPlaceholderText(self.placeholder_text)

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
        self.logger.info(
            f"ChatWindow: on_submit called with input: {user_input[:50]}..."
        )
        if not user_input:
            self.logger.info("ChatWindow: Empty input, returning")
            return

        self.logger.info("ChatWindow: Processing user input")
        self.input_text.clear()

        if self.waiting_for_api_key:
            self.logger.info("ChatWindow: Handling API key input")
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
            self.logger.info("ChatWindow: Adding user input to chat")
            self.add_to_chat("User", user_input)
            self.disable_ui_elements()
            self.add_to_chat("AI", "Thinking... 🤔")
            self.logger.info("ChatWindow: Scheduling call_process_input_async")
            QTimer.singleShot(100, lambda: self.call_process_input_async(user_input))

        self.update_submit_button_state()

    def call_process_input_async(self, user_input):
        self.logger.info(
            f"ChatWindow: call_process_input_async called with input: {user_input[:50]}..."
        )
        response = self.chat_handler.process_input(user_input)
        self.handle_response(response)

    def on_modify(self):
        self.input_text.ensureCursorVisible()
        if self.input_text.toPlainText() == self.placeholder_text:
            self.input_text.clear()
            self.input_text.setStyleSheet(
                f"background-color: {CHAT_WINDOW_BG}; color: {CHAT_WINDOW_FG}; border: 1px solid #ccc; padding: 5px;"
            )
        self.update_submit_button_state()

    def add_to_chat(self, sender, message):
        color = USER_MESSAGE_COLOR if sender == "User" else AI_MESSAGE_COLOR
        font = USER_FONT if sender == "User" else AI_FONT
        sender = AI_EMOJI if sender == "AI" else sender
        html_message = general_utils.format_chat_message(sender, message, font, color)
        self.chat_display.append(html_message + "<br>")

        # Move cursor to the end of the document
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

        self.logger.debug(f"Adding message to chat from {sender}: {message}")

        # Add message to chat contents
        self.chat_contents.append({"sender": sender, "message": message})

        # Save chat contents
        self.chat_handler.file_handler.save_chat_contents(self.chat_contents)

    def display_thinking(self):
        self.add_to_chat("AI", "Thinking... 🤔")

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
        code = response.get("code", "")
        requirements = response.get("requirements", [])
        if self.code_popup is None:
            self.code_popup = CodePopup(
                self,
                self.chat_handler.file_handler,
                self.chat_handler.terminal_manager,
                code,
                requirements,
                self.chat_handler.run_generated_code,
                chat_handler=self.chat_handler,
            )
        else:
            self.code_popup.update_with_new_version(code, requirements)

    def load_example(self):
        example = show_example_dialog(self)
        if example:
            self.input_text.setPlainText(example)
            self.input_text.moveCursor(self.input_text.textCursor().End)
            self.input_text.setFocus()
        else:
            QMessageBox.information(self, "No Selection", "No example was selected.")

    def on_exit(self):
        self.logger.info("User clicked Exit button, awaiting reply")
        reply = QMessageBox.question(
            self,
            "Quit",
            "Do you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        self.logger.info(f"User clicked Exit button, reply: {reply}")
        if reply == QMessageBox.Yes:
            self.close()

    def closeEvent(self, event):
        # Perform cleanup
        if hasattr(self, "code_popup") and self.code_popup:
            self.code_popup.terminal_manager.cleanup()

        # Use a timer to allow for a short delay before closing
        QTimer.singleShot(100, self.force_close)
        event.ignore()  # Prevent immediate closure

    def force_close(self):
        # Force close the application
        QApplication.quit()

    def sigint_handler(self, *args):
        QApplication.quit()

    def update_model_dropdown(self, provider, add_message_to_chat=False):
        self.model_dropdown.clear()
        models = AI_PROVIDERS[provider]["models"].keys()
        self.model_dropdown.addItems(models)

        # Set the current item to the first model in the list (default)
        if models:
            default_model = list(models)[0]
            self.model_dropdown.setCurrentText(default_model)
            self.logger.info(f"Set default model for {provider} to {default_model}")
        else:
            self.logger.info(f"No models available for provider {provider}")

        # Update the chat handler with the selected model if add_message_to_chat is True
        if add_message_to_chat:
            self.update_chat_handler()

    def update_chat_handler(self):
        provider = self.provider_dropdown.currentText()
        model = self.model_dropdown.currentText()

        if not provider or not model:
            return  # Exit early if either provider or model is not set

        current_version = self.chat_handler.get_latest_version()
        success, message = self.chat_handler.set_model(provider, model)

        self.logger.info(f"In update_chat_handler: current_version: {current_version}")
        self.logger.info(f"In update_chat_handler, success: {success}")
        self.logger.info(f"In update_chat_handler, message: {message}")

        if not success:
            self.logger.info("In update_chat_handler, not success")
            if message:  # This indicates that an API key is required
                self.waiting_for_api_key = True
                self.add_to_chat("AI", message)
            else:
                self.logger.info("In update_chat_handler, not success, no message")
                self.add_to_chat(
                    "System",
                    f"Failed to set model {model} for provider {provider}. Please check your API key.",
                )
            return

        # Use the constant with format
        switch_message = MODEL_SWITCH_MESSAGE.format(
            provider=provider,
            model=model,
        )

        self.add_to_chat("System", switch_message)

    def on_new_session_clicked(self):
        self.logger.info("User clicked New Session button")
        reply = QMessageBox.question(
            self,
            "New Session",
            "This will start a new session with a new chat history. Are you sure you'd like to proceed?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.logger.info("User confirmed starting a new session")
            self.chat_handler.start_new_session(self)
        else:
            self.logger.info("User cancelled starting a new session")

    def clear_chat_display(self):
        self.chat_display.clear()
        self.chat_contents = []
        self.chat_handler.file_handler.save_chat_contents(self.chat_contents)
        self.logger.info("Cleared chat display and contents in UI")

    def close_code_popup(self):
        if self.code_popup:
            self.code_popup.close()
            self.code_popup = None
            self.logger.info("Closed code pop-up")

    def load_chat_contents(self):
        self.chat_contents = self.chat_handler.file_handler.load_chat_contents()
        for item in self.chat_contents:
            self.add_to_chat(item["sender"], item["message"])
        self.logger.info(f"Loaded {len(self.chat_contents)} messages from chat log")

    def show_code(self, code, version):
        if not self.code_popup:
            self.code_popup = CodePopup(
                self,
                self.chat_handler.file_handler,
                code,
                [],
                self.chat_handler.run_generated_code,
                chat_handler=self.chat_handler,
            )
        else:
            self.code_popup.update_with_new_version(code, [])
        self.code_popup.show()
        self.code_popup.raise_()
        self.code_popup.activateWindow()

    def show_traceback_dialog(self, traceback_text):
        self.logger.info(
            f"ChatWindow: show_traceback_dialog called with text: {traceback_text[:50]}..."
        )
        dialog = TracebackDialog(self, traceback_text)
        self.logger.info("ChatWindow: Showing TracebackDialog")
        if dialog.exec_():
            self.logger.info("ChatWindow: User requested to fix the traceback")
            self.chat_handler.send_traceback_to_agent(traceback_text)
        else:
            self.logger.info("ChatWindow: User chose to ignore the traceback")

    def update_submit_button_state(self):
        if not self.is_recording:
            self.submit_button.setEnabled(bool(self.input_text.toPlainText().strip()))
        else:
            self.submit_button.setEnabled(False)

    def toggle_recording(self):
        if not hasattr(self, "is_recording"):
            self.is_recording = False

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.set_record_button_style(True)

        # Disable widgets
        for widget in self.widgets_to_disable_when_recording:
            widget.setEnabled(False)

        # Save the original HTML content
        self.original_html = self.input_text.toHtml()
        self.logger.info(f"Original HTML: {self.original_html}")

        # Check if the text box is empty or contains only placeholder text
        if (
            self.input_text.toPlainText().strip() == ""
            or self.input_text.toPlainText() == self.placeholder_text
        ):
            self.logger.info("Text box is empty or contains only placeholder text")
            # If empty, set HTML directly without any paragraph tags
            self.input_text.setHtml('<span style="color: white;">Recording...</span>')
        else:
            self.logger.info("Text box contains content")
            # Change text color to light gray while preserving formatting
            modified_html = self.original_html.replace(
                "color:#000000;", "color:#808080;"
            )
            modified_html = modified_html.replace("color:#ffffff;", "color:#808080;")

            # If there's no color specified, add it
            if "color:#808080;" not in modified_html:
                modified_html = modified_html.replace(
                    '<body style="', '<body style="color:#808080; '
                )

            # Add "Recording..." in white at the end, without extra line break
            recording_html = '<span style="color: white;">Recording...</span>'

            # Always add the recording text at the end
            modified_html = modified_html.replace(
                "</body></html>", f"{recording_html}</body></html>"
            )

            self.logger.info(f"Modified HTML before setting: {modified_html}")
            self.input_text.setHtml(modified_html)

        self.input_text.setReadOnly(True)

        # Scroll to show the "Recording..." text
        self.scroll_to_bottom()

        self.logger.info(f"Final HTML after setting: {self.input_text.toHtml()}")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            filename = temp_file.name
        self.recorder = AudioRecorder(filename, self.logger)
        self.recorder.finished.connect(self.on_recording_finished)
        self.recorder.start()
        self.logger.info("Recording started")

    def stop_recording(self):
        if self.recorder:
            self.logger.info(f"Stop recording clicked at: {time.time():.2f}")
            self.recorder.stop()
        self.is_recording = False
        self.set_record_button_style(False)

        self.scroll_to_bottom()

        # Re-enable widgets
        for widget in self.widgets_to_disable_when_recording:
            widget.setEnabled(True)
        self.logger.info("Recording stopped")

    def set_record_button_style(self, is_recording):
        self.record_button.setIcon(
            self.red_mic_icon if is_recording else self.green_mic_icon
        )

    def on_recording_finished(self, filename, recording_duration):
        self.logger.info(f"Recording saved to: {filename}")
        self.logger.info(f"Total recording time: {recording_duration:.2f} seconds")
        transcription_start = time.time()
        self.transcribe_audio(filename)
        transcription_end = time.time()
        self.logger.info(
            f"Total time from recording stop to transcription complete: {transcription_end - transcription_start:.2f} seconds"
        )

    def transcribe_audio(self, filename):
        self.logger.info("Transcribing audio")
        progress_dialog = QProgressDialog("Transcribing audio...", None, 0, 0, self)
        progress_dialog.setWindowTitle("Please Wait")
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setAutoClose(True)
        progress_dialog.setAutoReset(True)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setValue(0)
        progress_dialog.setMaximum(0)  # This makes it an indeterminate progress dialog
        progress_dialog.show()

        self.transcription_thread = TranscriptionThread(
            self.whisper_model, filename, self.logger
        )
        self.transcription_thread.finished.connect(self.on_transcription_finished)
        self.transcription_thread.error.connect(self.on_transcription_error)
        self.transcription_thread.finished.connect(progress_dialog.close)
        self.transcription_thread.error.connect(progress_dialog.close)
        self.transcription_thread.start()
        self.logger.info("Transcription thread started")

    def on_transcription_finished(self, transcribed_text):
        self.logger.info("on_transcription_finished method called")
        self.logger.info(f"Transcribed text: {transcribed_text}")
        self.logger.info(f"Original HTML: {self.original_html}")

        transcribed_text = transcribed_text.strip()

        if not self.original_html.strip():
            self.logger.info("No original text, setting transcribed text directly")
            self.input_text.setPlainText(transcribed_text)
        else:
            self.logger.info("Original text exists, appending transcribed text")
            self.input_text.setHtml(self.original_html)
            cursor = self.input_text.textCursor()
            cursor.movePosition(cursor.End)

            existing_text = self.input_text.toPlainText()
            self.logger.info(f"Existing text: '{existing_text}'")

            if existing_text and not existing_text.endswith((" ", "\n")):
                self.logger.info("Adding space before transcribed text")
                cursor.insertText(" ")

            cursor.insertText(transcribed_text)

        self.input_text.setReadOnly(False)
        self.scroll_to_bottom()

        final_text = self.input_text.toPlainText()
        self.logger.info(f"Final text: '{final_text}'")

        # Clear the original HTML
        self.original_html = ""

    def on_transcription_error(self, error_message):
        self.logger.error(f"Transcription error: {error_message}")
        QMessageBox.critical(
            self,
            "Transcription Error",
            f"An error occurred during transcription: {error_message}",
        )

    def scroll_to_bottom(self):
        # Move cursor to the end of the text
        cursor = self.input_text.textCursor()
        cursor.movePosition(cursor.End)
        self.input_text.setTextCursor(cursor)

        # Scroll to the bottom
        scrollbar = self.input_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def load_whisper_model(self):
        try:
            self.logger.info("Loading Whisper model...")
            model_path = get_resource_path("models/whisper")
            model_file = os.path.join(model_path, "tiny.pt")

            if not os.path.exists(model_file):
                self.logger.warning(
                    f"Whisper model not found at {model_file}. Attempting to download..."
                )
                whisper.load_model("tiny", download_root=model_path)

            self.whisper_model = whisper.load_model("tiny", download_root=model_path)
            self.logger.info("Whisper model loaded successfully.")
        except Exception as e:
            self.logger.error(f"Error loading Whisper model: {str(e)}")
            self.logger.error(traceback.format_exc())
            self.show_error_message(
                f"Failed to load Whisper model. Speech-to-text may not work. Error: {str(e)}"
            )

    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)

    def show_logs(self):
        try:
            if getattr(sys, "frozen", False):
                # We are running in a bundle
                log_file = get_most_recent_log_file()
            else:
                # We are running in a normal Python environment
                log_file = os.path.join(self.chat_handler.session_dir, "codeaide.log")

            if log_file and os.path.exists(log_file):
                self.logger.info(f"Opening log file: {log_file}")
                subprocess.run(["open", log_file])
            else:
                self.logger.warning("No log file found")
                QMessageBox.information(self, "Logs Not Found", "No log file found.")
        except Exception as e:
            self.logger.error(f"Error opening log file: {str(e)}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while trying to open the log file: {str(e)}",
            )
