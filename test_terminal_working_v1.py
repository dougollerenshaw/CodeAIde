import subprocess
import os
import threading
import time


def run_script_in_new_terminal(script_path):
    # Use a directory in the user's home folder
    home_dir = os.path.expanduser("~")
    temp_dir = os.path.join(home_dir, ".temp_script_files")
    os.makedirs(temp_dir, exist_ok=True)

    bash_script_path = os.path.join(temp_dir, "run_script.sh")
    output_file_path = os.path.join(temp_dir, "output.txt")

    # Unique markers for start and end of output
    START_MARKER = "<<<START_OF_OUTPUT>>>"
    END_MARKER = "<<<END_OF_OUTPUT>>>"

    # Create a bash script to run the Python script and handle output
    bash_script_content = f"""
    #!/bin/bash
    echo "{START_MARKER}" > {output_file_path}
    python -u {script_path} | tee -a {output_file_path}
    echo "{END_MARKER}" >> {output_file_path}
    echo "Script execution completed."
    read -p "Press any key to close this window."
    """

    # Write the bash script content to a temporary file
    with open(bash_script_path, "w") as f:
        f.write(bash_script_content)

    # Make the bash script executable
    os.chmod(bash_script_path, 0o755)

    # AppleScript to run the bash script in a new Terminal window
    apple_script = f"""
    tell application "Terminal"
        do script "{bash_script_path}"
        activate
    end tell
    """

    # Function to read from the output file and print output
    def read_and_print_output():
        # Wait for the output file to be created
        while not os.path.exists(output_file_path):
            time.sleep(0.1)

        with open(output_file_path, "r") as f:
            capture = False
            while True:
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
                    print(line, flush=True)

    # Start a thread to read and print output
    output_thread = threading.Thread(target=read_and_print_output)
    output_thread.start()

    # Run the AppleScript command
    subprocess.run(["osascript", "-e", apple_script])

    print("A new terminal window has opened running the script.")
    print("Capturing output:")

    # Wait for the output thread to finish
    output_thread.join()

    print("\nScript in new terminal has completed.")
    print("You can close the new terminal window by pressing any key there.")

    # Clean up
    if os.path.exists(bash_script_path):
        os.remove(bash_script_path)
    if os.path.exists(output_file_path):
        os.remove(output_file_path)
    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
        os.rmdir(temp_dir)


# Hard-coded path to the script we want to run
script_to_run = "/Users/dollerenshaw/code/CodeAIde/temp_script.py"

# Run the script in a new terminal
run_script_in_new_terminal(script_to_run)
