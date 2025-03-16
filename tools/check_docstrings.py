#!/usr/bin/env python
"""Check that docstrings in specified folders can be parsed.

This script scans Python files in specified directories and checks if their
docstrings can be parsed with the google_docstring_parser.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path
from typing import Any, NamedTuple

import tomli

from google_docstring_parser.google_docstring_parser import parse_google_docstring

# Default configuration
DEFAULT_CONFIG = {
    "paths": ["."],
    "require_param_types": False,
    "exclude_files": [],
    "verbose": False,
}


class DocstringContext(NamedTuple):
    """Context for docstring processing.

    Args:
        file_path (Path): Path to the file
        line_no (int): Line number
        name (str): Name of the function or class
        verbose (bool): Whether to print verbose output
        require_param_types (bool): Whether parameter types are required
    """

    file_path: Path
    line_no: int
    name: str
    verbose: bool
    require_param_types: bool = False


def load_pyproject_config() -> dict[str, Any]:
    """Load configuration from pyproject.toml if it exists.

    Returns:
        Dictionary with configuration values
    """
    config = DEFAULT_CONFIG.copy()

    # Look for pyproject.toml in the current directory
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.is_file():
        return config

    try:
        with pyproject_path.open("rb") as f:
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


def get_docstrings(file_path: Path) -> list[tuple[str, int, str | None, ast.AST | None]]:
    """Extract docstrings from a Python file.

    Args:
        file_path (Path): Path to the Python file

    Returns:
        List of tuples containing (function/class name, line number, docstring, node)
    """
    with file_path.open(encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []

    docstrings = []

    # Get module docstring
    if len(tree.body) > 0 and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant):
        docstrings.append(("module", 1, tree.body[0].value.value, None))

    # Get function and class docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            if docstring:
                docstrings.append((node.name, node.lineno, docstring, node))

    return docstrings


def check_param_types(docstring_dict: dict[str, Any], require_types: bool) -> list[str]:
    """Check if all parameters have types if required.

    Args:
        docstring_dict (dict[str, Any]): Parsed docstring dictionary
        require_types (bool): Whether parameter types are required

    Returns:
        List of error messages for parameters missing types or having invalid types
    """
    if not require_types or "Args" not in docstring_dict:
        return []

    errors = []
    for arg in docstring_dict["Args"]:
        if arg["type"] is None:
            errors.append(f"Parameter '{arg['name']}' is missing a type in docstring")
        elif "invalid type" in arg["type"].lower():
            errors.append(f"Parameter '{arg['name']}' has an invalid type in docstring: '{arg['type']}'")

    return errors


def validate_docstring(docstring: str) -> list[str]:
    """Perform additional validation on a docstring.

    Args:
        docstring (str): The docstring to validate

    Returns:
        List of validation error messages
    """
    errors = []

    # Check for unclosed parentheses in parameter types
    lines = docstring.split("\n")
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue

        # Check for parameter definitions with unclosed parentheses
        # Improved regex to better detect unclosed parentheses and brackets
        if param_match := re.match(
            r"^\s*(\w+)\s+\(([^)]*$|.*\[[^\]]*$)",
            stripped_line,
        ):
            errors.append(f"Unclosed parenthesis in parameter type: '{stripped_line}'")

        # Check for invalid type declarations
        param_match = re.match(r"^\s*(\w+)\s+\((invalid type)\)", stripped_line)
        if param_match:
            errors.append(f"Invalid type declaration: '{stripped_line}'")

    return errors


def _format_error(context: DocstringContext, error: str) -> str:
    """Format an error message consistently.

    Args:
        context (DocstringContext): Docstring context
        error (str): Error message

    Returns:
        str: Formatted error message
    """
    msg = f"{context.file_path}:{context.line_no}: {error} in '{context.name}'"
    if context.verbose:
        print(msg)
    return msg


def _process_docstring(context: DocstringContext, docstring: str) -> list[str]:
    """Process a single docstring.

    Args:
        context (DocstringContext): Docstring context
        docstring (str): The docstring to process

    Returns:
        list[str]: List of error messages
    """
    errors = []
    if not docstring:
        return errors

    # Validate docstring inline
    try:
        val_errors = validate_docstring(docstring)
        if val_errors:
            errors.extend(_format_error(context, err) for err in val_errors)
    except Exception as e:
        errors.append(_format_error(context, f"Error validating docstring: {e}"))
        return errors

    # Parse docstring inline
    try:
        parsed = parse_google_docstring(docstring)
    except Exception as e:
        errors.append(_format_error(context, f"Error parsing docstring: {e}"))
        return errors

    # Check parameter types (if required) inline
    if context.require_param_types:
        try:
            type_errors = check_param_types(parsed, context.require_param_types)
            errors.extend(_format_error(context, err) for err in type_errors)
        except Exception as e:
            errors.append(_format_error(context, f"Error checking parameter types: {e}"))

    return errors


def check_file(
    file_path: Path,
    require_param_types: bool = False,
    verbose: bool = False,
) -> list[str]:
    """Check docstrings in a file.

    Args:
        file_path (Path): Path to the Python file
        require_param_types (bool): Whether parameter types are required
        verbose (bool): Whether to print verbose output

    Returns:
        List of error messages
    """
    if verbose:
        print(f"Checking {file_path}")

    errors = []

    try:
        docstrings = get_docstrings(file_path)
    except Exception as e:
        error_msg = f"{file_path}: Error getting docstrings: {e!s}"
        errors.append(error_msg)
        if verbose:
            print(error_msg)
        return errors

    for name, line_no, docstring, _ in docstrings:
        context = DocstringContext(
            file_path=file_path,
            line_no=line_no,
            name=name,
            verbose=verbose,
            require_param_types=require_param_types,
        )
        errors.extend(_process_docstring(context, docstring))

    return errors


def scan_directory(
    directory: Path,
    exclude_files: list[str] | None = None,
    require_param_types: bool = False,
    verbose: bool = False,
) -> list[str]:
    """Scan a directory for Python files and check their docstrings.

    Args:
        directory (Path): Directory to scan
        exclude_files (list[str] | None): List of filenames to exclude
        require_param_types (bool): Whether parameter types are required
        verbose (bool): Whether to print verbose output

    Returns:
        List of error messages
    """
    if exclude_files is None:
        exclude_files = []

    errors = []
    for py_file in directory.glob("**/*.py"):
        # Check if the file should be excluded
        should_exclude = False
        for exclude_pattern in exclude_files:
            # Check if the filename matches exactly
            if py_file.name == exclude_pattern:
                should_exclude = True
                break
            # Check if the path ends with the pattern (for subdirectories)
            if str(py_file).endswith(f"/{exclude_pattern}"):
                should_exclude = True
                break

        if not should_exclude:
            errors.extend(check_file(py_file, require_param_types, verbose))
    return errors


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Check that docstrings in specified folders can be parsed.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Directories or files to scan for Python docstrings",
    )
    parser.add_argument(
        "--require-param-types",
        action="store_true",
        help="Require parameter types in docstrings",
    )
    parser.add_argument(
        "--exclude-files",
        help="Comma-separated list of filenames to exclude",
        default="",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def _get_config_values(args: argparse.Namespace, config: dict[str, Any]) -> tuple[list[str], bool, bool, list[str]]:
    """Get configuration values from command line args and config.

    Args:
        args (argparse.Namespace): Command line arguments
        config (dict[str, Any]): Configuration from pyproject.toml

    Returns:
        Tuple of (paths, require_param_types, verbose, exclude_files)
    """
    # Get paths
    paths = args.paths or config["paths"]

    # Get require_param_types
    require_param_types = args.require_param_types or config["require_param_types"]

    # Get verbose
    verbose = args.verbose or config["verbose"]

    # Get exclude_files
    exclude_files = []
    if args.exclude_files:
        exclude_files = [f.strip() for f in args.exclude_files.split(",") if f.strip()]

    # If no exclude_files specified on command line, use the ones from config
    if not exclude_files:
        exclude_files = config["exclude_files"]

    return paths, require_param_types, verbose, exclude_files


def _process_paths(
    paths: list[str],
    exclude_files: list[str],
    require_param_types: bool,
    verbose: bool,
) -> list[str]:
    """Process paths and collect errors.

    Args:
        paths (list[str]): List of paths to process
        exclude_files (list[str]): List of files to exclude
        require_param_types (bool): Whether to require parameter types
        verbose (bool): Whether to print verbose output

    Returns:
        List of error messages
    """
    all_errors = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            errors = scan_directory(path, exclude_files, require_param_types, verbose)
            all_errors.extend(errors)
        elif path.is_file() and path.suffix == ".py":
            errors = check_file(path, require_param_types, verbose)
            all_errors.extend(errors)
        else:
            print(f"Error: {path} is not a directory or Python file")
    return all_errors


def main():
    """Run the docstring checker."""
    # Load configuration from pyproject.toml
    config = load_pyproject_config()

    # Parse command line arguments
    args = _parse_args()

    # Get configuration values
    paths, require_param_types, verbose, exclude_files = _get_config_values(args, config)

    # Print configuration if verbose
    if verbose:
        print("Configuration:")
        print(f"  Paths: {paths}")
        print(f"  Require parameter types: {require_param_types}")
        print(f"  Exclude files: {exclude_files}")

    if all_errors := _process_paths(
        paths,
        exclude_files,
        require_param_types,
        verbose,
    ):
        for error in all_errors:
            print(error)
        print(f"\nFound {len(all_errors)} error{'s' if len(all_errors) != 1 else ''}")
        sys.exit(1)
    elif verbose:
        print("All docstrings parsed successfully!")

    sys.exit(0)


if __name__ == "__main__":
    main()
