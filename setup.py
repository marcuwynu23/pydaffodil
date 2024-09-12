from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pydaffodil",
    version="1.0.4",
    description="A reusable deployment framework for Python.",
    long_description=long_description,  # Use README.md for the long description
    long_description_content_type="text/markdown",  # Ensure content is treated as markdown
    author="Mark Wayne Menorca",
    author_email="marcuwynu23@gmail.com",
    packages=find_packages(),
    install_requires=[
        "paramiko",
        "tqdm",
        "colorama"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
