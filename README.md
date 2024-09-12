# PyDaffodil

`pydaffodil` is a reusable deployment framework for Python, designed to simplify the process of deploying applications to remote vps servers.

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
