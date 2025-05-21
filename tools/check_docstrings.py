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

from google_docstring_parser.google_docstring_parser import (
    parse_google_docstring,
)

# Default configuration
DEFAULT_CONFIG = {
    "paths": [],  # Empty by default, so no directories are scanned unless explicitly specified
    "require_param_types": False,
    "check_references": True,
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
        check_references (bool): Whether to check references for errors

    Returns:
        DocstringContext: A named tuple containing docstring processing context
    """

    file_path: Path
    line_no: int
    name: str
    verbose: bool
    require_param_types: bool = False
    check_references: bool = True


def load_pyproject_config() -> dict[str, Any]:
    """Load configuration from pyproject.toml if it exists.

    Returns:
        dict[str, Any]: Dictionary with configuration values
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
        if "check_references" in tool_config:
            config["check_references"] = bool(tool_config["check_references"])
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
        list[tuple[str, int, str | None, ast.AST | None]]: List of tuples containing:
            - str: function/class name
            - int: line number
            - str | None: docstring
            - ast.AST | None: AST node
    """
    with file_path.open(encoding="utf-8") as f:
        content = f.read()

    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")
        return []

    docstrings = []

    # Get function and class docstrings only
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
        list[str]: List of error messages for parameters missing types or having invalid types
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


def _check_reference_fields(reference: dict[str, Any], index: int) -> list[str]:
    """Check a single reference for missing or empty fields.

    Args:
        reference (dict[str, Any]): The reference to check
        index (int): The index of the reference (for error messages)

    Returns:
        list[str]: List of error messages
    """
    errors = []

    # Check required fields
    if "description" not in reference:
        errors.append(f"Reference #{index + 1} is missing a description")
    elif not reference["description"]:
        errors.append(f"Reference #{index + 1} has an empty description")

    if "source" not in reference:
        errors.append(f"Reference #{index + 1} is missing a source")
    elif not reference["source"]:
        errors.append(f"Reference #{index + 1} has an empty source")

    return errors


def check_references(docstring_dict: dict[str, Any]) -> list[str]:
    """Check references section for common errors.

    Args:
        docstring_dict (dict[str, Any]): Parsed docstring dictionary

    Returns:
        list[str]: List of error messages for problematic references
    """
    errors = []

    # Check for References section
    for ref_section in ["References", "Reference"]:
        if ref_section in docstring_dict:
            references = docstring_dict[ref_section]

            # Check if references is a list
            if not isinstance(references, list):
                errors.append(f"{ref_section} section is not properly formatted")
                return errors

            # If no references, that's fine
            if not references:
                return errors

            # Check each reference
            for i, ref in enumerate(references):
                if not isinstance(ref, dict):
                    errors.append(f"Reference #{i + 1} is not properly formatted")
                    continue

                errors.extend(_check_reference_fields(ref, i))

            # We've processed one references section, no need to check the other
            break

    return errors


def validate_docstring(docstring: str) -> list[str]:
    """Perform additional validation on a docstring.

    Args:
        docstring (str): The docstring to validate

    Returns:
        list[str]: List of validation error messages
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


def check_returns_section_name(docstring: str) -> list[str]:
    """Check for incorrect Returns section names.

    Args:
        docstring (str): The docstring to check

    Returns:
        list[str]: List of error messages for incorrect Returns section names
    """
    errors = []
    lines = docstring.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped in ["return:", "Return:", "returns:"]:
            errors.append(f"Invalid section name '{stripped}', use 'Returns:' instead")
    return errors


def check_returns_type(docstring_dict: dict[str, Any]) -> list[str]:
    """Check Returns type in a docstring."""
    errors = []
    if returns := docstring_dict.get("Returns"):
        # Special case: Returns section just contains "None"
        if isinstance(returns, str) and returns.strip() == "None":
            return errors

        if not isinstance(returns, dict):
            errors.append("Returns section must be either 'None' or have a type annotation")
            return errors

        if not returns.get("type"):
            errors.append("Returns section is missing type annotation")

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


def safe_execute(
    context: DocstringContext,
    func: callable,
    *args,  # noqa: ANN002
    error_prefix: str,
    format_results: bool = True,
) -> tuple[list[str], Any]:
    """Safely execute a function and handle errors consistently.

    Args:
        context (DocstringContext): Context for error formatting
        func (callable): Function to execute
        *args (Any): Arguments to pass to the function
        error_prefix (str): Prefix for error messages
        format_results (bool): Whether to format results as errors

    Returns:
        tuple[list[str], Any]: Tuple containing:
            - List of error messages
            - Result of the function if successful, None otherwise
    """
    try:
        result = func(*args)
    except Exception as e:
        return ([_format_error(context, f"{error_prefix}: {e}")], None)

    if format_results and isinstance(result, list):
        return ([_format_error(context, err) for err in result], None)
    return ([], result)


def _check_returns_section(context: DocstringContext, docstring: str) -> list[str]:
    """Check the Returns section name.

    Args:
        context (DocstringContext): Docstring context
        docstring (str): The docstring to process

    Returns:
        list[str]: List of error messages
    """
    errors, _ = safe_execute(
        context,
        check_returns_section_name,
        docstring,
        error_prefix="Error checking Returns section name",
    )
    return errors


def _validate_docstring_format(context: DocstringContext, docstring: str) -> list[str]:
    """Validate docstring format.

    Args:
        context (DocstringContext): Docstring context
        docstring (str): The docstring to process

    Returns:
        list[str]: List of error messages
    """
    errors, _ = safe_execute(
        context,
        validate_docstring,
        docstring,
        error_prefix="Error validating docstring",
    )
    return errors


def _parse_and_check_returns(context: DocstringContext, docstring: str) -> tuple[list[str], dict[str, Any] | None]:
    """Parse docstring and check returns type.

    Args:
        context (DocstringContext): Docstring context
        docstring (str): The docstring to process

    Returns:
        tuple[list[str], dict[str, Any] | None]: Tuple containing:
            - List of error messages
            - Parsed docstring dictionary if successful, None otherwise
    """
    errors = []

    # Parse docstring
    parse_errors, parsed = safe_execute(
        context,
        parse_google_docstring,
        docstring,
        error_prefix="Error parsing docstring",
        format_results=False,
    )
    if parse_errors:
        return parse_errors, None

    # Check returns type
    returns_errors, _ = safe_execute(
        context,
        check_returns_type,
        parsed,
        error_prefix="Error checking Returns type",
    )
    errors.extend(returns_errors)

    return errors, parsed


def _check_additional_validations(context: DocstringContext, parsed: dict[str, Any]) -> list[str]:
    """Run additional validations on parsed docstring.

    Args:
        context (DocstringContext): Docstring context
        parsed (dict[str, Any]): Parsed docstring

    Returns:
        list[str]: List of error messages
    """
    errors = []

    if context.require_param_types:
        type_errors, _ = safe_execute(
            context,
            check_param_types,
            parsed,
            context.require_param_types,
            error_prefix="Error checking parameter types",
        )
        errors.extend(type_errors)

    if context.check_references:
        ref_errors, _ = safe_execute(
            context,
            check_references,
            parsed,
            error_prefix="Error checking references",
        )
        errors.extend(ref_errors)

    return errors


def _process_docstring(context: DocstringContext, docstring: str) -> list[str]:
    """Process a single docstring.

    Args:
        context (DocstringContext): Docstring context
        docstring (str): The docstring to process

    Returns:
        list[str]: List of error messages
    """
    if not docstring:
        return []

    errors = []

    # Check Returns section name
    errors.extend(_check_returns_section(context, docstring))

    # Validate docstring format
    format_errors = _validate_docstring_format(context, docstring)
    errors.extend(format_errors)
    if format_errors:
        return errors

    # Parse and check returns
    parse_errors, parsed = _parse_and_check_returns(context, docstring)
    errors.extend(parse_errors)
    if not parsed:
        return errors

    # Run additional validations
    errors.extend(_check_additional_validations(context, parsed))

    return errors


def check_file(
    file_path: Path,
    require_param_types: bool = False,
    verbose: bool = False,
    check_references: bool = True,
) -> list[str]:
    """Check docstrings in a file.

    Args:
        file_path (Path): Path to the Python file
        require_param_types (bool): Whether parameter types are required
        verbose (bool): Whether to print verbose output
        check_references (bool): Whether to check references for errors

    Returns:
        list[str]: List of error messages
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
            check_references=check_references,
        )
        errors.extend(_process_docstring(context, docstring))

    return errors


def scan_directory(
    directory: Path,
    exclude_files: list[str] | None = None,
    require_param_types: bool = False,
    verbose: bool = False,
    check_references: bool = True,
) -> list[str]:
    """Scan a directory for Python files and check their docstrings.

    Args:
        directory (Path): Directory to scan
        exclude_files (list[str] | None): List of filenames to exclude
        require_param_types (bool): Whether parameter types are required
        verbose (bool): Whether to print verbose output
        check_references (bool): Whether to check references for errors

    Returns:
        list[str]: List of error messages
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
            errors.extend(check_file(py_file, require_param_types, verbose, check_references))
    return errors


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments
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
        "--check-references",
        action="store_true",
        help="Check references for errors",
    )
    parser.add_argument(
        "--no-check-references",
        action="store_true",
        help="Skip reference checking",
    )
    parser.add_argument(
        "--exclude-files",
        help="Comma-separated list of filenames to exclude",
        default="",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    return parser.parse_args()


def _get_config_values(
    args: argparse.Namespace,
    config: dict[str, Any],
) -> tuple[list[str], bool, bool, bool, list[str]]:
    """Get configuration values from command line arguments and config file.

    Args:
        args (argparse.Namespace): Command line arguments
        config (dict[str, Any]): Configuration dictionary

    Returns:
        tuple[list[str], bool, bool, bool, list[str]]: Tuple containing:
            - List of paths to check
            - Whether to require parameter types
            - Whether to check references
            - Whether to enable verbose output
            - List of files to exclude
    """
    # Get paths
    paths = args.paths or config["paths"]

    # Get require_param_types
    require_param_types = args.require_param_types or config["require_param_types"]

    # Get verbose
    verbose = args.verbose or config["verbose"]

    # Get check_references - handle both positive and negative flags
    check_references = config["check_references"]
    if args.check_references:
        check_references = True
    if args.no_check_references:
        check_references = False

    # Get exclude_files
    exclude_files = []
    if args.exclude_files:
        exclude_files = [f.strip() for f in args.exclude_files.split(",") if f.strip()]

    # If no exclude_files specified on command line, use the ones from config
    if not exclude_files:
        exclude_files = config["exclude_files"]

    return paths, require_param_types, verbose, check_references, exclude_files


def _process_paths(
    paths: list[str],
    exclude_files: list[str],
    require_param_types: bool,
    verbose: bool,
    check_references: bool,
) -> list[str]:
    """Process paths and check docstrings.

    Args:
        paths (list[str]): List of paths to check
        exclude_files (list[str]): List of files to exclude
        require_param_types (bool): Whether parameter types are required
        verbose (bool): Whether to print verbose output
        check_references (bool): Whether to check references for errors

    Returns:
        list[str]: List of error messages
    """
    all_errors = []
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            errors = scan_directory(path, exclude_files, require_param_types, verbose, check_references)
            all_errors.extend(errors)
        elif path.is_file() and path.suffix == ".py":
            errors = check_file(path, require_param_types, verbose, check_references)
            all_errors.extend(errors)
        else:
            print(f"Error: {path} is not a directory or Python file")
    return all_errors


def main() -> None:
    """Run the docstring checker.

    Returns:
        None
    """
    # Load configuration from pyproject.toml
    config = load_pyproject_config()

    # Parse command line arguments
    args = _parse_args()

    # Get configuration values
    paths, require_param_types, verbose, check_references, exclude_files = _get_config_values(args, config)

    # Print configuration if verbose
    if verbose:
        print("Configuration:")
        print(f"  Paths: {paths}")
        print(f"  Require parameter types: {require_param_types}")
        print(f"  Check references: {check_references}")
        print(f"  Exclude files: {exclude_files}")

    # Check if paths is empty
    if not paths:
        print(
            "No paths specified for checking. Please specify paths as command line "
            "arguments or configure them in pyproject.toml under [tool.docstring_checker] section.",
        )
        sys.exit(0)

    if all_errors := _process_paths(
        paths,
        exclude_files,
        require_param_types,
        verbose,
        check_references,
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
