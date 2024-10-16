import atexit
import os
import subprocess
import sys
import threading
import logging
import queue
import time


class ScriptRunner:
    def __init__(
        self, script_content, window_name, script_name, traceback_callback=None
    ):
        self.script_content = script_content
        self.window_name = window_name
        self.script_name = script_name
        self.is_running = False
        self.output_queue = queue.Queue()
        self.traceback_buffer = []
        self.START_MARKER = f"START_OUTPUT_{self.script_name}"
        self.END_MARKER = f"END_OUTPUT_{self.script_name}"
        self.traceback_callback = traceback_callback
        self.logger = logging.getLogger(__name__)

    def run_script(self):
        home_dir = os.path.expanduser("~")
        temp_dir = os.path.join(home_dir, ".temp_script_files")
        os.makedirs(temp_dir, exist_ok=True)

        output_file_path = os.path.join(
            temp_dir, f"output_{self.script_name}_{int(time.time())}.txt"
        )
        bash_script_path = self._create_bash_script(temp_dir, output_file_path)

        if sys.platform == "darwin":
            self._run_in_macos_terminal(bash_script_path)
        elif sys.platform.startswith("linux"):
            self._run_in_linux_terminal(bash_script_path)
        elif sys.platform.startswith("win"):
            self._run_in_windows_terminal(bash_script_path)
        else:
            raise OSError("Unsupported operating system")

        self.monitor_output(output_file_path)

        if os.path.exists(bash_script_path):
            os.remove(bash_script_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

    def _create_bash_script(self, temp_dir, output_file_path):
        bash_script_path = os.path.join(
            temp_dir, f"run_script_{self.script_name}_{int(time.time())}.sh"
        )

        bash_script_content = f"""
        #!/bin/bash
        echo "{self.START_MARKER}" > {output_file_path}
        {{
        {self.script_content}
        }} 2>&1 | tee -a {output_file_path}
        EXIT_CODE=$?
        if [ $EXIT_CODE -ne 0 ]; then
            echo "ERROR: Script exited with code $EXIT_CODE" >> {output_file_path}
        fi
        echo "{self.END_MARKER}" >> {output_file_path}
        echo "Script execution completed. You can close this window."
        """

        with open(bash_script_path, "w") as f:
            f.write(bash_script_content)

        os.chmod(bash_script_path, 0o755)
        return bash_script_path

    def _run_in_macos_terminal(self, bash_script_path):
        apple_script = f"""
        tell application "Terminal"
            do script "{bash_script_path}"
            set custom title of front window to "{self.window_name} - {self.script_name}"
            activate
        end tell
        """
        subprocess.run(["osascript", "-e", apple_script])

    def _run_in_linux_terminal(self, bash_script_path):
        subprocess.Popen(["x-terminal-emulator", "-e", bash_script_path])

    def _run_in_windows_terminal(self, bash_script_path):
        subprocess.Popen(["start", "cmd", "/c", bash_script_path], shell=True)

    def monitor_output(self, output_file_path):
        while not os.path.exists(output_file_path):
            time.sleep(0.1)

        with open(output_file_path, "r") as f:
            capture = False
            while self.is_running:
                line = f.readline()
                if not line:
                    if self.END_MARKER in open(output_file_path).read():
                        break
                    time.sleep(0.1)
                    continue
                line = line.strip()
                if line == self.START_MARKER:
                    capture = True
                elif line == self.END_MARKER:
                    break
                elif capture:
                    self.process_line(line)

        self.output_queue.put(f"{self.window_name} ({self.script_name}) has completed.")
        self.is_running = False
        self.show_traceback_if_any()

    def process_line(self, line):
        self.output_queue.put(f"{self.window_name} ({self.script_name}) output: {line}")

        if "Traceback (most recent call last):" in line:
            self.traceback_buffer = [line]
        elif any(
            error in line
            for error in [
                "SyntaxError:",
                "IndentationError:",
                "ERROR: Script exited with code",
            ]
        ):
            self.traceback_buffer = [line]
            self.show_traceback_if_any()
        elif self.traceback_buffer:
            self.traceback_buffer.append(line)
            if any(
                line.startswith(error)
                for error in [
                    "AttributeError:",
                    "TypeError:",
                    "ValueError:",
                    "NameError:",
                    "ZeroDivisionError:",
                ]
            ):
                self.show_traceback_if_any()

    def show_traceback_if_any(self):
        if self.traceback_buffer:
            traceback_text = "\n".join(self.traceback_buffer)
            self.logger.info(
                f"ScriptRunner: Traceback detected: {traceback_text[:50]}..."
            )
            if self.traceback_callback:
                self.logger.info("ScriptRunner: Calling traceback callback")
                self.traceback_callback(traceback_text)
            self.traceback_buffer = []

    def start(self):
        self.is_running = True
        self.output_thread = threading.Thread(target=self.run_script)
        self.output_thread.start()

    def stop(self):
        self.is_running = False
        if self.output_thread:
            self.output_thread.join()

    def get_output(self):
        while not self.output_queue.empty():
            yield self.output_queue.get()


class TerminalManager:
    def __init__(
        self,
        environment_manager,
        traceback_callback=None,
    ):
        self.runners = []
        self.logger = logging.getLogger(__name__)
        self.traceback_callback = traceback_callback
        self.env_manager = environment_manager
        atexit.register(self.cleanup)

    def run_script(self, script_path, requirements_path):
        # Install only new requirements
        new_packages = self.env_manager.install_requirements(requirements_path)

        # Get activation command
        activation_command = self.env_manager.get_activation_command()

        # Create the script content
        script_content = self._create_script_content(
            script_path, activation_command, new_packages
        )

        # Create and start a new ScriptRunner
        runner = ScriptRunner(
            script_content,
            f"Terminal Window {len(self.runners) + 1}",
            os.path.basename(script_path),
            self.traceback_callback,
        )
        self.runners.append(runner)
        runner.start()

    def _create_script_content(self, script_path, activation_command, new_packages):
        script_name = os.path.basename(script_path)
        current_env_name = self.env_manager.get_current_env_name()
        python_executable = self.env_manager.get_python_executable()
        currently_installed_packages = self.env_manager.get_installed_packages()

        script_content = f"""
        clear
        echo "Activating environment {current_env_name}..."
        {activation_command}
        """

        if new_packages:
            script_content += 'echo "New dependencies installed:"\n'
            for package in new_packages:
                script_content += f'echo "  - {package}"\n'

        script_content += 'echo "All installed packages:"\n'
        for package in currently_installed_packages:
            script_content += f'echo "  - {package}"\n'

        script_content += f"""
        echo "Running {script_name}..."
        "{python_executable}" "{script_path}"
        echo "Script execution completed."
        """
        return script_content

    def _install_requirements(self, requirements_path):
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path]
        )

    def cleanup(self):
        for runner in self.runners:
            runner.stop()
        self.logger.info("All script runners stopped.")

        if sys.platform == "darwin":
            threading.Thread(target=self._close_macos_terminals, daemon=True).start()

    def _close_macos_terminals(self):
        apple_script = """
        tell application "Terminal"
            close every window
        end tell
        """
        subprocess.run(["osascript", "-e", apple_script], timeout=5)
        self.logger.info("All terminal windows closed.")
