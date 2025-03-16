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
        file_path: Path to the file
        line_no: Line number
        name: Name of the function or class
        verbose: Whether to print verbose output
        require_param_types: Whether parameter types are required
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
        file_path: Path to the Python file

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


def check_param_types(docstring_dict: dict, require_types: bool) -> list[str]:
    """Check if all parameters have types if required.

    Args:
        docstring_dict: Parsed docstring dictionary
        require_types: Whether parameter types are required

    Returns:
        List of error messages for parameters missing types
    """
    if not require_types or "Args" not in docstring_dict:
        return []

    return [f"Parameter '{arg['name']}' is missing a type" for arg in docstring_dict["Args"] if arg["type"] is None]


def validate_docstring(docstring: str) -> list[str]:
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
        stripped_line = line.strip()
        if not stripped_line:
            continue

        # Check for parameter definitions with unclosed parentheses
        # Improved regex to better detect unclosed parentheses and brackets
        param_match = re.match(r"^\s*(\w+)\s+\(([^)]*$|.*\[[^\]]*$)", stripped_line)
        if param_match:
            errors.append(f"Unclosed parenthesis in parameter type: '{stripped_line}'")

    return errors


def _format_error(context: DocstringContext, error: str) -> str:
    """Format an error message.

    Args:
        context: Docstring context
        error: Error message

    Returns:
        Formatted error message
    """
    return f"{context.file_path}:{context.line_no}: {error} in '{context.name}'"


def _handle_validation_errors(
    context: DocstringContext,
    docstring: str,
) -> list[str]:
    """Handle validation errors for a docstring.

    Args:
        context: Docstring context
        docstring: The docstring to validate

    Returns:
        List of error messages
    """
    errors = []
    try:
        validation_errors = validate_docstring(docstring)
        for error in validation_errors:
            error_msg = _format_error(context, error)
            errors.append(error_msg)
            if context.verbose:
                print(error_msg)
    except Exception as e:
        error_msg = f"{context.file_path}:{context.line_no}: Error validating docstring for '{context.name}': {e!s}"
        errors.append(error_msg)
        if context.verbose:
            print(error_msg)

    return errors


def _handle_param_type_errors(
    context: DocstringContext,
    parsed: dict,
) -> list[str]:
    """Handle parameter type errors for a docstring.

    Args:
        context: Docstring context
        parsed: Parsed docstring

    Returns:
        List of error messages
    """
    errors = []
    if not context.require_param_types:
        return errors

    try:
        type_errors = check_param_types(parsed, context.require_param_types)
        for error in type_errors:
            error_msg = _format_error(context, error)
            errors.append(error_msg)
            if context.verbose:
                print(error_msg)
    except Exception as e:
        error_msg = f"{context.file_path}:{context.line_no}: Error checking parameter types for '{context.name}': {e!s}"
        errors.append(error_msg)
        if context.verbose:
            print(error_msg)

    return errors


def _process_docstring(
    context: DocstringContext,
    docstring: str,
) -> list[str]:
    """Process a single docstring.

    Args:
        context: Docstring context
        docstring: The docstring to process

    Returns:
        List of error messages
    """
    errors = []

    if not docstring:
        return errors

    # Perform additional validation
    errors.extend(_handle_validation_errors(context, docstring))

    # If validation failed with an exception, we'll have errors and should stop processing this docstring
    if errors and errors[-1].endswith(f"Error validating docstring for '{context.name}'"):
        return errors

    try:
        parsed = parse_google_docstring(docstring)
        errors.extend(_handle_param_type_errors(context, parsed))
    except Exception as e:
        error_msg = f"{context.file_path}:{context.line_no}: Error parsing docstring for '{context.name}': {e!s}"
        errors.append(error_msg)
        if context.verbose:
            print(error_msg)

    return errors


def check_file(
    file_path: Path,
    require_param_types: bool = False,
    verbose: bool = False,
) -> list[str]:
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
        args: Command line arguments
        config: Configuration from pyproject.toml

    Returns:
        Tuple of (paths, require_param_types, verbose, exclude_files)
    """
    # Get paths
    paths = args.paths if args.paths else config["paths"]

    # Get require_param_types
    require_param_types = args.require_param_types if args.require_param_types else config["require_param_types"]

    # Get verbose
    verbose = args.verbose if args.verbose else config["verbose"]

    # Get exclude_files
    exclude_files = []
    if args.exclude_files:
        exclude_files = [f.strip() for f in args.exclude_files.split(",") if f.strip()]
    elif not exclude_files:
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
        paths: List of paths to process
        exclude_files: List of files to exclude
        require_param_types: Whether to require parameter types
        verbose: Whether to print verbose output

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

    # Process paths and collect errors
    all_errors = _process_paths(paths, exclude_files, require_param_types, verbose)

    # Report results
    if all_errors:
        for error in all_errors:
            print(error)
        sys.exit(1)
    elif verbose:
        print("All docstrings parsed successfully!")

    sys.exit(0)


if __name__ == "__main__":
    main()
