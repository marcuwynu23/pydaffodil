<div align="center">
  <h1>🌼 PyDaffodil</h1>
  <p><strong>Cross-Platform Python Deployment Framework</strong></p>
  <p>Automate remote server deployments with ease. Transfer files, execute commands, and manage deployments across Windows, macOS, and Linux.</p>
</div>

<p align="center">
  <img src="https://img.shields.io/pypi/v/pydaffodil?color=blue&label=PyPI" alt="PyPI Version"/>
  <img src="https://img.shields.io/pypi/pyversions/pydaffodil?color=green" alt="Python Versions"/>
  <img src="https://img.shields.io/pypi/dm/pydaffodil?color=orange" alt="Downloads"/>
  <img src="https://img.shields.io/github/stars/marcuwynu23/pydaffodil.svg" alt="Stars Badge"/>
  <img src="https://img.shields.io/github/forks/marcuwynu23/pydaffodil.svg" alt="Forks Badge"/>
  <img src="https://img.shields.io/github/issues/marcuwynu23/pydaffodil.svg" alt="Issues Badge"/>
  <img src="https://img.shields.io/github/license/marcuwynu23/pydaffodil.svg" alt="License Badge"/>
</p>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [API Reference](#api-reference)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

**PyDaffodil** is a powerful, cross-platform Python deployment framework designed to simplify and automate the process of deploying applications to remote servers via SSH. Whether you're deploying to a VPS, cloud instance, or dedicated server, PyDaffodil provides a clean, intuitive API for managing your deployment workflows.

### Key Benefits

- ✅ **Cross-Platform**: Works seamlessly on Windows, macOS, and Linux
- ✅ **No Admin Required**: Runs without administrator privileges
- ✅ **Efficient Transfers**: Automatically archives files before transfer for faster deployments
- ✅ **Secure**: Supports SSH key and password authentication
- ✅ **Progress Tracking**: Visual progress bars for file transfers and operations
- ✅ **Modular**: Build reusable deployment steps with a simple, declarative API

## ✨ Features

### Core Capabilities

- **🔐 Secure SSH Connections**: Connect using SSH keys (RSA, DSA, ECDSA, Ed25519) or password authentication
- **📦 Smart File Transfer**: Automatically creates archives before transfer and extracts them on the remote server
- **⚡ Remote Command Execution**: Execute shell commands and SSH commands on remote servers
- **📁 Directory Management**: Create directories and manage file structures on remote servers
- **🎨 Colored Output**: Beautiful, color-coded terminal output for better visibility
- **📊 Progress Tracking**: Real-time progress bars for file operations
- **🔄 Deployment Workflows**: Chain multiple deployment steps together for complex workflows

### Technical Features

- Cross-platform archive creation and extraction (ZIP format)
- Automatic cleanup of temporary files
- Comprehensive error handling and reporting
- Support for hidden files and directories
- Configurable remote paths and SSH ports
- Ignore file support (`.scpignore`)

## 🚀 Installation

### Prerequisites

- Python 3.6 or higher
- SSH access to your remote server
- SCP installed on your local machine (usually comes with SSH)

### Install from PyPI

```bash
pip install pydaffodil
```

### Verify Installation

```python
from pydaffodil import Daffodil
print("PyDaffodil installed successfully!")
```

## 🏃 Quick Start

Here's a simple example to get you started:

```python
from pydaffodil import Daffodil

# Initialize the deployment client
cli = Daffodil(
    remote_user="root",
    remote_host="your-server.com",
    remote_path="/var/www/myapp"
)

# Define deployment steps
steps = [
    {"step": "Build the project", "command": lambda: cli.run_command("npm run build")},
    {"step": "Transfer files", "command": lambda: cli.transfer_files("dist")},
    {"step": "Restart service", "command": lambda: cli.ssh_command("sudo systemctl restart myapp")}
]

# Execute deployment
cli.deploy(steps)
```

## 📚 Usage Examples

### Basic File Transfer

```python
from pydaffodil import Daffodil

cli = Daffodil(
    remote_user="deploy",
    remote_host="192.168.1.100",
    remote_path="/home/deploy/app"
)

# Transfer files (automatically archived and extracted)
cli.transfer_files("build", destination_path="/home/deploy/app/production")
```

### Using SSH Keys

```python
cli = Daffodil(
    remote_user="deploy",
    remote_host="example.com",
    ssh_key_path="~/.ssh/id_rsa",
    ssh_key_pass="your-passphrase"  # Optional, only if key is encrypted
)
```

### Custom Port and Path

```python
cli = Daffodil(
    remote_user="admin",
    remote_host="server.example.com",
    port=2222,  # Custom SSH port
    remote_path="/opt/myapplication"
)
```

### Complex Deployment Workflow

```python
from pydaffodil import Daffodil

cli = Daffodil(
    remote_user="root",
    remote_host="production.example.com",
    remote_path="/var/www/production"
)

steps = [
    {
        "step": "Build frontend",
        "command": lambda: cli.run_command("cd frontend && npm run build")
    },
    {
        "step": "Build backend",
        "command": lambda: cli.run_command("cd backend && npm run build")
    },
    {
        "step": "Stop services",
        "command": lambda: cli.ssh_command("sudo systemctl stop myapp")
    },
    {
        "step": "Backup current deployment",
        "command": lambda: cli.ssh_command("cp -r /var/www/production /var/www/backup/$(date +%Y%m%d_%H%M%S)")
    },
    {
        "step": "Transfer frontend",
        "command": lambda: cli.transfer_files("frontend/dist", "/var/www/production/frontend")
    },
    {
        "step": "Transfer backend",
        "command": lambda: cli.transfer_files("backend/dist", "/var/www/production/backend")
    },
    {
        "step": "Install dependencies",
        "command": lambda: cli.ssh_command("cd /var/www/production/backend && npm install --production")
    },
    {
        "step": "Start services",
        "command": lambda: cli.ssh_command("sudo systemctl start myapp")
    }
]

cli.deploy(steps)
```

## 📖 API Reference

### `Daffodil` Class

#### Constructor Parameters

- `remote_user` (str, required): Username for SSH connection
- `remote_host` (str, required): Hostname or IP address of the remote server
- `remote_path` (str, optional): Default remote directory path
- `port` (int, optional): SSH port number (default: 22)
- `ssh_key_path` (str, optional): Path to SSH private key file
- `ssh_key_pass` (str, optional): Passphrase for encrypted SSH keys
- `scp_ignore` (str, optional): Path to ignore file (default: ".scpignore")

#### Methods

##### `transfer_files(local_path, destination_path=None)`

Transfer files and directories to the remote server. Files are automatically archived before transfer and extracted on the remote server.

- `local_path` (str): Local directory or file path to transfer
- `destination_path` (str, optional): Remote destination path (defaults to `remote_path`)

##### `run_command(command)`

Execute a shell command on the local machine.

- `command` (str): Shell command to execute

##### `ssh_command(command)`

Execute a command on the remote server via SSH.

- `command` (str): Command to execute on remote server

##### `make_directory(directory_name)`

Create a directory on the remote server.

- `directory_name` (str): Name of the directory to create

##### `deploy(steps)`

Execute a series of deployment steps.

- `steps` (list): List of step dictionaries, each containing:
  - `step` (str): Description of the step
  - `command` (callable): Lambda function or callable to execute

## 🔧 Requirements

### System Requirements

- Python 3.6+
- SCP (usually included with SSH/OpenSSH)

### Python Dependencies

- `paramiko` >= 2.0.0 - SSH client library
- `tqdm` >= 4.60.0 - Progress bars
- `colorama` >= 0.4.0 - Cross-platform colored terminal output

## 🌍 Cross-Platform Support

PyDaffodil is fully cross-platform and has been tested on:

- **Windows** 10/11
- **macOS** (all recent versions)
- **Linux** (Ubuntu, Debian, CentOS, etc.)

The framework automatically handles platform-specific differences in:
- Archive creation and extraction
- File path handling
- SSH key detection
- Command execution

## 🔒 Security

PyDaffodil prioritizes security:

- Supports all major SSH key types (RSA, DSA, ECDSA, Ed25519)
- Encrypted key support with passphrase protection
- Secure password authentication (when keys aren't available)
- No storage of credentials in code
- Automatic cleanup of temporary files

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 Publishing to PyPI

To publish a new version to PyPI:

1. **Update version** in `setup.py`
2. **Install build tools**: `pip install build twine`
3. **Build package**: `python -m build`
4. **Upload**: `twine upload dist/*`

For testing, use TestPyPI:
```bash
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Mark Wayne Menorca**

- Email: marcuwynu23@gmail.com
- GitHub: [@marcuwynu23](https://github.com/marcuwynu23)

## 🙏 Acknowledgments

- Built with [Paramiko](https://www.paramiko.org/) for SSH functionality
- Progress bars powered by [tqdm](https://github.com/tqdm/tqdm)
- Cross-platform colors with [Colorama](https://github.com/tartley/colorama)

---

<div align="center">
  <p>Made with ❤️ for developers who love automation</p>
  <p>⭐ Star this repo if you find it useful!</p>
</div>
