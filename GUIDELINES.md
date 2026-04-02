# PyDaffodil Usage Guidelines

Complete guide to deploying with PyDaffodil: API usage, **`inventory.ini`**, **`.daffodil.yml`**, **`watch()`**, and troubleshooting. For developer setup see [DOCUMENTATION.md](./DOCUMENTATION.md).

## Table of contents

1. [Installation](#installation)
2. [Quick start (API)](#quick-start-api)
3. [Configuration](#configuration)
4. [Core operations](#core-operations)
5. [Multi-host (`inventory.ini`)](#multi-host-inventoryini)
6. [Watch (`watch()`)](#watch-watch)
7. [YAML CLI](#yaml-cli)
8. [Ignore file (`.scpignore`)](#ignore-file-scpignore)
9. [Best practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

## Installation

```bash
pip install pydaffodil
```

Requires Python ≥ 3.9 (see PyPI). SSH keys are typically loaded from standard locations or via `ssh_key_path=`.

## Quick start (API)

```python
from pydaffodil import Daffodil

d = Daffodil(
    remote_user="deploy",
    remote_host="203.0.113.10",
    remote_path="/var/www/app",
    port=22,
)

steps = [
    {"step": "Upload", "command": lambda: d.transfer_files("./dist", "/var/www/app")},
    {"step": "Reload", "command": lambda: d.ssh_command("systemctl reload nginx")},
]

d.deploy(steps)
```

## Configuration

### Constructor (single-host)

| Parameter | Description |
| --------- | ----------- |
| `remote_user` | SSH username |
| `remote_host` | Hostname or IP |
| `remote_path` | Default remote base path |
| `port` | SSH port (default 22) |
| `ssh_key_path` | Optional path to private key |
| `ssh_key_pass` | Optional key passphrase |
| `scp_ignore` | Ignore file path (default `.scpignore`) |

### Constructor (inventory)

| Parameter | Description |
| --------- | ----------- |
| `inventory` | Path to `inventory.ini` |
| `group` | Section name to deploy (e.g. `webservers`) |

When `inventory` is set, `group` is required; `remote_user`/`remote_host` are not used as the single target—hosts come from the file.

## Core operations

- **`run_command(cmd)`** — Local shell command.
- **`ssh_command(cmd)`** — Remote command over SSH.
- **`transfer_files(local_path, destination_path=None)`** — Archive, upload, extract remotely; respects `.scpignore`.
- **`make_directory(name)`** — Create remote directory.
- **`deploy(steps)`** — Run each step in order; inventory mode runs the full sequence per host.

## Multi-host (`inventory.ini`)

Ansible-style INI: sections in brackets, one host per line with `host=`, `user=`, optional `port=`.

```ini
[webservers]
app1 host=203.0.113.10 user=deploy port=22
app2 host=203.0.113.11 user=deploy
```

```python
d = Daffodil(inventory="./inventory.ini", group="webservers", remote_path="/var/www/app")
d.deploy(steps)
```

See `example/publish-multi.py` and `example/inventory.ini`.

## Watch (`watch()`)

Triggers redeploys when files change and/or Git state changes (commits, merges, tags).

```python
d.watch(
    paths=["./dist", "./src"],
    debounce=2000,
    repo_path=".",
    branches=["main"],
    tags=True,
    tag_pattern=r"^v\d+\.\d+\.\d+$",
    events=["commit", "merge", "tag"],
    interval=5000,
).deploy(steps)
```

Requires at least one of `paths` or `repo_path`. See `example/publish-watch.py`.

## YAML CLI

```bash
pydaffodil --config example/.daffodil.yml
pydaffodil --config example/.daffodil.yml --watch
```

- Config file **basename** must be exactly **`.daffodil.yml`**.
- **Host resolution order** (same family as JSDaffodil / GoDaffodil):
  1. Non-empty **`hosts`** in YAML
  2. **`inventoryFile`** + **`inventoryGroup`**
  3. Top-level **`remoteHost` / `remoteUser`** (or snake_case)

Example inventory snippet:

```yaml
inventoryFile: inventory.ini
inventoryGroup: webservers
```

## Ignore file (`.scpignore`)

Glob-like lines; paths matching patterns are excluded from packaged transfers. Place next to your project or set `scp_ignore=`.

## Best practices

- Verify `ssh user@host` before automating.
- Store secrets in environment variables or a secrets manager, not in repo YAML.
- Use **inventory** for production multi-host; keep **YAML `hosts`** for small staging lists.
- Match behavior with [JSDaffodil](https://github.com/marcuwynu23/jsdaffodil) / [GoDaffodil](https://github.com/marcuwynu23/godaffodil) when sharing `.daffodil.yml` across languages.

## Troubleshooting

| Issue | Checks |
| ----- | ------ |
| `Connection refused` / timeout | Firewall, `port`, correct IP, SSH daemon on host |
| Auth failures | Key path, `ssh_agent`, permissions on `~/.ssh` |
| Inventory empty / wrong group | Section name matches `group=`; lines include `host=` and `user=` |
| `watch()` never fires | `paths` or `repo_path` set; `repo_path` exists; `interval` / debounce not too aggressive |
| CLI “No hosts” | Define `hosts`, or inventory + group, or `remoteHost` + `remoteUser` |

## Additional resources

- [README.md](./README.md) — Sister projects table
- [DOCUMENTATION.md](./DOCUMENTATION.md) — Module layout and tests
- [CONTRIBUTING.md](./CONTRIBUTING.md) — How to contribute
