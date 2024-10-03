"""
test_terminal.py: Multi-Script Runner with Real-Time Output Monitoring

This script provides a framework for running multiple Python scripts simultaneously
in separate terminal windows while monitoring and displaying their output in real-time.
It is designed to facilitate debugging and monitoring of multiple concurrent processes.

Key Features:
1. Concurrent Execution: Runs multiple Python scripts in parallel.
2. Isolated Environments: Each script runs in its own terminal window for clear separation.
3. Real-Time Output: Captures and displays the output of each script as it occurs.
4. Traceback Detection: Automatically detects and highlights error tracebacks.
5. Non-Blocking Operation: Allows all scripts to run independently without mutual interference.
6. Graceful Termination: Provides a mechanism to stop all scripts and clean up resources.

Operating Philosophy:
- Transparency: All script outputs are visible in real-time, aiding in debugging and monitoring.
- Independence: Each script runs in its own process, preventing inter-script dependencies or conflicts.
- Robustness: The system continues to run and monitor even if individual scripts fail.
- User Control: The main process continues until manually terminated, allowing for long-running scripts.

Usage:
1. Define the list of scripts to run in the `main()` function.
2. Run this script to start all defined scripts concurrently.
3. Monitor the output in the main terminal window.
4. Use Ctrl+C to gracefully terminate all running scripts and close their windows.

This script serves as a template for managing multiple concurrent processes within a larger system,
demonstrating principles of process management, output capturing, and error handling in a multi-script environment.
"""

import subprocess
import os
import threading
import time
import queue
import re


class ScriptRunner:
    """
    A class to run and monitor individual Python scripts in separate terminal windows.
    """

    def __init__(self, script_path, window_name):
        """
        Initialize the ScriptRunner.

        Args:
            script_path (str): Path to the Python script to run.
            window_name (str): Name for the terminal window.
        """
        print(f"Debug: ScriptRunner initialized with script_path: {script_path}")
        self.script_path = script_path
        self.script_name = os.path.basename(script_path)
        self.window_name = window_name
        self.is_running = False
        self.output_thread = None
        self.output_queue = queue.Queue()
        self.traceback_buffer = []
        self.in_traceback = False
        self.START_MARKER = f"START_OUTPUT_{self.script_name}"
        self.END_MARKER = f"END_OUTPUT_{self.script_name}"

    def run_script(self):
        """
        Run the script in a new terminal window and monitor its output.
        """
        home_dir = os.path.expanduser("~")
        temp_dir = os.path.join(home_dir, ".temp_script_files")
        os.makedirs(temp_dir, exist_ok=True)

        output_file_path = os.path.join(
            temp_dir, f"output_{self.script_name}_{int(time.time())}.txt"
        )

        bash_script_path = self._create_bash_script(
            temp_dir,
            self.script_name,
            self.window_name,
            self.script_path,
            output_file_path,
        )

        apple_script = self._create_apple_script(
            self.window_name, self.script_name, bash_script_path
        )

        subprocess.run(["osascript", "-e", apple_script])

        self.monitor_output(output_file_path, self.START_MARKER, self.END_MARKER)

        if os.path.exists(bash_script_path):
            os.remove(bash_script_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)

    def _create_bash_script(
        self, temp_dir, script_name, window_name, script_path, output_file_path
    ):
        """
        Create a bash script to run the Python script and capture its output.

        Args:
            temp_dir (str): Directory to store temporary files.
            script_name (str): Name of the Python script.
            window_name (str): Name for the terminal window.
            script_path (str): Path to the Python script.
            output_file_path (str): Path to store the script's output.

        Returns:
            str: Path to the created bash script.
        """
        bash_script_path = os.path.join(
            temp_dir, f"run_script_{script_name}_{int(time.time())}.sh"
        )

        bash_script_content = f"""
        #!/bin/bash
        echo -n -e "\033]0;{window_name} - {script_name}\007"
        echo "Debug: Script path is {script_path}"
        echo "Running script: {script_name}"
        echo "{self.START_MARKER}" > {output_file_path}
        python -u {script_path} 2>&1 | tee -a {output_file_path}
        echo "{self.END_MARKER}" >> {output_file_path}
        echo "Script execution completed. You can close this window."
        """

        with open(bash_script_path, "w") as f:
            f.write(bash_script_content)

        os.chmod(bash_script_path, 0o755)

        return bash_script_path

    def _create_apple_script(self, window_name, script_name, bash_script_path):
        """
        Create an AppleScript to open a new terminal window and run the bash script.

        Args:
            window_name (str): Name for the terminal window.
            script_name (str): Name of the Python script.
            bash_script_path (str): Path to the bash script to run.

        Returns:
            str: AppleScript content.
        """
        apple_script = f"""
        tell application "Terminal"
            do script "{bash_script_path}"
            set custom title of front window to "{window_name} - {script_name}"
        end tell
        """

        return apple_script

    def monitor_output(self, output_file_path, START_MARKER, END_MARKER):
        """
        Monitor the output file for the script's output and process it.

        Args:
            output_file_path (str): Path to the output file.
            START_MARKER (str): Marker indicating the start of the script's output.
            END_MARKER (str): Marker indicating the end of the script's output.
        """
        while not os.path.exists(output_file_path):
            time.sleep(0.1)

        with open(output_file_path, "r") as f:
            capture = False
            while self.is_running:
                line = f.readline()
                if not line:
                    if END_MARKER in open(output_file_path).read():
                        break
                    time.sleep(0.1)
                    continue
                line = line.strip()
                if line == START_MARKER:
                    capture = True
                elif line == END_MARKER:
                    break
                elif capture:
                    self.process_line(line)

        self.output_queue.put(f"{self.window_name} ({self.script_name}) has completed.")
        self.is_running = False
        self.show_traceback_if_any()

    def process_line(self, line):
        """
        Process a line of output from the script.

        Args:
            line (str): A line of output from the script.
        """
        self.output_queue.put(f"{self.window_name} ({self.script_name}) output: {line}")

        if "Traceback (most recent call last):" in line:
            self.in_traceback = True
            self.traceback_buffer = [line]
        elif self.in_traceback:
            self.traceback_buffer.append(line)
            if (
                line.startswith("AttributeError:")
                or line.startswith("TypeError:")
                or line.startswith("ValueError:")
            ):
                self.in_traceback = False
                self.show_traceback_if_any()

    def show_traceback_if_any(self):
        """
        Display the traceback if one has been captured.
        """
        if self.traceback_buffer:
            traceback_text = "\n".join(self.traceback_buffer)
            print("\nTRACEBACK DETECTED:")
            print("-----------------------")
            print(traceback_text)
            print("-----------------------")
            self.traceback_buffer = []

    def terminate(self):
        """
        Terminate the running script process.
        """
        if self.process_id:
            try:
                os.kill(int(self.process_id), signal.SIGKILL)
                print(f"Terminated process {self.process_id} for {self.script_name}")
            except ProcessLookupError:
                print(
                    f"Process {self.process_id} for {self.script_name} already terminated"
                )
            except ValueError:
                print(f"Invalid process ID {self.process_id} for {self.script_name}")

    def start(self):
        """
        Start running the script in a new thread.
        """
        self.is_running = True
        self.output_thread = threading.Thread(target=self.run_script)
        self.output_thread.start()

    def stop(self):
        """
        Stop the script runner and wait for the thread to complete.
        """
        self.is_running = False
        if self.output_thread:
            self.output_thread.join()

    def get_output(self):
        """
        Get any available output from the script.

        Yields:
            str: Lines of output from the script.
        """
        while not self.output_queue.empty():
            yield self.output_queue.get()

    def close_window(self):
        """
        Close the terminal window associated with this script.
        """
        apple_script = f"""
        tell application "Terminal"
            close (every window whose name contains "{self.window_name} - {self.script_name}")
        end tell
        """
        subprocess.run(["osascript", "-e", apple_script])


class MultiScriptRunner:
    """
    A class to run and monitor multiple Python scripts simultaneously.
    """

    def __init__(self, scripts_to_run):
        """
        Initialize the MultiScriptRunner.

        Args:
            scripts_to_run (list): List of paths to Python scripts to run.
        """
        self.scripts_to_run = scripts_to_run
        self.runners = []
        self.completion_message_delivered = False

    def start(self):
        """
        Start running all scripts and monitor their output.
        """
        for i, script in enumerate(self.scripts_to_run):
            print(f"Creating ScriptRunner for: {script}")
            runner = ScriptRunner(script, f"Terminal Window {i+1}")
            self.runners.append(runner)
            runner.start()

        print(f"Started {len(self.runners)} script runners.")

        try:
            while True:
                all_completed = all(not runner.is_running for runner in self.runners)

                for runner in self.runners:
                    for output in runner.get_output():
                        print(output, flush=True)

                if all_completed and not self.completion_message_delivered:
                    time.sleep(0.5)  # Add a small delay

                    # Check one more time for any remaining output
                    for runner in self.runners:
                        for output in runner.get_output():
                            print(output, flush=True)

                    print("All scripts have completed. Press Ctrl+C to exit.")
                    self.completion_message_delivered = True

                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received. Stopping all runners...")
        finally:
            self.stop()
            self.close_all_windows()

    def stop(self):
        """
        Stop all script runners.
        """
        for runner in self.runners:
            runner.stop()
        print("All script runners stopped.")

    def close_all_windows(self):
        """
        Close all terminal windows associated with the running scripts.
        """
        apple_script = """
        tell application "Terminal"
            close every window
        end tell
        """
        subprocess.run(["osascript", "-e", apple_script])
        print("All terminal windows closed.")


def main():
    """
    Main function to run multiple Python scripts simultaneously.
    """
    scripts_to_run = [
        "/Users/dollerenshaw/code/CodeAIde/temp_script.py",
        "/Users/dollerenshaw/code/CodeAIde/temp_script_2.py",
        "/Users/dollerenshaw/code/CodeAIde/temp_script_3.py",
    ]
    print("Scripts to run:")
    for script in scripts_to_run:
        print(f"  - {script}")
    multi_runner = MultiScriptRunner(scripts_to_run)
    multi_runner.start()


if __name__ == "__main__":
    main()
