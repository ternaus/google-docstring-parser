#!/usr/bin/env python
"""Check that docstrings in specified folders can be parsed.

This script scans Python files in specified directories and checks if their
docstrings can be parsed with the google_docstring_parser.
"""

import argparse
import ast
import inspect
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, get_type_hints

import tomli

from google_docstring_parser import parse_google_docstring

# Default configuration
DEFAULT_CONFIG = {
    "paths": ["."],
    "require_param_types": False,
    "check_type_consistency": False,
    "exclude_files": [],
    "verbose": False,
}

# Mapping from common docstring type names to their Python type equivalents
TYPE_MAPPING = {
    "str": str,
    "string": str,
    "int": int,
    "integer": int,
    "float": float,
    "bool": bool,
    "boolean": bool,
    "list": list,
    "dict": dict,
    "tuple": tuple,
    "set": set,
    "none": type(None),
    "None": type(None),
    "any": Any,
    "Any": Any,
}


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
        if "check_type_consistency" in tool_config:
            config["check_type_consistency"] = bool(tool_config["check_type_consistency"])
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
    if not require_types or "args" not in docstring_dict:
        return []

    errors = []
    for arg in docstring_dict["args"]:
        if arg["type"] is None:
            errors.append(f"Parameter '{arg['name']}' is missing a type")

    return errors


def normalize_type_string(type_str: str) -> str:
    """Normalize a type string for comparison.

    Args:
        type_str: The type string from a docstring

    Returns:
        Normalized type string
    """
    # Remove spaces and convert to lowercase for basic comparison
    normalized = type_str.lower().replace(" ", "")

    # Handle common aliases
    normalized = normalized.replace("integer", "int")
    normalized = normalized.replace("boolean", "bool")
    normalized = normalized.replace("string", "str")

    # Handle optional types
    if normalized.startswith("optional[") and normalized.endswith("]"):
        inner_type = normalized[9:-1]  # Extract type inside Optional[]
        normalized = f"union[{inner_type},none]"

    return normalized


def extract_annotation_type_str(annotation) -> str:
    """Extract a string representation from a type annotation.

    Args:
        annotation: Type annotation from function signature

    Returns:
        String representation of the type
    """
    if annotation is None:
        return "None"

    if hasattr(annotation, "__origin__"):
        # Handle generic types like List[str], Dict[str, int], etc.
        origin = annotation.__origin__
        args = getattr(annotation, "__args__", [])

        if origin is Union:
            return f"Union[{', '.join(extract_annotation_type_str(arg) for arg in args)}]"

        origin_name = origin.__name__ if hasattr(origin, "__name__") else str(origin)
        if args:
            args_str = ", ".join(extract_annotation_type_str(arg) for arg in args)
            return f"{origin_name}[{args_str}]"
        return origin_name

    # Handle basic types
    if hasattr(annotation, "__name__"):
        return annotation.__name__

    return str(annotation)


def compare_types(docstring_type: str, annotation_type) -> bool:
    """Compare a docstring type with a function annotation type.

    Args:
        docstring_type: Type string from docstring
        annotation_type: Type annotation from function

    Returns:
        True if types are compatible, False otherwise
    """
    if docstring_type is None or annotation_type is None:
        return False

    # Normalize docstring type
    normalized_docstring = normalize_type_string(docstring_type)

    # Get string representation of annotation
    annotation_str = normalize_type_string(extract_annotation_type_str(annotation_type))

    # Direct comparison
    if normalized_docstring == annotation_str:
        return True

    # Handle special cases
    if normalized_docstring == "any" or annotation_str == "any":
        return True

    # Handle Union/Optional types
    if "union" in normalized_docstring and "union" in annotation_str:
        # This is a simplified check - a more robust implementation would parse and compare the union members
        return True

    return False


def verify_type_consistency(node: ast.AST, docstring_dict: dict) -> list[str]:
    """Check if types in docstring match function annotations.

    Args:
        node: AST node for the function
        docstring_dict: Parsed docstring dictionary

    Returns:
        List of error messages for type inconsistencies
    """
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []

    # Ensure docstring_dict is a dictionary and has the expected structure
    if not isinstance(docstring_dict, dict) or "args" not in docstring_dict:
        return []

    # Ensure args is a list
    if not isinstance(docstring_dict["args"], list):
        return []

    errors = []

    try:
        # Extract parameter annotations from function definition
        param_annotations = {}
        for arg in node.args.args:
            if hasattr(arg, "annotation") and arg.annotation is not None:
                # Get a simple string representation of the annotation
                if isinstance(arg.annotation, ast.Name):
                    param_annotations[arg.arg] = arg.annotation.id
                elif isinstance(arg.annotation, ast.Subscript):
                    # For generic types like List[str], just get the base type
                    if isinstance(arg.annotation.value, ast.Name):
                        param_annotations[arg.arg] = arg.annotation.value.id
                    else:
                        param_annotations[arg.arg] = "complex_type"
                else:
                    param_annotations[arg.arg] = "complex_type"

        # Compare docstring types with annotations
        for arg in docstring_dict["args"]:
            # Ensure arg is a dictionary with the expected keys
            if not isinstance(arg, dict) or "name" not in arg or "type" not in arg:
                continue

            param_name = arg["name"]
            docstring_type = arg["type"]

            # Skip if either is None
            if param_name is None or docstring_type is None:
                continue

            if param_name in param_annotations:
                annotation_type = param_annotations[param_name]

                # Simple comparison - just check if the base type is mentioned in the docstring
                docstring_lower = docstring_type.lower()
                annotation_lower = annotation_type.lower()

                # Basic type check - this is very simplified
                if (annotation_lower not in docstring_lower and
                    not (annotation_lower == "str" and "string" in docstring_lower) and
                    not (annotation_lower == "int" and "integer" in docstring_lower) and
                    not (annotation_lower == "bool" and "boolean" in docstring_lower)):
                    errors.append(
                        f"Type mismatch for parameter '{param_name}': "
                        f"docstring says '{docstring_type}', annotation is '{annotation_type}'"
                    )

        # Check return type if present
        if ("returns" in docstring_dict and
            isinstance(docstring_dict["returns"], list) and
            len(docstring_dict["returns"]) > 0 and
            isinstance(docstring_dict["returns"][0], dict) and
            "type" in docstring_dict["returns"][0] and
            hasattr(node, "returns") and
            node.returns is not None):

            docstring_return = docstring_dict["returns"][0]["type"]
            if docstring_return is None:
                docstring_return = "None"

            # Get a simple string representation of the return annotation
            if isinstance(node.returns, ast.Name):
                return_annotation = node.returns.id
            elif isinstance(node.returns, ast.Subscript):
                if isinstance(node.returns.value, ast.Name):
                    return_annotation = node.returns.value.id
                else:
                    return_annotation = "complex_type"
            else:
                return_annotation = "complex_type"

            # Simple comparison for return type
            docstring_lower = docstring_return.lower()
            annotation_lower = return_annotation.lower()

            if (annotation_lower not in docstring_lower and
                not (annotation_lower == "str" and "string" in docstring_lower) and
                not (annotation_lower == "int" and "integer" in docstring_lower) and
                not (annotation_lower == "bool" and "boolean" in docstring_lower)):
                errors.append(
                    f"Return type mismatch: docstring says '{docstring_return}', "
                    f"annotation is '{return_annotation}'"
                )

    except Exception as e:
        errors.append(f"Error checking type consistency: {str(e)}")

    return errors


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
            "Args",
            "Returns",
            "Raises",
            "Yields",
            "Example",
            "Examples",
            "Note",
            "Notes",
            "Warning",
            "Warnings",
            "See",
            "References",
            "Attributes",
        ]:
            errors.append(f"Unknown section header: '{section_match.group(1)}'")

    return errors


def check_file(
    file_path: Path,
    require_param_types: bool = False,
    check_type_consistency: bool = False,
    verbose: bool = False
) -> list[str]:
    """Check docstrings in a file.

    Args:
        file_path: Path to the Python file
        require_param_types: Whether parameter types are required
        check_type_consistency: Whether to check if docstring types match annotations
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
        error_msg = f"{file_path}: Error getting docstrings: {str(e)}"
        errors.append(error_msg)
        if verbose:
            print(error_msg)
        return errors

    for name, line_no, docstring, node in docstrings:
        if not docstring:
            continue

        # Perform additional validation
        try:
            validation_errors = validate_docstring(docstring)
            for error in validation_errors:
                error_msg = f"{file_path}:{line_no}: {error} in '{name}'"
                errors.append(error_msg)
                if verbose:
                    print(error_msg)
        except Exception as e:
            error_msg = f"{file_path}:{line_no}: Error validating docstring for '{name}': {str(e)}"
            errors.append(error_msg)
            if verbose:
                print(error_msg)
            continue

        try:
            parsed = parse_google_docstring(docstring)

            # Check for missing parameter types if required
            if require_param_types:
                try:
                    type_errors = check_param_types(parsed, require_param_types)
                    for error in type_errors:
                        error_msg = f"{file_path}:{line_no}: {error} in '{name}'"
                        errors.append(error_msg)
                        if verbose:
                            print(error_msg)
                except Exception as e:
                    error_msg = f"{file_path}:{line_no}: Error checking parameter types for '{name}': {str(e)}"
                    errors.append(error_msg)
                    if verbose:
                        print(error_msg)

            # Check type consistency if required
            if check_type_consistency and node is not None:
                try:
                    if verbose:
                        print(f"Checking type consistency for {name}")

                    # Debug: Print the node type
                    if verbose:
                        print(f"Node type: {type(node)}")

                    consistency_errors = verify_type_consistency(node, parsed)
                    for error in consistency_errors:
                        error_msg = f"{file_path}:{line_no}: {error} in '{name}'"
                        errors.append(error_msg)
                        if verbose:
                            print(error_msg)
                except Exception as e:
                    error_msg = f"{file_path}:{line_no}: Error checking type consistency for '{name}': {str(e)}"
                    errors.append(error_msg)
                    if verbose:
                        print(error_msg)
                    # Debug: Print the exception traceback
                    if verbose:
                        import traceback
                        print(f"Exception traceback: {traceback.format_exc()}")

        except Exception as e:
            error_msg = f"{file_path}:{line_no}: Error parsing docstring for '{name}': {e!s}"
            errors.append(error_msg)
            if verbose:
                print(error_msg)

    return errors


def scan_directory(
    directory: Path,
    exclude_files: list[str] = None,
    require_param_types: bool = False,
    check_type_consistency: bool = False,
    verbose: bool = False,
) -> list[str]:
    """Scan a directory for Python files and check their docstrings.

    Args:
        directory: Directory to scan
        exclude_files: List of filenames to exclude
        require_param_types: Whether parameter types are required
        check_type_consistency: Whether to check if docstring types match annotations
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
            errors.extend(check_file(py_file, require_param_types, check_type_consistency, verbose))
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


def get_env_var_as_list(var_name: str, default: list[str] = None, separator: str = ",") -> list[str]:
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
        "--check-type-consistency",
        action="store_true",
        help="Check if types in docstrings match function annotations",
    )
    parser.add_argument(
        "--exclude-files",
        help="Comma-separated list of filenames to exclude",
        default="",
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

    # Get check_type_consistency
    check_type_consistency = args.check_type_consistency
    if not check_type_consistency:
        check_type_consistency = get_env_var_as_bool("DOCSTRING_CHECK_TYPE_CONSISTENCY")
        if not check_type_consistency:
            check_type_consistency = config["check_type_consistency"]

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
    for path_str in paths:
        path = Path(path_str)
        if path.is_dir():
            errors = scan_directory(path, exclude_files, require_param_types, check_type_consistency, verbose)
            all_errors.extend(errors)
        elif path.is_file() and path.suffix == ".py":
            errors = check_file(path, require_param_types, check_type_consistency, verbose)
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
