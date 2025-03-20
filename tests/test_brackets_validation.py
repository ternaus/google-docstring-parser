"""Tests for bracket balancing and validation logic in type annotations."""

from __future__ import annotations

import pytest

from google_docstring_parser.type_validation import (
    BracketValidationError,
    InvalidTypeAnnotationError,
    _process_string_literals,
    _tokenize_type_declaration,
    _validate_type_declaration,
)


def test_process_string_literals() -> None:
    """Test that string literals are properly processed and placeholders are returned."""
    # Test with various string literals
    test_input = 'Type[Literal["list", "tuple"]] and "Dict"'
    result, extracted = _process_string_literals(test_input)

    # Check that string literals were extracted
    assert len(extracted) == 3
    assert extracted[0] == '"list"'
    assert extracted[1] == '"tuple"'
    assert extracted[2] == '"Dict"'

    # Check that placeholders were inserted
    assert "STR_LITERAL_0" in result
    assert "STR_LITERAL_1" in result
    assert "STR_LITERAL_2" in result


def test_tokenize_type_declaration() -> None:
    """Test that type declarations are properly tokenized."""
    # Test with various type declarations
    test_cases = [
        # Simple type
        ("int", ["int"]),
        # Collection type
        ("List[int]", ["List", "[", "int", "]"]),
        # Nested type
        ("Dict[str, List[int]]", ["Dict", "[", "str", ",", "List", "[", "int", "]", "]"]),
        # Multiple brackets
        ("Tuple[int, (str, float)]", ["Tuple", "[", "int", ",", "(", "str", ",", "float", ")", "]"]),
        # Curly braces
        ("Set[{1, 2, 3}]", ["Set", "[", "{", "1", ",", "2", ",", "3", "}", "]"]),
        # Mixed brackets
        ("Dict[str, (List[int], {Set[str]})]",
         ["Dict", "[", "str", ",", "(", "List", "[", "int", "]", ",", "{", "Set", "[", "str", "]", "}", ")", "]"]),
    ]

    for input_str, expected_tokens in test_cases:
        tokens = _tokenize_type_declaration(input_str)
        assert tokens == expected_tokens, f"Failed for input: {input_str}"


@pytest.mark.parametrize(
    "type_declaration,should_raise",
    [
        # Valid bracket combinations
        ("List[int]", False),
        ("Dict[str, Any]", False),
        ("Tuple[int, str, bool]", False),
        ("Set[frozenset[int]]", False),
        ("Dict[str, List[Tuple[int, float]]]", False),
        ("Callable[[int, str], bool]", False),
        ("Dict[str, (int, float)]", False),  # Parentheses
        ("Union[str, {int, float}]", False),  # Curly braces
        ("Dict[str, Union[(int, float), {str, bytes}]]", False),  # Mixed brackets

        # Invalid bracket combinations - unbalanced
        ("List[int", True),
        ("Dict[str, Any", True),
        ("Tuple[int, str, bool", True),
        ("List]int[", True),
        ("Dict]str, Any[", True),

        # Invalid bracket combinations - mismatched
        ("List(int]", True),
        ("Dict[str, Any}", True),
        ("Tuple{int, str, bool]", True),

        # Invalid bracket combinations - nested mismatches
        ("Dict[str, List[Tuple(int, float]]]", True),
        ("Dict[str, List{Tuple[int, float]}]", True),

        # Invalid collection usage - bare collections
        ("List", True),
        ("Dict", True),
        ("List without brackets", True),
        ("Nested Dict[str, List] with bare List", True),
        ("Nested Dict[str, Tuple[int, List]] with bare List", True),
        ("Dict[List, int]", True),  # List should have element type
    ],
)
def test_validate_type_declaration(type_declaration: str, should_raise: bool) -> None:
    """Test validation of type declarations with various bracket combinations."""
    # Check if validation raises an exception as expected
    if should_raise:
        with pytest.raises((BracketValidationError, InvalidTypeAnnotationError)):
            _validate_type_declaration(type_declaration)
    else:
        # Should not raise any exception
        _validate_type_declaration(type_declaration)


@pytest.mark.parametrize(
    "bracket_pairs",
    [
        # Simple balanced pairs
        "[]",
        "()",
        "{}",
        # Nested balanced pairs
        "[()]",
        "{[]}",
        "({[]})",
        # Multiple balanced pairs
        "[](){}",
        "[()]{[()]}",
        # Complex balanced pairs with other content
        "List[Dict[str, Set[int]]]",
        "Dict[str, (Tuple[int, float], {str, bytes})]",
    ],
)
def test_balanced_brackets(bracket_pairs: str) -> None:
    """Test that properly balanced bracket combinations are validated correctly."""
    # Add some context to make it look like a type annotation if needed
    if not any(bracket_pairs.startswith(prefix) for prefix in ["List", "Dict", "Tuple", "Set"]):
        test_input = f"Type{bracket_pairs}" if bracket_pairs[0] == "[" else f"Type[{bracket_pairs}]"
    else:
        test_input = bracket_pairs

    # Should not raise any exception
    _validate_type_declaration(test_input)


@pytest.mark.parametrize(
    "unbalanced_brackets",
    [
        # Unbalanced - missing closing
        "[",
        "(",
        "{",
        "[(",
        "{[",
        # Unbalanced - missing opening
        "]",
        ")",
        "}",
        ")]",
        "}]",
        # Unbalanced - mixed
        "[)",
        "(]",
        "{]",
        "[}",
        # Complex unbalanced
        "List[Dict[str, Set[int]",
        "Dict[str, (Tuple[int, float], {str, bytes}]",
    ],
)
def test_unbalanced_brackets(unbalanced_brackets: str) -> None:
    """Test that unbalanced bracket combinations are properly rejected."""
    # Add some context to make it look like a type annotation
    if not any(unbalanced_brackets.startswith(prefix) for prefix in ["List", "Dict", "Tuple", "Set"]):
        # Ensure it starts with a valid collection name for proper testing
        if unbalanced_brackets.startswith("[") or unbalanced_brackets.startswith("(") or unbalanced_brackets.startswith("{"):
            test_input = f"List{unbalanced_brackets}"
        else:
            test_input = f"List[{unbalanced_brackets}]"
    else:
        test_input = unbalanced_brackets

    # Should raise an exception
    with pytest.raises(BracketValidationError):
        _validate_type_declaration(test_input)
