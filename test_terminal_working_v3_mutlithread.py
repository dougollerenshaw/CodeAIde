import subprocess
import os
import threading
import time
import queue
import logging


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
        echo "Debug: Script path is {self.script_path}"
        echo "Running script: {self.script_name}"
        echo "{START_MARKER}" > {output_file_path}
        python -u {self.script_path} | tee -a {output_file_path}
        echo "{END_MARKER}" >> {output_file_path}
        echo "Script execution completed."
        read -n 1 -s -r -p "Press any key to close this window..."
        """

        with open(bash_script_path, "w") as f:
            f.write(bash_script_content)

        os.chmod(bash_script_path, 0o755)

        apple_script = f"""
        tell application "Terminal"
            set newTab to do script "{bash_script_path}"
            delay 1
            set custom title of newTab to "{self.window_name} - {self.script_name}"
            activate
            set windowId to id of window 1 where its tab 1 = newTab
            delay 1
            repeat while newTab is busy
                delay 1
            end repeat
            close window id windowId
        end tell
        """

        print(
            f"Debug: Running AppleScript for {self.script_name} with bash script: {bash_script_path}"
        )
        subprocess.Popen(["osascript", "-e", apple_script])

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
            while any(runner.is_running for runner in self.runners):
                for runner in self.runners:
                    for output in runner.get_output():
                        print(output, flush=True)
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nMultiScriptRunner interrupted. Cleaning up...")
            self.stop()

    def stop(self):
        for runner in self.runners:
            runner.stop()
        print("All script runners stopped.")


def main():
    scripts_to_run = [
        "/Users/dollerenshaw/code/CodeAIde/temp_script.py",
        "/Users/dollerenshaw/code/CodeAIde/temp_script_2.py",
    ]
    print("Scripts to run:")
    for script in scripts_to_run:
        print(f"  - {script}")
    multi_runner = MultiScriptRunner(scripts_to_run)
    multi_runner.start()


if __name__ == "__main__":
    main()
