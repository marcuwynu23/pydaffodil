<div align="center">
  <h1>PyDaffodil</h1>
  <p><strong>Cross-Platform Deployment Automation Framework for Python</strong></p>
  <p>
    <img src="https://img.shields.io/pypi/v/pydaffodil?color=blue&label=PyPI" alt="PyPI version"/>
    <img src="https://img.shields.io/pypi/pyversions/pydaffodil?color=green" alt="Python versions"/>
    <img src="https://img.shields.io/pypi/dm/pydaffodil?color=orange" alt="PyPI downloads"/>
    <img src="https://img.shields.io/github/stars/marcuwynu23/pydaffodil.svg" alt="Stars"/>
    <img src="https://img.shields.io/github/license/marcuwynu23/pydaffodil.svg" alt="License"/>
  </p>
</div>

---

## Overview

**PyDaffodil** is the **Python** implementation in the Daffodil family. It provides remote deployment over SSH with a step-oriented API, archive-based transfer, optional **`watch()`** triggers, and multi-host **`inventory.ini`** support—the same concepts as [JSDaffodil](https://www.npmjs.com/package/@marcuwynu23/jsdaffodil) (Node.js) and [GoDaffodil](https://github.com/marcuwynu23/godaffodil) (Go). See **[Sister projects](#sister-projects)** for links and CLI equivalents.

### Key Features

- **Archive-Based File Transfer** — Packages local paths, transfers efficiently, and extracts on the remote host
- **Cross-Platform Support** — Runs on Windows, Linux, and macOS
- **SSH via Paramiko** — Key-based authentication (RSA, ECDSA, Ed25519, and others supported by Paramiko)
- **Step-by-Step Execution** — Chain deployment steps with readable progress output
- **Ignore Pattern Support** — `.scpignore` (or custom path) to exclude paths from transfers
- **Colored Terminal Output** — Clear logs via Colorama
- **Progress Feedback** — Transfer progress with tqdm
- **Watch-Based Workflows (`watch()`)** — Trigger deploys on file changes and/or Git activity (commits, merges, tags)
- **Multi-Host Deployments** — Same steps across multiple servers using `inventory.ini` groups

---

## Sister projects

The **Daffodil** line shares the same ideas: SSH, archive transfer, `.scpignore`, `watch()` (files + Git), Ansible-style **`inventory.ini`**, and a shared **`.daffodil.yml`** schema for the official CLIs.

| Project | Language | Install | YAML CLI |
|---------|----------|---------|----------|
| **JSDaffodil** | Node.js | [`@marcuwynu23/jsdaffodil`](https://www.npmjs.com/package/@marcuwynu23/jsdaffodil) · [source](https://github.com/marcuwynu23/jsdaffodil) | `jsdaffodil --config .daffodil.yml` |
| **PyDaffodil** (this repo) | Python | [`pydaffodil`](https://pypi.org/project/pydaffodil/) · [source](https://github.com/marcuwynu23/pydaffodil) | `pydaffodil --config .daffodil.yml` |
| **GoDaffodil** | Go | [module](https://github.com/marcuwynu23/godaffodil) | `godaffodil run --config .daffodil.yml` |

Use **`--watch`** with each CLI when your YAML defines a `watch:` block (Go uses `godaffodil run … --watch`).

---

## Documentation

| Resource | Description |
| -------- | ----------- |
| [GUIDELINES.md](./GUIDELINES.md) | Usage: API, `inventory.ini`, `.daffodil.yml` CLI, `watch()`, troubleshooting |
| [DOCUMENTATION.md](./DOCUMENTATION.md) | Developers: `src/pydaffodil` layout, architecture, tests, packaging |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | Contribution workflow and PR expectations |
| [LICENSE](./LICENSE) | MIT License |

Aligned with [JSDaffodil](https://github.com/marcuwynu23/jsdaffodil) (`GUIDELINES.md`, `DOCUMENTATION.md`, `CONTRIBUTING.md`).

---

## Documentation and Examples

For hands-on usage, see the **`example/`** directory:

- `example/publish.py` — Basic scripted deployment
- `example/publish-multi.py` — Multi-host deployment with `inventory.ini`
- `example/publish-watch.py` — File and Git–triggered deploys with `watch()`
- `example/.daffodil.yml` — Reference schema for the YAML CLI

---

## Installation

```bash
pip install pydaffodil
```

Requires a supported Python 3.x (see PyPI classifiers) and network access to the remote host over SSH.

---

## Quick Start

```python
from pydaffodil import Daffodil

deployer = Daffodil(
    remote_user="deployer",
    remote_host="231.142.34.222",
    remote_path="/var/www/myapp",
    port=22,  # optional; default 22
)

steps = [
    {
        "step": "Transfer application files",
        "command": lambda: deployer.transfer_files("./dist", "/var/www/myapp"),
    },
    {
        "step": "Install dependencies",
        "command": lambda: deployer.ssh_command(
            "cd /var/www/myapp && npm install --production=false"
        ),
    },
    {
        "step": "Restart application",
        "command": lambda: deployer.ssh_command("pm2 restart myapp"),
    },
]

deployer.deploy(steps)
```

---

## API Reference

### Constructor

```python
Daffodil(
    remote_user=None,
    remote_host=None,
    remote_path=None,
    port=22,
    ssh_key_path=None,
    ssh_key_pass=None,
    scp_ignore=".scpignore",
    inventory=None,   # path to inventory.ini (multi-host mode)
    group=None,       # inventory group name (required if inventory is set)
)
```

In **single-host** mode, `remote_user` and `remote_host` are required. In **inventory** mode, hosts are loaded from `inventory.ini` and `group` must identify the section to use.

### Methods

#### `transfer_files(local_path, destination_path=None)`

Transfers a local file or directory to the remote server using an archive step, then extracts on the remote side. Honors `.scpignore` patterns.

#### `run_command(command)`

Runs a shell command on the **local** machine.

#### `ssh_command(command)`

Runs a command on the **remote** server over the active SSH session.

#### `make_directory(directory_name)`

Creates a directory on the remote server (under the configured remote context).

#### `deploy(steps)`

Runs deployment **steps** in order. Each step is a `dict` with:

- `step` — Human-readable label
- `command` — Callable (typically a `lambda`) returning the operation result

In **inventory** mode, the same steps are executed **sequentially per host**.

#### `watch(...)`

Returns a watch session with a `.deploy(steps)` method. Configure file paths, Git repo path, branches, tags, events, debounce, and polling interval.

```python
deployer.watch(
    paths=["./dist", "./src"],
    debounce=2000,          # ms between eligible deploys after a trigger
    repo_path=".",
    branches=["main", "staging"],
    tags=True,
    tag_pattern=r"^v\d+\.\d+\.\d+$",  # regex string; optional
    events=["commit", "merge", "tag"],
    interval=5000,          # poll interval in ms
).deploy(steps)
```

---

## Advanced Topics

### Archive-Based Transfer

PyDaffodil builds an archive of the selected local content, transfers it, and extracts it remotely. This reduces round-trips and works well for larger trees and slower links.

### Ignore Patterns (`.scpignore`)

Place a `.scpignore` in your project (or point `scp_ignore` at another file). Patterns exclude matching paths from transfer, similar in spirit to `.gitignore`-style workflows.

### SSH Keys

Provide `ssh_key_path` (and `ssh_key_pass` if the key is encrypted), or rely on Paramiko’s default key discovery where applicable.

---

## Best Practices

### SSH Access

Ensure key-based login works before automating:

```bash
ssh-keygen -t ed25519 -C "you@example.com"
ssh-copy-id deployer@your-server
ssh deployer@your-server
```

### Error Handling

Wrap deploy scripts in `try` / `except` and exit with a non-zero status in CI.

### Secrets

Prefer environment variables or a secrets manager for hosts, users, and keys—not hard-coded credentials in source control.

### Conditional Steps

Build the `steps` list dynamically (e.g. only run migrations in production) using ordinary Python control flow.

---

## Configuration Options

| Option          | Type    | Default         | Description |
| --------------- | ------- | --------------- | ----------- |
| `remote_user`   | `str`   | —               | SSH username (single-host mode) |
| `remote_host`   | `str`   | —               | Hostname or IP (single-host mode) |
| `remote_path`   | `str`   | auto / `.`      | Default remote base path |
| `port`          | `int`   | `22`            | SSH port |
| `ssh_key_path`  | `str`   | `None`          | Path to private key |
| `ssh_key_pass`  | `str`   | `None`          | Key passphrase, if needed |
| `scp_ignore`    | `str`   | `".scpignore"` | Ignore file path |
| `inventory`     | `str`   | `None`          | Path to `inventory.ini` (multi-host) |
| `group`         | `str`   | `None`          | Inventory group name (e.g. `webservers`) |

---

## Watch-Based CI/CD

Use `watch()` to run the same `deploy(steps)` pipeline when files change or Git state updates. See `example/` for patterns; combine `paths` with `repo_path` for file + Git triggers.

---

## Multi-Host Deployments with `inventory.ini`

Use an Ansible-style INI file to target a group of hosts with one script.

### Example `inventory.ini`

```ini
[webservers]
server1 host=231.142.34.222 user=deployer port=22
server2 host=231.142.34.223 user=deployer
server3 host=231.142.34.224 user=ubuntu port=2200
```

### Programmatic usage

```python
from pydaffodil import Daffodil

deployer = Daffodil(
    inventory="./inventory.ini",
    group="webservers",
    remote_path="/var/www/myapp",
)

deployer.deploy(steps)
```

See `example/publish-multi.py` and `example/inventory.ini` for a complete layout.

---

## Requirements

- **Python** 3.x (see [PyPI](https://pypi.org/project/pydaffodil/) for supported versions)
- **SSH** connectivity to the remote host
- **Dependencies** (installed with the package): `paramiko`, `tqdm`, `colorama`

---

## YAML CLI Deployment

PyDaffodil includes a CLI that reads `.daffodil.yml`:

```bash
pydaffodil --config example/.daffodil.yml
pydaffodil --config example/.daffodil.yml --watch
```

The config filename must be exactly **`.daffodil.yml`**. The same schema works with **JSDaffodil** and **GoDaffodil**—see **[Sister projects](#sister-projects)**.

### Host resolution (CLI)

Hosts are resolved in this order:

1. Inline **`hosts`** in the YAML file (if present and non-empty)
2. **`inventoryFile`** + **`inventoryGroup`** (Ansible-style `inventory.ini`)
3. Top-level **`remoteHost` / `remoteUser`** (or snake_case equivalents) for a single default host

Optional inventory reference:

```yaml
inventoryFile: inventory.ini
inventoryGroup: webservers
```

---

## Contributing

See **[CONTRIBUTING.md](./CONTRIBUTING.md)** for workflow, commits, and PR expectations (aligned with [JSDaffodil](https://github.com/marcuwynu23/jsdaffodil)). Short version: open an issue for large changes, submit focused PRs with tests and doc updates.

The library code lives under `src/pydaffodil/`.

### Local setup with uv

From the repository root:

```bash
uv sync
```

That creates `.venv/`, installs the project in editable mode, and pulls dev dependencies (build tools, and so on). Use `uv run …` so commands use that environment without activating the venv manually.

### CLI in development

Run the CLI through uv so it uses the local package:

```bash
uv run pydaffodil
```

Other equivalent entry points:

```bash
uv run python -m pydaffodil
uv run python -m pydaffodil.cli
```

The CLI looks for a config file named **`.daffodil.yml`** in the current working directory. To try the sample config under `example/`:

```bash
uv run --directory example pydaffodil
```

Or:

```bash
cd example
uv run pydaffodil
```

(Add `--watch` for watch mode when your YAML defines it.)

### Tests

From the repository root:

```bash
uv run python -m unittest discover -s tests -v
```

---

## License

[MIT License](./LICENSE)

---

## Acknowledgments

- SSH: [Paramiko](https://www.paramiko.org/)
- Progress: [tqdm](https://github.com/tqdm/tqdm)
- Terminal colors: [Colorama](https://github.com/tartley/colorama)

Part of the **Daffodil** family with [JSDaffodil](https://www.npmjs.com/package/@marcuwynu23/jsdaffodil) and [GoDaffodil](https://github.com/marcuwynu23/godaffodil)—see **[Sister projects](#sister-projects)**.

---

<div align="center">
  <p>Made with care by <a href="https://github.com/marcuwynu23">Mark Wayne B. Menorca</a></p>
</div>
