import subprocess
import os
import logging
import threading
import tempfile
import time
import platform


class TerminalManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.terminals = []
        self.system = platform.system().lower()

    def run_in_terminal(self, script_content, error_callback):
        self.logger.info("run_in_terminal called in TerminalManager")

        # Create a temporary script file
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

    def _run_in_windows_cmd(self, script_file, error_callback):
        cmd = f'start cmd /K "{script_file}"'
        subprocess.Popen(cmd, shell=True)
        self._monitor_output(script_file, error_callback)

    def _run_in_linux_terminal(self, script_file, error_callback):
        cmd = f'x-terminal-emulator -e "{script_file}"'
        subprocess.Popen(cmd, shell=True)
        self._monitor_output(script_file, error_callback)

    def _monitor_output(self, script_file, error_callback):
        def monitor():
            process = subprocess.Popen(
                ["/bin/bash", script_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in process.stdout:
                self.logger.info(f"Terminal output: {line.strip()}")
                if "Traceback" in line:
                    error_callback()
            process.wait()

        threading.Thread(target=monitor, daemon=True).start()

    def cleanup(self):
        for _, script_file in self.terminals:
            try:
                if os.path.exists(script_file):
                    os.remove(script_file)
            except Exception as e:
                self.logger.exception(
                    f"Error while cleaning up file {script_file}: {str(e)}"
                )
        self.terminals.clear()
