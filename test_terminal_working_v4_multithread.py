import subprocess
import os
import threading
import time
import queue
import logging
import signal


class ScriptRunner:
    def __init__(self, script_path, window_name):
        print(f"Debug: ScriptRunner initialized with script_path: {script_path}")
        self.script_path = script_path
        self.script_name = os.path.basename(script_path)
        self.window_name = window_name
        self.is_running = False
        self.output_thread = None
        self.output_queue = queue.Queue()

    def run_script(self):
        home_dir = os.path.expanduser("~")
        temp_dir = os.path.join(home_dir, ".temp_script_files")
        os.makedirs(temp_dir, exist_ok=True)

        bash_script_path = os.path.join(
            temp_dir, f"run_script_{self.script_name}_{int(time.time())}.sh"
        )
        output_file_path = os.path.join(
            temp_dir, f"output_{self.script_name}_{int(time.time())}.txt"
        )

        START_MARKER = "<<<START_OF_OUTPUT>>>"
        END_MARKER = "<<<END_OF_OUTPUT>>>"

        bash_script_content = f"""
        #!/bin/bash
        echo -n -e "\033]0;{self.window_name} - {self.script_name}\007"
        echo "Debug: Script path is {self.script_path}"
        echo "Running script: {self.script_name}"
        echo "{START_MARKER}" > {output_file_path}
        python -u {self.script_path} | tee -a {output_file_path}
        echo "{END_MARKER}" >> {output_file_path}
        echo "Script execution completed. You can close this window."
        """

        with open(bash_script_path, "w") as f:
            f.write(bash_script_content)

        os.chmod(bash_script_path, 0o755)

        apple_script = f"""
        tell application "Terminal"
            do script "{bash_script_path}"
        end tell
        """

        subprocess.run(["osascript", "-e", apple_script])

        self.monitor_output(output_file_path, START_MARKER, END_MARKER)

        # Clean up
        if os.path.exists(bash_script_path):
            os.remove(bash_script_path)
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)

    def monitor_output(self, output_file_path, START_MARKER, END_MARKER):
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
                    self.output_queue.put(
                        f"{self.window_name} ({self.script_name}) output: {line}"
                    )

        self.output_queue.put(f"{self.window_name} ({self.script_name}) has completed.")
        self.is_running = False

    def terminate(self):
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

    def close_window(self):
        apple_script = f"""
        tell application "Terminal"
            close (every window whose name contains "{self.window_name} - {self.script_name}")
        end tell
        """
        subprocess.run(["osascript", "-e", apple_script])


class MultiScriptRunner:
    def __init__(self, scripts_to_run):
        self.scripts_to_run = scripts_to_run
        self.runners = []

    def start(self):
        for i, script in enumerate(self.scripts_to_run):
            print(f"Creating ScriptRunner for: {script}")
            runner = ScriptRunner(script, f"Terminal Window {i+1}")
            self.runners.append(runner)
            runner.start()

        print(f"Started {len(self.runners)} script runners.")

        try:
            while True:
                if all(not runner.is_running for runner in self.runners):
                    pass  # All scripts have completed, but we'll keep running silently
                for runner in self.runners:
                    for output in runner.get_output():
                        print(output, flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nMultiScriptRunner interrupted. Cleaning up...")
            self.stop()
            self.close_all_windows()

    def stop(self):
        for runner in self.runners:
            runner.stop()
        print("All script runners stopped.")

    def close_all_windows(self):
        apple_script = """
        tell application "Terminal"
            close every window
        end tell
        """
        subprocess.run(["osascript", "-e", apple_script])
        print("All terminal windows closed.")


def main():
    scripts_to_run = [
        "/Users/dollerenshaw/code/CodeAIde/temp_script.py",
        "/Users/dollerenshaw/code/CodeAIde/temp_script_2.py",
    ]
    print("Scripts to run:")
    for script in scripts_to_run:
        print(f"  - {script}")
    multi_runner = MultiScriptRunner(scripts_to_run)
    try:
        multi_runner.start()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Stopping all runners...")
    finally:
        multi_runner.stop()


if __name__ == "__main__":
    main()
