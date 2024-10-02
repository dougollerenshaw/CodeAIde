import subprocess
import os
import logging
import threading
import tempfile
import platform
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QTextEdit, QPushButton
from PyQt5.QtCore import Qt, QObject, pyqtSignal
import select
from codeaide.utils.constants import START_MARKER, END_MARKER


class ErrorDialogSignaler(QObject):
    show_dialog = pyqtSignal(str)


class ErrorDialog(QDialog):
    def __init__(self, error_text):
        super().__init__()
        self.setWindowTitle("Error Detected")
        self.setModal(True)
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setPlainText(error_text)
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)
        self.resize(600, 400)


class TerminalManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.terminals = []
        self.system = platform.system().lower()
        self.output_buffer = []
        self.error_dialog_signaler = ErrorDialogSignaler()
        self.error_dialog_signaler.show_dialog.connect(
            self.show_error_dialog_on_main_thread
        )

    def run_in_terminal(self, script_content, error_callback):
        self.logger.info("run_in_terminal called in TerminalManager")

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".command", delete=False
        ) as temp_file:
            temp_file.write(script_content)
            script_file = temp_file.name

        os.chmod(script_file, 0o755)
        self.logger.info(f"Temporary script file created: {script_file}")

        if self.system == "darwin":  # macOS
            self._run_in_macos_terminal(script_file, error_callback)
        elif self.system == "windows":
            self._run_in_windows_cmd(script_file, error_callback)
        elif self.system == "linux":
            self._run_in_linux_terminal(script_file, error_callback)
        else:
            self.logger.error(f"Unsupported operating system: {self.system}")

    def _run_in_macos_terminal(self, script_file, error_callback):
        applescript = f"""
        tell application "Terminal"
            activate
            set currentTab to do script ""
            delay 0.5
            do script "clear; {script_file}" in currentTab
        end tell
        """
        subprocess.Popen(["osascript", "-e", applescript])
        self._monitor_output(script_file, error_callback)

    def _monitor_output(self, script_file, error_callback):
        def monitor():
            self.logger.info("TerminalManager: Starting to monitor output")
            process = subprocess.Popen(
                ["/bin/bash", script_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            capturing = False
            traceback_detected = False

            for line in iter(process.stdout.readline, ""):
                self.logger.info(f"Read line: {line.strip()}")

                if START_MARKER in line:
                    capturing = True
                    continue
                elif END_MARKER in line:
                    break

                if capturing:
                    self.logger.info(f"Terminal output: {line.strip()}")
                    self.output_buffer.append(line)
                    if "Traceback" in line and not traceback_detected:
                        traceback_detected = True
                        error_callback()
                    self.logger.info(f"Traceback detected: {traceback_detected}")

            self.logger.info("Done with loop to read output")
            process.stdout.close()
            process.terminate()
            process.wait()

            if traceback_detected:
                self.logger.info("Traceback detected")
                self.logger.info(f"Output buffer: {self.output_buffer}")
                self.logger.info("Calling show_error_dialog_on_main_thread")
                self.error_dialog_signaler.show_dialog.emit("".join(self.output_buffer))
                self.logger.info("show_error_dialog_on_main_thread called")

        threading.Thread(target=monitor, daemon=True).start()

    def show_error_dialog_on_main_thread(self, error_text):
        dialog = ErrorDialog(error_text)
        dialog.exec_()
        self.output_buffer.clear()

    def cleanup(self):
        for script_file in self.terminals:
            try:
                if os.path.exists(script_file):
                    os.remove(script_file)
            except Exception as e:
                self.logger.exception(
                    f"Error while cleaning up file {script_file}: {str(e)}"
                )
        self.terminals.clear()
