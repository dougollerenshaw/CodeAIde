from setuptools import setup, find_packages
from version import __version__

# Read requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="codeaide",
    version=__version__,
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "codeaide=codeaide.__main__:main",
        ],
    },
    author="Doug Ollerenshaw",
    author_email="d.ollerenshaw@gmail.com",
    description="A chat application leveraging large language models (LLMs) for code generation and execution",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dougollerenshaw/CodeAIde",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
