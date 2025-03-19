from __future__ import annotations

import pytest

from google_docstring_parser import parse_google_docstring
from google_docstring_parser.google_docstring_parser import InvalidTypeAnnotationError


def test_invalid_nested_types() -> None:
    """Test that invalid nested types are properly caught."""
    docstrings = [
        # Invalid nested type (inner type is a bare collection)
        """Description.

        Args:
            param1 (Dict[str, List]): Invalid nested type
        """,

        # Invalid nested type in return
        """Description.

        Returns:
            Tuple[int, Dict]: Invalid return type
        """,

        # Multiple invalid parameters
        """Description.

        Args:
            param1 (List[Dict]): First invalid type
            param2 (Tuple[int, List]): Second invalid type
        """,
    ]

    for docstring in docstrings:
        with pytest.raises(InvalidTypeAnnotationError):
            parse_google_docstring(docstring)


def test_mixed_valid_invalid_types() -> None:
    """Test docstrings with both valid and invalid type annotations."""
    docstrings = [
        """Description.

        Args:
            param1 (int): Valid type
            param2 (str): Valid type
            param3 (List): Invalid type
            param4 (Dict[str, int]): Valid type
        """,

        """Description.

        Args:
            param1 (Dict[str, Any]): Valid type
            param2 (Set): Invalid type

        Returns:
            List[int]: Valid return type
        """,

        """Description.

        Args:
            param1 (List[int]): Valid type
            param2 (Tuple): Invalid type

        Returns:
            Dict: Invalid return type
        """,
    ]

    for docstring in docstrings:
        with pytest.raises(InvalidTypeAnnotationError):
            parse_google_docstring(docstring)


def test_none_type_handling() -> None:
    """Test that None types are properly handled."""
    # None type parameter
    docstring = """Description.

    Args:
        param1: No type specified
    """

    # Should parse successfully since we're not validating missing types
    result = parse_google_docstring(docstring)
    assert "Args" in result
    assert result["Args"][0]["type"] is None


def test_case_sensitivity() -> None:
    """Test that type validation is case-sensitive and only exact matches are caught."""
    # These should raise errors because they exactly match our list of collection types
    invalid_docstrings = [
        """Description.

        Args:
            param1 (List): Invalid bare collection
        """,

        """Description.

        Args:
            param1 (dict): Invalid bare collection
        """,
    ]

    for docstring in invalid_docstrings:
        with pytest.raises(InvalidTypeAnnotationError):
            parse_google_docstring(docstring)

    # These should NOT raise errors because they don't exactly match our collection types
    valid_docstrings = [
        """Description.

        Args:
            param1 (LIST): Not in our list of collections to check
        """,

        """Description.

        Args:
            param1 (Dict_): Not in our list of collections to check
        """,

        """Description.

        Args:
            param1 (TUPLE): Not in our list of collections to check
        """,
    ]

    for docstring in valid_docstrings:
        # Should not raise
        parse_google_docstring(docstring)


def test_string_literal_handling() -> None:
    """Test that string literals in type annotations are handled correctly."""
    # These should be valid
    valid_docstrings = [
        """Description.

        Args:
            param1 (Literal["list", "tuple"]): Valid literal type
        """,

        """Description.

        Args:
            param1 (Literal["List"]): Valid literal containing a collection name
        """,
    ]

    for docstring in valid_docstrings:
        # Should not raise
        parse_google_docstring(docstring)


def test_union_type_handling() -> None:
    """Test that Union types are properly validated."""
    # These should be valid
    valid_docstrings = [
        """Description.

        Args:
            param1 (Union[int, str]): Valid union
        """,

        """Description.

        Args:
            param1 (Union[int, List[str]]): Valid union with collection
        """,
    ]

    for docstring in valid_docstrings:
        # Should not raise
        parse_google_docstring(docstring)

    # These should raise errors
    invalid_docstrings = [
        """Description.

        Args:
            param1 (Union[int, List]): Invalid union with bare collection
        """,

        """Description.

        Args:
            param1 (Union[Dict, List[int]]): Invalid union with bare collection
        """,
    ]

    for docstring in invalid_docstrings:
        with pytest.raises(InvalidTypeAnnotationError):
            parse_google_docstring(docstring)


def test_docstring_without_types() -> None:
    """Test that docstrings without types are still valid."""
    docstring = """Simple description without args or returns."""

    # Should not raise
    result = parse_google_docstring(docstring)
    assert result["Description"] == "Simple description without args or returns."
