# Google Docstring Parser Tools

This directory contains tools for working with Google-style docstrings.

## Pre-commit Hook: Check Google Docstrings

A pre-commit hook that checks if Google-style docstrings in your codebase can be parsed correctly.

### Usage in Other Projects

To use this hook in another project, add the following to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/ternaus/google-docstring-parser
  rev: v0.0.1  # Use the latest version
  hooks:
    - id: check-google-docstrings
      additional_dependencies: ["tomli>=2.0.0"]  # Required for pyproject.toml configuration
```

### Installation

1. Install pre-commit: `pip install pre-commit`
2. Add the hook to your `.pre-commit-config.yaml` as shown above
3. Run `pre-commit install` to set up the git hook scripts

### Configuration

The hook is configured via pyproject.toml, following modern Python tooling conventions like those used by mypy, ruff, and other tools.

#### pyproject.toml Configuration

Add a `[tool.docstring_checker]` section to your pyproject.toml:

```toml
[tool.docstring_checker]
# List of directories or files to scan for docstrings
paths = ["src", "tests"]

# Whether to require parameter types in docstrings
require_param_types = true

# List of filenames to exclude from checks
# These can be just filenames (e.g., "conftest.py") or paths ending with the filename
exclude_files = ["conftest.py", "__init__.py", "tests/fixtures/bad_docstrings.py"]

# Whether to enable verbose output
verbose = false
```

This approach has several advantages:
- Keeps all your project configuration in one place
- Follows modern Python tooling conventions (like mypy, ruff, black, etc.)
- Makes it easier to maintain and update configuration
- Provides better IDE support and documentation

### Example Configuration

```toml
# pyproject.toml
[tool.docstring_checker]
paths = ["src", "tests"]
require_param_types = true
exclude_files = ["conftest.py", "__init__.py"]
verbose = false
```

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/ternaus/google-docstring-parser
  rev: v0.0.1
  hooks:
    - id: check-google-docstrings
      additional_dependencies: ["tomli>=2.0.0"]
```
