import subprocess
import os
import threading
import time


class ScriptRunner:
    def __init__(self, script_path):
        self.script_path = script_path
        self.is_running = False
        self.script_completed = False
        self.output_thread = None
        self.main_thread = None
        self.start_time = None

    def run_script(self):
        home_dir = os.path.expanduser("~")
        temp_dir = os.path.join(home_dir, ".temp_script_files")
        os.makedirs(temp_dir, exist_ok=True)

        bash_script_path = os.path.join(temp_dir, f"run_script_{int(time.time())}.sh")
        output_file_path = os.path.join(temp_dir, f"output_{int(time.time())}.txt")

        START_MARKER = "<<<START_OF_OUTPUT>>>"
        END_MARKER = "<<<END_OF_OUTPUT>>>"

        bash_script_content = f"""
        #!/bin/bash
        echo "{START_MARKER}" > {output_file_path}
        python -u {self.script_path} | tee -a {output_file_path}
        echo "{END_MARKER}" >> {output_file_path}
        echo "Script execution completed."
        read -p "Press any key to close this window."
        """

        with open(bash_script_path, "w") as f:
            f.write(bash_script_content)

        os.chmod(bash_script_path, 0o755)

        apple_script = f"""
        tell application "Terminal"
            do script "{bash_script_path}"
            activate
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
            while not self.script_completed:
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
                    print(f"Script output: {line}", flush=True)

        print("Script in new terminal has completed.")
        self.script_completed = True

    def print_elapsed_time(self):
        while self.is_running:
            elapsed_time = time.time() - self.start_time
            status = "completed" if self.script_completed else "running"
            print(
                f"Elapsed time: {elapsed_time:.2f} seconds. Script status: {status}",
                flush=True,
            )
            time.sleep(1)

    def start(self):
        self.is_running = True
        self.start_time = time.time()
        self.output_thread = threading.Thread(target=self.run_script)
        self.main_thread = threading.Thread(target=self.print_elapsed_time)
        self.output_thread.start()
        self.main_thread.start()

        try:
            while self.is_running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nScript runner interrupted. Cleaning up...")
            self.stop()

    def stop(self):
        self.is_running = False
        if self.output_thread:
            self.output_thread.join()
        if self.main_thread:
            self.main_thread.join()
        print("Cleanup complete.")


def main():
    script_to_run = "/Users/dollerenshaw/code/CodeAIde/temp_script.py"
    runner = ScriptRunner(script_to_run)
    runner.start()


if __name__ == "__main__":
    main()
