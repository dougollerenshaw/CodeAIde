import os
import platform
import sys
from pathlib import Path
from decouple import Config, RepositoryEnv


class ConfigManager:
    def __init__(self):
        self.is_packaged_app = getattr(sys, "frozen", False)
        if self.is_packaged_app:
            self.config_dir = self._get_app_config_dir()
            self.keyring_service = "CodeAIde"
        else:
            self.config_dir = Path(__file__).parent.parent.parent
            self.env_file = self.config_dir / ".env"

    def _get_app_config_dir(self):
        system = platform.system()
        if system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "CodeAIde"
        elif system == "Windows":
            return Path(os.getenv("APPDATA")) / "CodeAIde"
        else:  # Linux and others
            return Path.home() / ".config" / "codeaide"

    def get_api_key(self, provider):
        if self.is_packaged_app:
            import keyring

            return keyring.get_password(
                self.keyring_service, f"{provider.upper()}_API_KEY"
            )
        else:
            config = Config(RepositoryEnv(self.env_file))
            return config(f"{provider.upper()}_API_KEY", default=None)

    def set_api_key(self, provider, api_key):
        if self.is_packaged_app:
            import keyring

            keyring.set_password(
                self.keyring_service, f"{provider.upper()}_API_KEY", api_key
            )
        else:
            with open(self.env_file, "a") as f:
                f.write(f'\n{provider.upper()}_API_KEY="{api_key}"\n')

    def delete_api_key(self, provider):
        if self.is_packaged_app:
            import keyring

            keyring.delete_password(self.keyring_service, f"{provider.upper()}_API_KEY")
        else:
            # Read the .env file, remove the line with the API key, and write it back
            if self.env_file.exists():
                lines = self.env_file.read_text().splitlines()
                lines = [
                    line
                    for line in lines
                    if not line.startswith(f"{provider.upper()}_API_KEY=")
                ]
                self.env_file.write_text("\n".join(lines) + "\n")
