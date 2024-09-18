import pytest
import os
import tempfile
from codeaide.utils.file_handler import FileHandler

@pytest.fixture
def file_handler():
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = FileHandler(base_dir=temp_dir)
        yield handler

def test_clear_output_dir(file_handler):
    # Create a file in the output directory
    test_file = os.path.join(file_handler.output_dir, "test.txt")
    with open(test_file, "w") as f:
        f.write("test")
    
    file_handler.clear_output_dir()
    
    assert os.path.exists(file_handler.output_dir)
    assert len(os.listdir(file_handler.output_dir)) == 0

def test_save_code(file_handler):
    code = "print('Hello, World!')"
    version = "1.0"
    description = "Initial version"
    requirements = ["pytest"]
    
    code_path = file_handler.save_code(code, version, description, requirements)
    
    assert os.path.exists(code_path)
    with open(code_path, "r") as f:
        assert f.read() == code
    
    assert version in file_handler.versions_dict
    assert file_handler.versions_dict[version]['version_description'] == description
    assert file_handler.versions_dict[version]['requirements'] == requirements

def test_save_requirements(file_handler):
    requirements = ["pytest", "requests"]
    version = "1.0"
    
    req_path = file_handler.save_requirements(requirements, version)
    
    assert os.path.exists(req_path)
    with open(req_path, "r") as f:
        assert f.read().splitlines() == requirements

def test_get_versions_dict(file_handler):
    file_handler.save_code("code1", "1.0", "Version 1")
    file_handler.save_code("code2", "2.0", "Version 2")
    
    versions_dict = file_handler.get_versions_dict()
    
    assert "1.0" in versions_dict
    assert "2.0" in versions_dict

def test_get_code(file_handler):
    original_code = "print('Test')"
    file_handler.save_code(original_code, "1.0", "Test version")
    
    retrieved_code = file_handler.get_code("1.0")
    
    assert retrieved_code == original_code

def test_get_requirements(file_handler):
    original_requirements = ["pytest", "requests"]
    file_handler.save_code("code", "1.0", "Test", original_requirements)
    
    retrieved_requirements = file_handler.get_requirements("1.0")
    
    assert retrieved_requirements == original_requirements

def test_nonexistent_version(file_handler):
    with pytest.raises(FileNotFoundError):
        file_handler.get_code("nonexistent")
    
    with pytest.raises(FileNotFoundError):
        file_handler.get_requirements("nonexistent")