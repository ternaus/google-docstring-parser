# Google Docstring Parser Tools

This directory contains tools for working with Google-style docstrings.

## Pre-commit Hook: Check Google Docstrings

A pre-commit hook that checks if Google-style docstrings in your codebase can be parsed correctly.

### Usage in Other Projects

To use this hook in another project, add the following to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/albumentations-team/google-docstring-parser
  rev: v0.0.1  # Use the latest version
  hooks:
    - id: check-google-docstrings
      args: ["your_package_directory", "other_directory_to_check"]  # Directories to check
```

### Installation

1. Install pre-commit: `pip install pre-commit`
2. Add the hook to your `.pre-commit-config.yaml` as shown above
3. Run `pre-commit install` to set up the git hook scripts

### Configuration

The hook accepts the following arguments:

- Positional arguments: List of directories to scan for Python files
- `-v`, `--verbose`: Enable verbose output

### Example

```yaml
- repo: https://github.com/albumentations-team/google-docstring-parser
  rev: v0.0.1
  hooks:
    - id: check-google-docstrings
      args: ["src", "tests"]
      # Optional: add verbose flag
      # args: ["src", "tests", "--verbose"]
```
