# Contributing to PyDaffodil

Thank you for your interest in PyDaffodil. This guide matches the contribution workflow used across the [Daffodil](https://github.com/marcuwynu23) family (see also [JSDaffodil](https://github.com/marcuwynu23/jsdaffodil) and [GoDaffodil](https://github.com/marcuwynu23/godaffodil)).

## Documentation overview

| Document | Purpose |
| -------- | ------- |
| [GUIDELINES.md](./GUIDELINES.md) | End-user usage: API, `inventory.ini`, `.daffodil.yml` CLI, `watch()`, troubleshooting |
| [DOCUMENTATION.md](./DOCUMENTATION.md) | Developer guide: layout, architecture, tests, packaging |
| [README.md](./README.md) | Overview, install, quick links |
| [CHANGELOG.md](./CHANGELOG.md) | Release history |

## Getting started

1. Read [GUIDELINES.md](./GUIDELINES.md) for how the library is meant to be used.
2. Read [DOCUMENTATION.md](./DOCUMENTATION.md) for where code lives (`src/pydaffodil/`) and how tests are run.
3. Clone the repo and install a dev environment (see below).

## Development setup

The repo is configured for **[uv](https://docs.astral.sh/uv/)** (recommended):

```bash
git clone https://github.com/marcuwynu23/pydaffodil.git
cd pydaffodil
uv sync
```

Run tests:

```bash
uv run python -m unittest discover -s tests -v
```

Or, with `pip` / a virtualenv:

```bash
pip install -e ".[dev]"   # if extras are defined; otherwise pip install -e .
python -m unittest discover -s tests -v
```

CLI smoke (from repo root, optional):

```bash
uv run --directory example pydaffodil --config .daffodil.yml
```

## Contribution workflow

1. **Fork** the repository and create a branch: `feature/short-description` or `fix/issue-description`.
2. **Make changes** with tests for new behavior. Keep edits focused on the request.
3. **Run tests** before opening a PR: `uv run python -m unittest discover -s tests -v` (or equivalent).
4. **Update docs** if you change public API, CLI behavior, or `inventory.ini` / YAML semantics.
5. **Update [CHANGELOG.md](./CHANGELOG.md)** for user-visible changes (follow existing style).
6. **Open a Pull Request** with a clear description and, if applicable, links to issues.

## Commit messages

Prefer [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation only
- `test:` — Tests
- `chore:` — Tooling, CI, non-user-facing maintenance

## Code review

- Keep PRs reasonably small and focused.
- Match existing style (imports, naming, error messages).
- Do not commit secrets (SSH keys, passwords, tokens).

## Reporting issues

Include:

- Python version and OS
- PyDaffodil version (`pip show pydaffodil` or `uv pip show pydaffodil`)
- Minimal steps or a small script to reproduce
- Expected vs actual behavior

## Security

Report sensitive vulnerabilities privately to the maintainers (e.g. via GitHub Security Advisories if enabled). Do not open public issues for undisclosed security problems.

## Questions

- Check [GUIDELINES.md](./GUIDELINES.md) and [DOCUMENTATION.md](./DOCUMENTATION.md) first.
- Open a GitHub issue with the `question` label if something is still unclear.

Thank you for helping improve PyDaffodil.
