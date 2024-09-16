def get_unix_run_script_content(project_root, env_name, req_path, script_path):
    return f'''#!/bin/bash
cd "{project_root}"
source $(conda info --base)/etc/profile.d/conda.sh
conda activate {env_name}
if [ -f "{req_path}" ]; then
    pip install -r "{req_path}"
else
    echo "No requirements file found. Skipping package installation."
fi
clear  # Clear the screen before running the script
python "{script_path}"
echo
echo "Press any key to continue..."
read -n 1 -s
'''

def get_windows_run_script_content(project_root, env_name, req_path, script_path):
    return f'''
cd /d "{project_root}"
conda activate {env_name}
if exist "{req_path}" pip install -r "{req_path}"
cls  & REM Clear the screen before running the script
python "{script_path}"
echo.
echo Press any key to continue...
pause >nul
'''