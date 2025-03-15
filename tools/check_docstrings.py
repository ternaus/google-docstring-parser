#!/usr/bin/env python
"""Check that docstrings in specified folders can be parsed.

This script scans Python files in specified directories and checks if their
docstrings can be parsed with the google_docstring_parser.
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import tomli

from google_docstring_parser import parse_google_docstring

# Default configuration
DEFAULT_CONFIG = {
    "paths": ["."],
    "require_param_types": False,
    "exclude_files": [],
    "verbose": False,
}


def load_pyproject_config() -> Dict[str, Any]:
    """Load configuration from pyproject.toml if it exists.

    Returns:
        Dictionary with configuration values
    """
    config = DEFAULT_CONFIG.copy()

    # Look for pyproject.toml in the current directory
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return config

    try:
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)

        # Check if our tool is configured
        tool_config = pyproject_data.get("tool", {}).get("docstring_checker", {})
        if not tool_config:
            return config

        # Update config with values from pyproject.toml
        if "paths" in tool_config:
            config["paths"] = tool_config["paths"]
        if "require_param_types" in tool_config:
            config["require_param_types"] = bool(tool_config["require_param_types"])
        if "exclude_files" in tool_config:
            config["exclude_files"] = tool_config["exclude_files"]
        if "verbose" in tool_config:
            config["verbose"] = bool(tool_config["verbose"])

    except Exception as e:
        print(f"Warning: Failed to load configuration from pyproject.toml: {e}")

    return config


def get_docstrings(file_path: str) -> List[Tuple[str, int, Optional[str]]]:
    """Extract docstrings from a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        List of tuples containing (function/class name, line number, docstring)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []

    docstrings = []

    # Get module docstring
    if (
        len(tree.body) > 0
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Str)
    ):
        docstrings.append(("module", 1, tree.body[0].value.s))

    # Get function and class docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            if docstring:
                docstrings.append((node.name, node.lineno, docstring))

    return docstrings


def check_param_types(docstring_dict: dict, require_types: bool) -> List[str]:
    """Check if all parameters have types if required.

    Args:
        docstring_dict: Parsed docstring dictionary
        require_types: Whether parameter types are required

    Returns:
        List of error messages for parameters missing types
    """
    if not require_types or "args" not in docstring_dict:
        return []

    errors = []
    for arg in docstring_dict["args"]:
        if arg["type"] is None:
            errors.append(f"Parameter '{arg['name']}' is missing a type")

    return errors


def validate_docstring(docstring: str) -> List[str]:
    """Perform additional validation on a docstring.

    Args:
        docstring: The docstring to validate

    Returns:
        List of validation error messages
    """
    errors = []

    # Check for unclosed parentheses in parameter types
    lines = docstring.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for parameter definitions with unclosed parentheses
        param_match = re.match(r"^\s*(\w+)\s+\(([^)]*$)", line)
        if param_match:
            errors.append(f"Unclosed parenthesis in parameter type: '{line}'")

        # Check for malformed section headers
        section_match = re.match(r"^([A-Z][a-zA-Z0-9]+):\s*$", line)
        if section_match and section_match.group(1) not in [
            "Args", "Returns", "Raises", "Yields", "Example", "Examples",
            "Note", "Notes", "Warning", "Warnings", "See", "References",
            "Attributes"
        ]:
            errors.append(f"Unknown section header: '{section_match.group(1)}'")

    return errors


def check_file(file_path: str, require_param_types: bool = False, verbose: bool = False) -> List[str]:
    """Check docstrings in a file.

    Args:
        file_path: Path to the Python file
        require_param_types: Whether parameter types are required
        verbose: Whether to print verbose output

    Returns:
        List of error messages
    """
    if verbose:
        print(f"Checking {file_path}")

    errors = []
    docstrings = get_docstrings(file_path)

    for name, line_no, docstring in docstrings:
        if not docstring:
            continue

        # Perform additional validation
        validation_errors = validate_docstring(docstring)
        for error in validation_errors:
            error_msg = f"{file_path}:{line_no}: {error} in '{name}'"
            errors.append(error_msg)
            if verbose:
                print(error_msg)

        try:
            parsed = parse_google_docstring(docstring)

            # Check for missing parameter types if required
            type_errors = check_param_types(parsed, require_param_types)
            for error in type_errors:
                error_msg = f"{file_path}:{line_no}: {error} in '{name}'"
                errors.append(error_msg)
                if verbose:
                    print(error_msg)

        except Exception as e:
            error_msg = f"{file_path}:{line_no}: Error parsing docstring for '{name}': {str(e)}"
            errors.append(error_msg)
            if verbose:
                print(error_msg)

    return errors


def scan_directory(directory: str, exclude_files: List[str] = None, require_param_types: bool = False, verbose: bool = False) -> List[str]:
    """Scan a directory for Python files and check their docstrings.

    Args:
        directory: Directory to scan
        exclude_files: List of filenames to exclude
        require_param_types: Whether parameter types are required
        verbose: Whether to print verbose output

    Returns:
        List of error messages
    """
    if exclude_files is None:
        exclude_files = []

    errors = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)

                # Check if the file should be excluded
                should_exclude = False
                for exclude_pattern in exclude_files:
                    # Check if the filename matches exactly
                    if file == exclude_pattern:
                        should_exclude = True
                        break
                    # Check if the path ends with the pattern (for subdirectories)
                    if file_path.endswith(os.path.sep + exclude_pattern):
                        should_exclude = True
                        break

                if not should_exclude:
                    errors.extend(check_file(file_path, require_param_types, verbose))
    return errors


def get_env_var_as_bool(var_name: str, default: bool = False) -> bool:
    """Get an environment variable as a boolean.

    Args:
        var_name: Name of the environment variable
        default: Default value if the environment variable is not set

    Returns:
        Boolean value of the environment variable
    """
    value = os.environ.get(var_name)
    if value is None:
        return default
    return value.lower() in ("yes", "true", "t", "1")


def get_env_var_as_list(var_name: str, default: List[str] = None, separator: str = ",") -> List[str]:
    """Get an environment variable as a list.

    Args:
        var_name: Name of the environment variable
        default: Default value if the environment variable is not set
        separator: Separator to split the environment variable value

    Returns:
        List of values from the environment variable
    """
    if default is None:
        default = []
    value = os.environ.get(var_name)
    if not value:
        return default
    return [item.strip() for item in value.split(separator) if item.strip()]


def main():
    """Run the docstring checker."""
    # Load configuration from pyproject.toml
    config = load_pyproject_config()

    parser = argparse.ArgumentParser(
        description="Check that docstrings in specified folders can be parsed."
    )
    parser.add_argument(
        "paths", nargs="*", help="Directories or files to scan for Python docstrings"
    )
    parser.add_argument(
        "--require-param-types",
        action="store_true",
        help="Require parameter types in docstrings"
    )
    parser.add_argument(
        "--exclude-files",
        help="Comma-separated list of filenames to exclude",
        default=""
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Priority: Command line > Environment variables > pyproject.toml > Defaults

    # Get paths
    paths = args.paths
    if not paths:
        # Get paths from environment variable
        env_paths = get_env_var_as_list("DOCSTRING_CHECK_PATHS")
        if env_paths:
            paths = env_paths
        else:
            # Use paths from pyproject.toml
            paths = config["paths"]

    # Get require_param_types
    require_param_types = args.require_param_types
    if not require_param_types:
        require_param_types = get_env_var_as_bool("DOCSTRING_CHECK_REQUIRE_PARAM_TYPES")
        if not require_param_types:
            require_param_types = config["require_param_types"]

    # Get verbose
    verbose = args.verbose
    if not verbose:
        verbose = get_env_var_as_bool("DOCSTRING_CHECK_VERBOSE")
        if not verbose:
            verbose = config["verbose"]

    # Get exclude_files
    exclude_files = []
    if args.exclude_files:
        exclude_files = [f.strip() for f in args.exclude_files.split(",") if f.strip()]

    # Add files from environment variable
    env_exclude_files = get_env_var_as_list("DOCSTRING_CHECK_EXCLUDE_FILES")
    if env_exclude_files:
        exclude_files.extend(env_exclude_files)

    # Add files from pyproject.toml if no files specified yet
    if not exclude_files:
        exclude_files = config["exclude_files"]

    all_errors = []
    for path in paths:
        if os.path.isdir(path):
            errors = scan_directory(path, exclude_files, require_param_types, verbose)
            all_errors.extend(errors)
        elif os.path.isfile(path) and path.endswith(".py"):
            errors = check_file(path, require_param_types, verbose)
            all_errors.extend(errors)
        else:
            print(f"Error: {path} is not a directory or Python file")

    if all_errors:
        for error in all_errors:
            print(error)
        sys.exit(1)
    else:
        if verbose:
            print("All docstrings parsed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
