import atexit
import os
import subprocess
import sys
import tempfile
import logging
import threading
import time
import pexpect
import io


class TerminalManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.terminals = []
        atexit.register(self.cleanup)

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

        # Create a unique named pipe for output
        timestamp = int(time.time() * 1000)
        fifo_path = os.path.join(
            tempfile.gettempdir(), f"codeaide_output_{os.getpid()}_{timestamp}.fifo"
        )

        try:
            os.mkfifo(fifo_path)
        except FileExistsError:
            self.logger.warning(
                f"FIFO file {fifo_path} already exists. Creating a new one."
            )
            fifo_path = os.path.join(
                tempfile.gettempdir(),
                f"codeaide_output_{os.getpid()}_{timestamp + 1}.fifo",
            )
            os.mkfifo(fifo_path)

        # Construct the AppleScript command
        applescript = f"""
        tell application "Terminal"
            activate
            set currentTab to do script ""
            delay 0.5
            do script "clear; {script_file} 2>&1 | tee {fifo_path}" in currentTab
        end tell
        """

        # Run the AppleScript command
        subprocess.Popen(["osascript", "-e", applescript])

        self.terminals.append((fifo_path, script_file))

        # Start a thread to monitor the output
        threading.Thread(
            target=self._monitor_output, args=(fifo_path, error_callback), daemon=True
        ).start()

    def _create_temp_script(self, script_content):
        with open("temp_script.command", "w") as f:
            f.write("#!/bin/bash\n")
            f.write(script_content)
            f.write('\necho "Press Enter to close this window..."\n')
            f.write("read\n")
        os.chmod("temp_script.command", 0o755)
        return os.path.abspath("temp_script.command")

    def _monitor_output(self, fifo_path, error_callback):
        try:
            with open(fifo_path, "r") as fifo:
                for line in fifo:
                    line = line.strip()
                    self.logger.info(f"Terminal output: {line}")
                    if "Traceback" in line:
                        error_callback()
        except Exception as e:
            self.logger.error(f"Error while monitoring output: {str(e)}")
        finally:
            if os.path.exists(fifo_path):
                os.remove(fifo_path)

    def _run_in_macos_terminal(self, script_content):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".command", delete=False
        ) as f:
            f.write("#!/bin/bash\n")
            f.write(script_content)
            f.write('\necho "Script execution completed. You can close this window."\n')
            f.write("exec bash\n")  # Keep the terminal open
        os.chmod(f.name, 0o755)
        process = subprocess.Popen(["open", "-a", "Terminal", f.name])
        self.terminals.append((process, f.name))
        return process

    def _run_in_linux_terminal(self, script_content):
        script_with_shell = f"""#!/bin/bash
{script_content}
echo "Script execution completed. You can close this window."
exec bash
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(script_with_shell)
        os.chmod(f.name, 0o755)
        process = subprocess.Popen(["x-terminal-emulator", "-e", f.name])
        self.terminals.append((process, f.name))
        return process

    def _run_in_windows_terminal(self, script_content):
        bat_script = f"""
@echo off
{script_content.replace('echo "', 'echo ').replace('"', '')}
echo Script execution completed. You can close this window.
cmd /k
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bat", delete=False) as f:
            f.write(bat_script)
        process = subprocess.Popen(["start", "cmd", "/c", f.name], shell=True)
        self.terminals.append((process, f.name))
        return process

    def cleanup(self):
        for fifo_path, script_file in self.terminals:
            try:
                if os.path.exists(fifo_path):
                    os.remove(fifo_path)
                if os.path.exists(script_file):
                    os.remove(script_file)
            except Exception as e:
                self.logger.exception(f"Error while cleaning up files: {str(e)}")
        self.terminals.clear()
