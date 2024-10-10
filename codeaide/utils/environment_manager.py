import os
import subprocess
import venv
import shutil
from codeaide.utils.logging_config import get_logger

logger = get_logger()


class EnvironmentManager:
    def __init__(self, env_name="codeaide_env"):
        self.env_name = env_name
        self.env_path = os.path.join(
            os.path.expanduser("~"), ".codeaide_envs", self.env_name
        )
        self.installed_packages = set()
        self._setup_environment()
        self._get_installed_packages()

    def _setup_environment(self):
        if not os.path.exists(self.env_path):
            logger.info(f"Creating new virtual environment at {self.env_path}")
            venv.create(self.env_path, with_pip=True)
        else:
            logger.info(f"Using existing virtual environment at {self.env_path}")

    def _get_installed_packages(self):
        pip_path = (
            os.path.join(self.env_path, "bin", "pip")
            if os.name != "nt"
            else os.path.join(self.env_path, "Scripts", "pip.exe")
        )
        try:
            result = subprocess.run(
                f"{pip_path} freeze",
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            self.installed_packages = {
                pkg.split("==")[0].lower() for pkg in result.stdout.split("\n") if pkg
            }
            logger.info(f"Found {len(self.installed_packages)} installed packages")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting installed packages: {e}")

    def install_requirements(self, requirements_file):
        with open(requirements_file, "r") as f:
            required_packages = {line.strip().lower() for line in f if line.strip()}

        packages_to_install = required_packages - self.installed_packages

        if packages_to_install:
            packages_str = " ".join(packages_to_install)
            logger.info(f"Installing new packages: {packages_str}")
            pip_path = (
                os.path.join(self.env_path, "bin", "pip")
                if os.name != "nt"
                else os.path.join(self.env_path, "Scripts", "pip.exe")
            )
            try:
                subprocess.run(
                    f'"{pip_path}" install {packages_str}', shell=True, check=True
                )
                self.installed_packages.update(packages_to_install)
                logger.info(
                    f"Successfully installed {len(packages_to_install)} new packages"
                )
                return list(packages_to_install)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error installing requirements: {e}")
                return []
        else:
            logger.info("No new packages to install")
        return []

    def get_activation_command(self):
        if os.name == "nt":  # Windows
            activation_path = os.path.join(self.env_path, "Scripts", "activate.bat")
        else:  # Unix-like
            activation_path = os.path.join(self.env_path, "bin", "activate")

        logger.info(f"Generated activation command for {os.name} system")
        return (
            f"call {activation_path}"
            if os.name == "nt"
            else f"source {activation_path}"
        )

    def get_python_executable(self):
        if os.name == "nt":  # Windows
            return os.path.join(self.env_path, "Scripts", "python.exe")
        else:  # Unix-like
            return os.path.join(self.env_path, "bin", "python")

    def recreate_environment(self):
        logger.info(f"Recreating virtual environment at {self.env_path}")
        if os.path.exists(self.env_path):
            shutil.rmtree(self.env_path)
        self._setup_environment()
        self._get_installed_packages()
