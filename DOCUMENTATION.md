# PyDaffodil — Developer Documentation

Documentation for contributors and maintainers. End-user usage is covered in [GUIDELINES.md](./GUIDELINES.md) and [README.md](./README.md).

## Table of contents

1. [Project overview](#project-overview)
2. [Repository layout](#repository-layout)
3. [Architecture](#architecture)
4. [Main package (`src/pydaffodil/`)](#main-package-srcpydaffodil)
5. [CLI (`cli.py`)](#cli-clipy)
6. [Features aligned with the Daffodil family](#features-aligned-with-the-daffodil-family)
7. [Development setup](#development-setup)
8. [Testing](#testing)
9. [Packaging and release](#packaging-and-release)
10. [Extension points](#extension-points)
11. [Runtime requirements](#runtime-requirements)
12. [Code style](#code-style)
13. [Additional resources](#additional-resources)
14. [Questions](#questions)

## Project overview

PyDaffodil is the **Python** implementation of the Daffodil deployment helpers. It uses **Paramiko** for SSH, archives local content for transfer, supports **`.scpignore`**, optional **`watch()`** (filesystem + Git polling), and **multi-host** deployments via Ansible-style **`inventory.ini`**.

Sister projects: [JSDaffodil](https://github.com/marcuwynu23/jsdaffodil) (Node.js), [GoDaffodil](https://github.com/marcuwynu23/godaffodil) (Go). Shared concepts: `.daffodil.yml` CLI schema, `inventoryFile` / `inventoryGroup`, host resolution order (`hosts` → inventory → single `remoteUser`/`remoteHost`).

## Repository layout

```
pydaffodil/
├── LICENSE
├── CONTRIBUTING.md
├── DOCUMENTATION.md      # This file
├── GUIDELINES.md
├── README.md
├── CHANGELOG.md
├── pyproject.toml
├── src/
│   └── pydaffodil/
│       ├── __init__.py
│       ├── __main__.py   # python -m pydaffodil
│       ├── core.py       # Daffodil class, deploy, watch, inventory
│       └── cli.py        # YAML-driven CLI (.daffodil.yml)
├── tests/
├── example/
└── .github/workflows/
```

## Architecture

```
Application / CLI
       │
       ▼
┌──────────────────┐
│  Daffodil        │  SSH connect, transfer, ssh_command, deploy(steps)
│  (core.py)       │  Optional inventory: per-host context switching
└────────┬─────────┘
         │
         ├── Paramiko SSHClient
         ├── Archive + transfer (see core implementation)
         └── _WatchSession (watch() → deploy loop)
```

- **Single-host mode**: `remote_user` + `remote_host` required; SSH is established in `__init__` (non-inventory path).
- **Inventory mode**: `inventory=` + `group=` loads hosts via `parse_inventory_ini_file()`; `deploy()` iterates hosts and switches context (`_switch_to_inventory_host`).

## Main package (`src/pydaffodil/`)

### `core.py`

- **`Daffodil`**: main class; deployment steps are dicts with `step` and `command` callables.
- **`parse_inventory_ini_file(path, group=None)`**: parses Ansible-style INI (`[section]`, lines like `name host=… user=… port=…`). Used by the class and by **`cli.py`** for YAML-driven runs.
- **`watch(...)`**: returns **`_WatchSession`**, which exposes `.deploy(steps)` and polls file mtime and/or Git state (branches, merges, tags).

### `__main__.py`

Entry for `python -m pydaffodil`; delegates to the CLI in `cli.py`.

## CLI (`cli.py`)

- **Invocation**: `pydaffodil --config path/to/.daffodil.yml` and optional **`--watch`**
- **Config path**: basename must be exactly **`.daffodil.yml`**
- Loads YAML with PyYAML; **`normalize_hosts`**: prefers inline **`hosts`**, then **`inventoryFile`** + **`inventoryGroup`**, then top-level remote user/host keys (camelCase or snake_case per `pick()`).
- Builds step callables for types **`local`**, **`ssh`**, **`transfer`** via `run_command`, `ssh_command`, `transfer_files`.

Aligned with **JSDaffodil** (`jsdaffodil --config`) and **GoDaffodil** (`godaffodil run --config`). End-user details: [GUIDELINES.md](./GUIDELINES.md).

## Features aligned with the Daffodil family

| Feature | Notes |
| ------- | ----- |
| `.daffodil.yml` | Same shape as JS/Go: `steps`, optional `hosts`, `watch`, `inventoryFile`, `inventoryGroup` |
| `inventory.ini` | Line-based host lines under `[group]`; see [GUIDELINES.md](./GUIDELINES.md) |
| Host precedence (CLI) | `hosts` array first, then inventory file, then default remote pair |
| `watch()` | Python API; YAML CLI uses `--watch` with a `watch:` block in YAML |

## Development setup

**Prerequisites:** Python ≥ 3.9 (see `pyproject.toml`), Git.

```bash
git clone https://github.com/marcuwynu23/pydaffodil.git
cd pydaffodil
uv sync
uv run python -m unittest discover -s tests -v
```

Develop against the example config:

```bash
cd example
uv run pydaffodil --config .daffodil.yml
```

## Testing

```bash
uv run python -m unittest discover -s tests -v
```

Tests live under **`tests/`** (e.g. `test_cli.py`). Add tests for CLI behavior, host resolution, or inventory parsing when changing those surfaces.

## Packaging and release

- Build backend: **Hatchling** (`pyproject.toml`).
- Publishing: typically **GitHub Actions** (`.github/workflows/publish.yml`); bump version in `pyproject.toml`, update **CHANGELOG.md**.

## Extension points

- New **YAML step types**: update `cli.py` (`build_steps`, validation in `run()`); keep parity with JSDaffodil/GoDaffodil when the feature is shared.
- New **inventory fields**: extend `parse_inventory_ini_file` and host dict handling in `core.py` / CLI normalization carefully.
- Avoid breaking changes to public `Daffodil` constructor arguments without a major version bump.

## Runtime requirements

- Python as specified in `pyproject.toml`
- Network path to the remote host over SSH; keys and permissions as in [GUIDELINES.md](./GUIDELINES.md)

## Code style

- Follow **PEP 8** and match existing patterns in `core.py` / `cli.py`.
- Prefer explicit errors (`ValueError`) with actionable messages for configuration mistakes.
- Do not log or print secrets.

## Additional resources

- [GUIDELINES.md](./GUIDELINES.md) — User-facing guide
- [CONTRIBUTING.md](./CONTRIBUTING.md) — PR workflow
- [README.md](./README.md) — Sister projects table and quick links

## Questions

Open an issue on GitHub or refer to [JSDaffodil](https://github.com/marcuwynu23/jsdaffodil) / [GoDaffodil](https://github.com/marcuwynu23/godaffodil) developer docs for cross-language behavior.
