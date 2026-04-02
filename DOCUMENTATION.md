# PyDaffodil — Developer Documentation

Documentation for contributors and maintainers. End-user usage is covered in [GUIDELINES.md](./GUIDELINES.md) and [README.md](./README.md).

## Table of contents

1. [Project overview](#project-overview)
2. [Repository layout](#repository-layout)
3. [Architecture](#architecture)
4. [Core modules](#core-modules)
5. [Features aligned with the Daffodil family](#features-aligned-with-the-daffodil-family)
6. [Development setup](#development-setup)
7. [Testing](#testing)
8. [Packaging and release](#packaging-and-release)
9. [Extension points](#extension-points)
10. [Code style](#code-style)

## Project overview

PyDaffodil is the **Python** implementation of the Daffodil deployment helpers. It uses **Paramiko** for SSH, archives local content for transfer, supports **`.scpignore`**, optional **`watch()`** (filesystem + Git polling), and **multi-host** deployments via Ansible-style **`inventory.ini`**.

Sister projects: [JSDaffodil](https://github.com/marcuwynu23/jsdaffodil) (Node.js), [GoDaffodil](https://github.com/marcuwynu23/godaffodil) (Go). Shared concepts: `.daffodil.yml` CLI schema, `inventoryFile` / `inventoryGroup`, host resolution order (`hosts` → inventory → single `remoteUser`/`remoteHost`).

## Repository layout

```
pydaffodil/
├── LICENSE
├── CONTRIBUTING.md
├── DOCUMENTATION.md      # This file
├── GUIDELINES.md         # Usage guide
├── README.md
├── CHANGELOG.md
├── pyproject.toml        # Hatchling build, metadata, optional uv lock
├── src/
│   └── pydaffodil/
│       ├── __init__.py
│       ├── __main__.py   # python -m pydaffodil
│       ├── core.py       # Daffodil class, deploy, watch, inventory
│       └── cli.py        # YAML-driven CLI (.daffodil.yml)
├── tests/                # unittest suite (e.g. test_cli.py)
├── example/              # Runnable samples and reference .daffodil.yml
└── .github/workflows/    # CI / publish
```

## Architecture

High-level flow:

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
         ├── Archive + SCP-style transfer (see core implementation)
         └── _WatchSession (watch() → deploy loop)
```

- **Single-host mode**: `remote_user` + `remote_host` required; SSH is established in `__init__` (non-inventory path).
- **Inventory mode**: `inventory=` + `group=` loads hosts via `parse_inventory_ini_file()`; `deploy()` iterates hosts and switches context (`_switch_to_inventory_host`).

## Core modules

### `core.py`

- **`Daffodil`**: main class; deployment steps are dicts with `step` and `command` callables.
- **`parse_inventory_ini_file(path, group=None)`**: parses Ansible-style INI (`[section]`, lines like `name host=… user=… port=…`). Used by the class and by **`cli.py`** for YAML-driven runs.
- **`watch(...)`**: returns **`_WatchSession`**, which exposes `.deploy(steps)` and polls file mtime and/or Git state (branches, merges, tags).

### `cli.py`

- Loads **`.daffodil.yml`** with PyYAML.
- **`normalize_hosts`**: prefers inline **`hosts`**, then **`inventoryFile`** + **`inventoryGroup`**, then top-level remote user/host keys (camelCase or snake_case per `pick()`).
- Builds step callables that invoke `Daffodil.run_command`, `ssh_command`, `transfer_files` for types `local`, `ssh`, `transfer`.

### `__main__.py`

Entry for `python -m pydaffodil`; delegates to the CLI parser in `cli.py`.

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
uv sync
uv run python -m unittest discover -s tests -v
```

Develop against the example config:

```bash
cd example
uv run pydaffodil --config .daffodil.yml
```

## Testing

- Tests live under **`tests/`** (e.g. `test_cli.py`).
- Run: `uv run python -m unittest discover -s tests -v`
- Add tests for new CLI behavior, host resolution, or inventory parsing edge cases.

## Packaging and release

- Build backend: **Hatchling** (`pyproject.toml`).
- Publishing is typically automated via **GitHub Actions** (see `.github/workflows/publish.yml`); maintainers bump version in `pyproject.toml` and tag releases per project practice.
- **CHANGELOG.md** should record user-visible changes.

## Extension points

- New **step types** in the YAML CLI require updates in `cli.py` (`build_steps`, validation in `run()`).
- New **inventory fields** may require extending `parse_inventory_ini_file` and host dict handling in `core.py` and CLI normalization.
- Avoid breaking changes to public `Daffodil` constructor arguments without a major version bump.

## Code style

- Follow **PEP 8** and match existing patterns in `core.py` / `cli.py`.
- Prefer explicit errors (`ValueError`) with actionable messages for configuration mistakes.
- Do not log or print secrets.

## Additional resources

- [GUIDELINES.md](./GUIDELINES.md) — User-facing guide
- [CONTRIBUTING.md](./CONTRIBUTING.md) — PR workflow
- [README.md](./README.md) — Sister projects table and quick links

## Questions

Open an issue on GitHub or refer to sister projects’ docs for cross-language behavior.
