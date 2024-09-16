import os
import sys
import subprocess
import tempfile
from codeaide.utils.run_scripts import get_unix_run_script_content, get_windows_run_script_content
from codeaide.utils.file_handler import FileHandler

def run_code(filename, requirements):
    file_handler = FileHandler()
    env_name = "codeaide_run"
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(base_dir)
    script_path = os.path.join(project_root, file_handler.output_dir, filename)
    req_path = os.path.join(project_root, file_handler.output_dir, requirements)
    
    # Create a new conda environment if it doesn't exist
    subprocess.run(["conda", "create", "-n", env_name, "python=3.8", "-y"], check=True)
    
    if sys.platform == 'darwin' or sys.platform.startswith('linux'):  # macOS or Linux
        script_content = get_unix_run_script_content(project_root, env_name, req_path, script_path)
        if sys.platform == 'darwin':
            with tempfile.NamedTemporaryFile(mode='w', suffix='.command', delete=False) as f:
                f.write(script_content)
            os.chmod(f.name, 0o755)
            subprocess.Popen(["open", f.name])
        else:  # Linux
            subprocess.Popen(["x-terminal-emulator", "-e", f"bash -c '{script_content}'"])
    elif sys.platform.startswith('win'):
        command = get_windows_run_script_content(project_root, env_name, req_path, script_path)
        subprocess.Popen(["start", "cmd", "/k", command], shell=True)