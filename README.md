<div align="center">
  <h1> PyDaffodil </h1>
</div>

<p align="center">
  <img src="https://img.shields.io/github/stars/marcuwynu23/pydaffodil.svg" alt="Stars Badge"/>
  <img src="https://img.shields.io/github/forks/marcuwynu23/pydaffodil.svg" alt="Forks Badge"/>
  <img src="https://img.shields.io/github/issues/marcuwynu23/pydaffodil.svg" alt="Issues Badge"/>
  <img src="https://img.shields.io/github/license/marcuwynu23/pydaffodil.svg" alt="License Badge"/>
</p>

`pydaffodil` is a reusable deployment framework for Python, designed to simplify the process of deploying applications to remote VPS servers.

## Features

- Check for admin privileges
- Run shell commands
- Transfer files using SCP
- Execute SSH commands
- Modular and reusable deployment steps

## Installation

```bash
pip install pydaffodil
```

## Usage

```py
from pydaffodil import Daffodil

cli = Daffodil(remote_user="root", remote_host="123.221.11.243", remote_path="/root/prod/bccs")

steps = [
    {"step": "Build the project", "command": lambda: cli.run_command("npm run build")},
    {"step": "Stop backend process on remote server", "command": lambda: cli.ssh_command("sudo forever stop 1")},
    {"step": "Transfer files to remote server", "command": lambda: cli.transfer_files("build")},
    {"step": "Restart backend process on remote server", "command": lambda: cli.ssh_command("sudo forever restartall")}
]

cli.deploy(steps)
```

## How to Republish to PyPI

To republish this project to PyPI after making changes, follow these steps:

### 1. **Update the Version Number**
In order to upload a new version to PyPI, you must increment the version number in the `setup.py` file. For example, if the current version is `1.0.0`, change it to `1.0.1`:

```python
# setup.py
setup(
    name="pydaffodil",
    version="1.0.1",  # Increment the version number here
    # Other metadata...
)
```

### 2. **Build the Package**

Run the following command to build both the source distribution (`.tar.gz`) and the wheel (`.whl`) files:

```bash
python -m build
```

This will generate the package files in the `dist/` folder.

### 3. **Upload the Package to PyPI**

Once your package is built, you can use `twine` to upload it to PyPI. Run the following command to upload the new version:

```bash
twine upload dist/*
```

You'll be prompted to enter your PyPI credentials. Make sure to have them ready.

### 4. **Test Your New Release**

After uploading, you can verify that the new version has been successfully published by installing it using `pip`:

```bash
pip install --upgrade pydaffodil
```

This will install the latest version of the package.

### 5. **Re-uploading to TestPyPI (Optional)**

If you'd like to test the release before publishing it to the official PyPI, you can upload to TestPyPI instead:

```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

Then install it from TestPyPI to verify:

```bash
pip install --index-url https://test.pypi.org/simple/ pydaffodil
```

This ensures that everything is working correctly before pushing the package to the main PyPI repository.
