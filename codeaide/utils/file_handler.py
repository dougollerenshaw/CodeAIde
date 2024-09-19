import os
import shutil


class FileHandler:
    def __init__(self, base_dir=None):
        if base_dir is None:
            self.base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
        else:
            self.base_dir = base_dir
        self.output_dir = os.path.join(self.base_dir, "generated_code")
        self.versions_dict = {}
        self._ensure_output_dir_exists()

    def _ensure_output_dir_exists(self):
        os.makedirs(self.output_dir, exist_ok=True)

    def clear_output_dir(self):
        print(f"Clearing output directory: {self.output_dir}")
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

    def save_code(self, code, version, version_description, requirements=[]):
        code_path = os.path.join(self.output_dir, f"generated_script_{version}.py")
        requirements_path = os.path.join(self.output_dir, f"requirements_{version}.txt")
        abs_code_path = os.path.abspath(code_path)
        abs_req_path = os.path.abspath(requirements_path)
        print(f"Attempting to save code to: {abs_code_path}")
        try:
            with open(abs_code_path, "w") as file:
                file.write(code)
            print(f"Code saved successfully to: {abs_code_path}")
            print(f"Saving associated requirements to: {abs_req_path}")
            self.save_requirements(requirements, version)
        except Exception as e:
            print(f"Error saving file: {str(e)}")
        print(f"Adding version {version} to versions_dict")
        self.versions_dict[version] = {
            "version_description": version_description,
            "requirements": requirements,
            "code_path": abs_code_path,
            "requirements_path": abs_req_path,
        }
        print(f"Current versions dict: {self.versions_dict}")
        return code_path

    def save_requirements(self, requirements, version):
        file_path = os.path.join(self.output_dir, f"requirements_{version}.txt")
        with open(file_path, "w") as file:
            for req in requirements:
                file.write(f"{req}\n")
        return file_path

    def get_versions_dict(self):
        return self.versions_dict

    def get_code(self, version):
        file_path = os.path.join(self.output_dir, f"generated_script_{version}.py")
        with open(file_path, "r") as file:
            return file.read()

    def get_requirements(self, version):
        file_path = os.path.join(self.output_dir, f"requirements_{version}.txt")
        with open(file_path, "r") as file:
            return file.read().splitlines()
