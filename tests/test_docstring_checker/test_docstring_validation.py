"""Tests for the docstring validation functions."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from tools.check_docstrings import (
    validate_docstring,
    check_param_types,
    get_docstrings,
)
from google_docstring_parser.google_docstring_parser import parse_google_docstring


@pytest.mark.parametrize(
    "docstring,expected_errors",
    [
        # Valid docstring
        (
            """A valid docstring.

            Args:
                param1 (int): An integer parameter
                param2 (str): A string parameter

            Returns:
                bool: True if successful
            """,
            [],
        ),
        # Unclosed parenthesis
        (
            """A docstring with unclosed parenthesis.

            Args:
                param1 (list[str): Parameter with unclosed bracket in type
            """,
            ["Unclosed parenthesis in parameter type: 'param1 (list[str): Parameter with unclosed bracket in type'"],
        ),
        # Docstring with custom section (should not trigger errors now)
        (
            """A docstring with custom section.

            Args:
                param1 (str): A string parameter

            BadSection:
                This section has a custom name
            """,
            [],
        ),
        # Multiple issues (only parenthesis issues should be detected now)
        (
            """A docstring with multiple issues.

            Args:
                param1 (dict[str, list[int): Unclosed bracket

            InvalidSection:
                This section is invalid
            """,
            [
                "Unclosed parenthesis in parameter type: 'param1 (dict[str, list[int): Unclosed bracket'",
            ],
        ),
    ],
)
def test_validate_docstring(docstring: str, expected_errors: list[str]) -> None:
    """Test the validate_docstring function with various docstrings."""
    errors = validate_docstring(docstring)
    assert errors == expected_errors


@pytest.mark.parametrize(
    "docstring_dict,require_types,expected_errors",
    [
        # No args
        ({"description": "A docstring with no args"}, True, []),
        # All args have types
        (
            {
                "description": "A docstring with args that have types",
                "Args": [
                    {"name": "param1", "type": "int", "description": "An integer parameter"},
                    {"name": "param2", "type": "str", "description": "A string parameter"},
                ],
            },
            True,
            [],
        ),
        # Missing types when required
        (
            {
                "description": "A docstring with args missing types",
                "Args": [
                    {"name": "param1", "type": None, "description": "Missing type"},
                    {"name": "param2", "type": "str", "description": "Has type"},
                ],
            },
            True,
            ["Parameter 'param1' is missing a type in docstring"],
        ),
        # Multiple missing types
        (
            {
                "description": "A docstring with multiple args missing types",
                "Args": [
                    {"name": "param1", "type": None, "description": "Missing type"},
                    {"name": "param2", "type": None, "description": "Also missing type"},
                    {"name": "param3", "type": "str", "description": "Has type"},
                ],
            },
            True,
            ["Parameter 'param1' is missing a type in docstring", "Parameter 'param2' is missing a type in docstring"],
        ),
        # Missing types but not required
        (
            {
                "description": "A docstring with args missing types",
                "Args": [
                    {"name": "param1", "type": None, "description": "Missing type"},
                    {"name": "param2", "type": "str", "description": "Has type"},
                ],
            },
            False,
            [],
        ),
    ],
)
def test_check_param_types(docstring_dict: dict[str, Any], require_types: bool, expected_errors: list[str]) -> None:
    """Test the check_param_types function with various docstring dictionaries."""
    errors = check_param_types(docstring_dict, require_types)
    assert errors == expected_errors


def test_get_docstrings() -> None:
    """Test the get_docstrings function with the test files."""
    # Test with valid docstrings file
    valid_file = Path(__file__).parent / "test_valid_docstrings.py"
    docstrings = get_docstrings(valid_file)

    # Check that we found the module docstring
    assert docstrings[0][0] == "module"

    # Check that we found the class and function docstrings
    function_names = [name for name, _, _, _ in docstrings[1:]]
    assert "simple_function" in function_names
    assert "function_with_args" in function_names
    assert "function_with_sections" in function_names
    assert "ValidClass" in function_names

    # Test with malformed docstrings file
    malformed_file = Path(__file__).parent / "test_malformed_docstrings.py"
    docstrings = get_docstrings(malformed_file)

    # Check that we found the module docstring
    assert docstrings[0][0] == "module"

    # Check that we found the function docstrings with issues
    function_names = [name for name, _, _, _ in docstrings[1:]]
    assert "missing_arg_type" in function_names
    assert "malformed_section" in function_names
    assert "unclosed_parenthesis" in function_names
    assert "MalformedClass" in function_names


@pytest.mark.parametrize(
    "docstring,expected_args_count,expected_returns_count",
    [
        # Simple docstring
        (
            """A simple docstring.""",
            0,
            0,
        ),
        # Docstring with args
        (
            """Docstring with args.

            Args:
                param1 (int): An integer parameter
                param2 (str): A string parameter
            """,
            2,
            0,
        ),
        # Docstring with args and returns
        (
            """Docstring with args and returns.

            Args:
                param1 (int): An integer parameter
                param2 (str): A string parameter

            Returns:
                bool: True if successful
            """,
            2,
            1,
        ),
        # Docstring with multiple sections
        (
            """Docstring with multiple sections.

            Args:
                param1 (int): An integer parameter

            Returns:
                bool: True if successful

            Raises:
                ValueError: If param1 is negative
            """,
            1,
            1,
        ),
    ],
)
def test_parse_google_docstring(docstring: str, expected_args_count: int, expected_returns_count: int) -> None:
    """Test the parse_google_docstring function with various docstrings."""
    parsed = parse_google_docstring(docstring)

    # Check args count
    args = parsed.get("Args", [])
    assert len(args) == expected_args_count, f"Expected {expected_args_count} args, got {args}"

    # Check returns count
    returns = parsed.get("Returns", [])
    assert len(returns) == expected_returns_count
