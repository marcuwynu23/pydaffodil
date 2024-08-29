 
from setuptools import setup, find_packages

setup(
    name="daffodil-cli",
    version="1.0.0",
    description="A reusable deployment framework for Python.",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "paramiko",
        "tqdm",
        "colorama"
    ],
    entry_points={
        "console_scripts": [
            "daffodil-cli = daffodil_cli.deploy:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
