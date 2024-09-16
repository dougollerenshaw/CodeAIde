import subprocess
import tempfile
import os
import sys
import atexit

class TerminalManager:
    def __init__(self):
        self.terminals = []
        atexit.register(self.cleanup)

    def run_in_terminal(self, script_content):
        if sys.platform == 'darwin':  # macOS
            return self._run_in_macos_terminal(script_content)
        elif sys.platform.startswith('linux'):
            return self._run_in_linux_terminal(script_content)
        elif sys.platform.startswith('win'):
            return self._run_in_windows_terminal(script_content)
        else:
            raise OSError("Unsupported operating system")

    def _run_in_macos_terminal(self, script_content):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.command', delete=False) as f:
            f.write('#!/bin/bash\n')
            f.write(script_content)
            f.write('\necho "Script execution completed. You can close this window."\n')
            f.write('exec bash\n')  # Keep the terminal open
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
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
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bat', delete=False) as f:
            f.write(bat_script)
        process = subprocess.Popen(["start", "cmd", "/c", f.name], shell=True)
        self.terminals.append((process, f.name))
        return process

    def cleanup(self):
        for _, file_name in self.terminals:
            try:
                os.remove(file_name)
            except:
                pass  # Ignore errors during cleanup