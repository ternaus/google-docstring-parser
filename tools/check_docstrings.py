#!/usr/bin/env python
"""Check that docstrings in specified folders can be parsed.

This script scans Python files in specified directories and checks if their
docstrings can be parsed with the google_docstring_parser.
"""

import argparse
import ast
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from google_docstring_parser import parse_google_docstring


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


def check_file(file_path: str, verbose: bool = False) -> List[str]:
    """Check docstrings in a file.

    Args:
        file_path: Path to the Python file
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

        try:
            parse_google_docstring(docstring)
        except Exception as e:
            error_msg = f"{file_path}:{line_no}: Error parsing docstring for '{name}': {str(e)}"
            errors.append(error_msg)
            if verbose:
                print(error_msg)

    return errors


def scan_directory(directory: str, verbose: bool = False) -> List[str]:
    """Scan a directory for Python files and check their docstrings.

    Args:
        directory: Directory to scan
        verbose: Whether to print verbose output

    Returns:
        List of error messages
    """
    errors = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                errors.extend(check_file(file_path, verbose))
    return errors


def main():
    """Run the docstring checker."""
    parser = argparse.ArgumentParser(
        description="Check that docstrings in specified folders can be parsed."
    )
    parser.add_argument(
        "directories", nargs="+", help="Directories to scan for Python files"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    all_errors = []
    for directory in args.directories:
        if not os.path.isdir(directory):
            print(f"Error: {directory} is not a directory")
            continue
        errors = scan_directory(directory, args.verbose)
        all_errors.extend(errors)

    if all_errors:
        for error in all_errors:
            print(error)
        sys.exit(1)
    else:
        if args.verbose:
            print("All docstrings parsed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
