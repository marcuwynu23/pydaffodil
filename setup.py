from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of your README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="pydaffodil",
    version="1.2.0",
    description="A cross-platform Python deployment framework for automated remote server deployments via SSH",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Mark Wayne Menorca",
    author_email="marcuwynu23@gmail.com",
    url="https://github.com/marcuwynu23/pydaffodil",
    project_urls={
        "Bug Reports": "https://github.com/marcuwynu23/pydaffodil/issues",
        "Source": "https://github.com/marcuwynu23/pydaffodil",
        "Documentation": "https://github.com/marcuwynu23/pydaffodil#readme",
    },
    packages=find_packages(),
    install_requires=[
        "paramiko>=2.0.0",
        "tqdm>=4.60.0",
        "colorama>=0.4.0"
    ],
    keywords=[
        "deployment",
        "ssh",
        "scp",
        "remote",
        "server",
        "automation",
        "devops",
        "ci-cd",
        "deploy",
        "vps",
        "remote-deployment",
        "ssh-deployment",
        "python-deployment",
        "cross-platform",
        "file-transfer",
        "remote-execution"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Installation/Setup",
        "Topic :: Internet :: File Transfer Protocol (FTP)",
        "Topic :: System :: Archiving :: Packaging",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Environment :: Console",
    ],
    python_requires='>=3.6',
    zip_safe=False,
)
