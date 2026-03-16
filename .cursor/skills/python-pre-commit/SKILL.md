---
name: python-pre-commit
description: Work with pre-commit hooks, fix pre-commit failures, add or update hooks. Use when pre-commit fails, adding pre-commit hooks, or debugging ruff/mypy/check-docstrings issues.
---

# Python Pre-commit (Project)

## Workflow

**Do not run ruff or flake8 directly.** Use:

```bash
pre-commit run --all-files
```

## Hooks (from .pre-commit-config.yaml)

| Hook | Config | Notes |
|------|--------|-------|
| ruff | pyproject.toml | Lint + format. `args: [--fix]` |
| ruff-format | pyproject.toml | Formatter |
| mypy | pyproject.toml | `files: ^(google_docstring_parser\|tests)/` |
| check-docstrings | local | `python -m tools.check_docstrings` |
| pyproject-fmt | - | Formats pyproject.toml |
| codespell | - | Spell check |
| pre-commit-hooks | - | AST, TOML, JSON, etc. |

## Lint rules

**Do not disable checks that force refactoring for better code** (e.g. C901 complexity). Fix the code instead.

## Config locations

- **Ruff**: `[tool.ruff]` in pyproject.toml (line-length 120, py310, pydocstyle google)
- **Mypy**: `[tool.mypy]` in pyproject.toml (strict: disallow_untyped_defs, etc.)
- **Docstrings**: `[tool.docstring_checker]` in pyproject.toml

## Fixing failures

1. Run `pre-commit run --all-files` to see all errors
2. Ruff: fix lint/format, often auto-fixable with `--fix`
3. Mypy: add types, fix annotations
4. check-docstrings: see google-docstring-format skill

## Add new hook

Edit `.pre-commit-config.yaml`, then:

```bash
pre-commit autoupdate   # optional: update revs
pre-commit run --all-files
```
