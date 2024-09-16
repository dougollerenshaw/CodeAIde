import subprocess
import os
import sys
import venv

class EnvironmentManager:
    def __init__(self, env_name="codeaide_env"):
        self.env_name = env_name
        self.env_path = os.path.join(os.path.expanduser("~"), ".codeaide_envs", self.env_name)
        self.installed_packages = set()
        self._setup_environment()
        self._get_installed_packages()

    def _setup_environment(self):
        if not os.path.exists(self.env_path):
            venv.create(self.env_path, with_pip=True)

    def _get_installed_packages(self):
        pip_path = os.path.join(self.env_path, "bin", "pip") if os.name != 'nt' else os.path.join(self.env_path, "Scripts", "pip.exe")
        result = subprocess.run(
            f"{pip_path} freeze",
            shell=True, check=True, capture_output=True, text=True
        )
        self.installed_packages = {
            pkg.split('==')[0].lower() for pkg in result.stdout.split('\n') if pkg
        }

    def install_requirements(self, requirements_file):
        pip_path = os.path.join(self.env_path, "bin", "pip") if os.name != 'nt' else os.path.join(self.env_path, "Scripts", "pip.exe")
        with open(requirements_file, 'r') as f:
            required_packages = {line.strip().lower() for line in f if line.strip()}

        packages_to_install = required_packages - self.installed_packages

        if packages_to_install:
            packages_str = ' '.join(packages_to_install)
            try:
                subprocess.run(
                    f"{pip_path} install {packages_str}",
                    shell=True, check=True
                )
                self.installed_packages.update(packages_to_install)
                return list(packages_to_install)
            except subprocess.CalledProcessError as e:
                print(f"Error installing requirements: {e}")
                return []
        return []

    def get_activation_command(self):
        if os.name == 'nt':  # Windows
            return f"call {os.path.join(self.env_path, 'Scripts', 'activate.bat')}"
        else:  # Unix-like
            return f"source {os.path.join(self.env_path, 'bin', 'activate')}"