import subprocess
import os

class EnvironmentManager:
    def __init__(self, env_name="codeaide_run"):
        self.env_name = env_name
        self.installed_packages = set()
        self._setup_environment()
        self._get_installed_packages()

    def _setup_environment(self):
        try:
            subprocess.run(["conda", "create", "-n", self.env_name, "python=3.8", "-y"], check=True)
        except subprocess.CalledProcessError:
            # Environment might already exist, which is fine
            pass

    def _get_installed_packages(self):
        result = subprocess.run(
            f"conda run -n {self.env_name} pip freeze",
            shell=True, check=True, capture_output=True, text=True
        )
        self.installed_packages = {
            pkg.split('==')[0].lower() for pkg in result.stdout.split('\n') if pkg
        }

    def install_requirements(self, requirements_file):
        with open(requirements_file, 'r') as f:
            required_packages = {line.strip().lower() for line in f if line.strip()}

        packages_to_install = required_packages - self.installed_packages

        if packages_to_install:
            packages_str = ' '.join(packages_to_install)
            try:
                subprocess.run(
                    f"conda run -n {self.env_name} pip install {packages_str}",
                    shell=True, check=True
                )
                self.installed_packages.update(packages_to_install)
                return list(packages_to_install)  # Return list of newly installed packages
            except subprocess.CalledProcessError as e:
                print(f"Error installing requirements: {e}")
                return []
        return []  # Return empty list if no new packages were installed

    def get_activation_command(self):
        if os.name == 'nt':  # Windows
            return f"call activate {self.env_name}"
        else:  # Unix-like
            return f"source $(conda info --base)/etc/profile.d/conda.sh && conda activate {self.env_name}"