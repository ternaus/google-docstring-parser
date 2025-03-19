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

# Whether to check references for proper format
check_references = true

# List of filenames to exclude from checks
# These can be just filenames (e.g., "conftest.py") or paths ending with the filename
exclude_files = ["conftest.py", "__init__.py", "tests/fixtures/bad_docstrings.py"]

# Whether to enable verbose output
verbose = false
```

### Features

#### Parameter Type Checking

When `require_param_types = true`, the hook will check if all parameters in docstrings have their types specified. This helps ensure consistent documentation across your codebase.

#### Reference Checking

When `check_references = true`, the hook will validate the References section in docstrings for proper formatting. It checks for:

- Proper separator colon between description and source
- Proper dash usage (required for multiple references, not allowed for single reference)
- Empty descriptions or sources
- URL colons are handled correctly (colons in URLs like https:// are not confused with separator colons)

For a single reference:
```python
"""
References:
    Paper title: https://example.com/paper
"""
```

For multiple references:
```python
"""
References:
    - First paper: https://example.com/paper1
    - Second paper: https://example.com/paper2
"""
```

### Example Configuration

```toml
# pyproject.toml
[tool.docstring_checker]
paths = ["src", "tests"]
require_param_types = true
check_references = true
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

### Command Line Usage

You can also run the docstring checker directly:

```bash
python -m tools.check_docstrings path/to/file_or_directory --require-param-types --check-references
```

Command line options:
- `--require-param-types`: Require parameter types in docstrings
- `--check-references`: Check references for proper format
- `--no-check-references`: Skip reference checking
- `--exclude-files`: Comma-separated list of filenames to exclude
- `-v, --verbose`: Enable verbose output
