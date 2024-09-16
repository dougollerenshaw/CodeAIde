import os
import shutil

class FileHandler:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = os.path.join(self.base_dir, "generated_code")
        self.version = 0

    def clear_output_dir(self):
        print(f"Clearing output directory: {self.output_dir}")
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)

    def save_code(self, code):
        self.version += 1
        file_path = os.path.join(self.output_dir, f"generated_script_{self.version}.py")
        abs_file_path = os.path.abspath(file_path)
        print(f"Attempting to save code to: {abs_file_path}")
        try:
            with open(abs_file_path, "w") as file:
                file.write(code)
            print(f"Code saved successfully to: {abs_file_path}")
            print(f"File exists after save: {os.path.exists(abs_file_path)}")
        except Exception as e:
            print(f"Error saving file: {str(e)}")
        return file_path

    def save_requirements(self, requirements):
        file_path = os.path.join(self.output_dir, f"requirements_{self.version}.txt")
        with open(file_path, "w") as file:
            for req in requirements:
                file.write(f"{req}\n")
        return file_path

    def get_versions(self):
        versions = []
        for file in os.listdir(self.output_dir):
            if file.startswith("generated_script_") and file.endswith(".py"):
                version = int(file.split("_")[2].split(".")[0])
                versions.append(version)
        return sorted(versions)

    def get_current_version(self):
        return self.version

    def get_code(self, version):
        file_path = os.path.join(self.output_dir, f"generated_script_{version}.py")
        with open(file_path, "r") as file:
            return file.read()

    def get_requirements(self, version):
        file_path = os.path.join(self.output_dir, f"requirements_{version}.txt")
        with open(file_path, "r") as file:
            return file.read().splitlines()