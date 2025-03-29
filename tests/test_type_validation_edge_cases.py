from __future__ import annotations

import pytest

from google_docstring_parser import parse_google_docstring
from google_docstring_parser.type_validation import InvalidTypeAnnotationError


@pytest.mark.parametrize("docstring", [
    """Description.

    Args:
        param1 (Dict[str, List]): Invalid nested type
    """,
    """Description.

    Returns:
        Tuple[int, Dict]: Invalid return type
    """,
    """Description.

    Args:
        param1 (List[Dict]): First invalid type
        param2 (Tuple[int, List]): Second invalid type
    """,
])
def test_invalid_nested_types(docstring: str) -> None:
    """Test that invalid nested types are properly caught."""
    result = parse_google_docstring(docstring)
    assert "errors" in result
    assert any("invalid nested type" in error.lower() for error in result["errors"])


@pytest.mark.parametrize("docstring", [
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
])
def test_mixed_valid_invalid_types(docstring: str) -> None:
    """Test docstrings with both valid and invalid type annotations."""
    result = parse_google_docstring(docstring)
    assert "errors" in result
    assert any("collection" in error.lower() for error in result["errors"])


def test_none_type_handling() -> None:
    """Test that None types are properly handled."""
    docstring = """Description.

    Args:
        param1: No type specified
    """
    result = parse_google_docstring(docstring)
    assert "Args" in result
    assert result["Args"][0]["type"] is None


@pytest.mark.parametrize("docstring", [
    """Description.

    Args:
        param1 (List): Invalid bare collection
    """,
    """Description.

    Args:
        param1 (dict): Invalid bare collection
    """,
])
def test_invalid_case_sensitivity(docstring: str) -> None:
    """Test that invalid type validation is case-sensitive."""
    result = parse_google_docstring(docstring)
    assert "errors" in result
    assert any("collection" in error.lower() for error in result["errors"])


@pytest.mark.parametrize("docstring", [
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
])
def test_valid_case_sensitivity(docstring: str) -> None:
    """Test that valid type validation is case-sensitive."""
    parse_google_docstring(docstring)


@pytest.mark.parametrize("docstring", [
    """Description.

    Args:
        param1 (Literal["list", "tuple"]): Valid literal type
    """,
    """Description.

    Args:
        param1 (Literal["List"]): Valid literal containing a collection name
    """,
])
def test_string_literal_handling(docstring: str) -> None:
    """Test that string literals in type annotations are handled correctly."""
    parse_google_docstring(docstring)


@pytest.mark.parametrize("docstring,should_raise", [
    ("""Description.

    Args:
        param1 (Union[int, str]): Valid union
    """, False),
    ("""Description.

    Args:
        param1 (Union[int, List[str]]): Valid union with collection
    """, False),
    ("""Description.

    Args:
        param1 (Union[int, List]): Invalid union with bare collection
    """, True),
    ("""Description.

    Args:
        param1 (Union[Dict, List[int]]): Invalid union with bare collection
    """, True),
])
def test_union_type_handling(docstring: str, should_raise: bool) -> None:
    """Test that Union types are properly validated."""
    result = parse_google_docstring(docstring)
    if should_raise:
        assert "errors" in result
        assert any("collection" in error.lower() for error in result["errors"])
    else:
        assert "errors" not in result or not result["errors"]


def test_docstring_without_types() -> None:
    """Test that docstrings without types are still valid."""
    docstring = """Simple description without args or returns."""
    result = parse_google_docstring(docstring)
    assert result["Description"] == "Simple description without args or returns."
