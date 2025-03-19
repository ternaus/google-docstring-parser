from __future__ import annotations

import pytest

from google_docstring_parser import parse_google_docstring
from google_docstring_parser.type_validation import (
    InvalidTypeAnnotationError,
    validate_type_annotation,
)


@pytest.mark.parametrize(
    "type_name,should_raise",
    [
        # Valid type annotations
        ("int", False),
        ("str", False),
        ("float", False),
        ("bool", False),
        ("None", False),
        ("Any", False),
        ("Optional[int]", False),
        ("Union[int, str]", False),
        ("List[int]", False),
        ("list[str]", False),
        ("Tuple[int, str]", False),
        ("tuple[int, ...]", False),
        ("Dict[str, Any]", False),
        ("dict[str, int]", False),
        ("Set[int]", False),
        ("FrozenSet[str]", False),
        ("Iterable[bytes]", False),
        ("Iterator[int]", False),
        ("Generator[int, None, None]", False),
        ("Sequence[str]", False),
        ("Callable[[int], str]", False),
        ("Mapping[str, int]", False),
        ("Type[int]", False),
        ("CustomType", False),
        ("module.CustomType", False),
        ('Literal["option1", "option2"]', False),

        # Invalid type annotations (bare collection types)
        ("List", True),
        ("list", True),
        ("Tuple", True),
        ("tuple", True),
        ("Dict", True),
        ("dict", True),
        ("Set", True),
        ("set", True),
        ("FrozenSet", True),
        ("frozenset", True),
        ("Iterable", True),
        ("Iterator", True),
        ("Generator", True),
        ("Sequence", True),
    ],
)
def test_validate_type_annotation(type_name: str, should_raise: bool) -> None:
    """Test the validate_type_annotation function with various type annotations."""
    if should_raise:
        with pytest.raises(InvalidTypeAnnotationError):
            validate_type_annotation(type_name)
    else:
        assert validate_type_annotation(type_name) is True


@pytest.mark.parametrize(
    "docstring,should_raise",
    [
        # Valid docstrings with properly formatted type annotations
        (
            """Description.

            Args:
                param1 (int): Description of param1
                param2 (str): Description of param2
            """,
            False,
        ),
        (
            """Description.

            Args:
                param1 (List[int]): Description of param1
                param2 (Dict[str, Any]): Description of param2
            """,
            False,
        ),
        (
            """Description.

            Args:
                param1 (list[int]): Description of param1
                param2 (tuple[str, int]): Description of param2
                param3 (dict[str, Any]): Description of param3
            """,
            False,
        ),
        (
            """Description.

            Returns:
                str: A string value
            """,
            False,
        ),
        (
            """Description.

            Returns:
                List[int]: A list of integers
            """,
            False,
        ),

        # Invalid docstrings with bare collection type annotations
        (
            """Description.

            Args:
                param1 (List): Description of param1
            """,
            True,
        ),
        (
            """Description.

            Args:
                param1 (int): Description of param1
                param2 (list): Description of param2
            """,
            True,
        ),
        (
            """Description.

            Args:
                param1 (Dict): Description of param1
            """,
            True,
        ),
        (
            """Description.

            Returns:
                Tuple: A tuple value
            """,
            True,
        ),
        (
            """Description.

            Args:
                param1 (int): Valid type
                param2 (str): Also valid type
                param3 (Sequence): Invalid type - missing element type
            """,
            True,
        ),
    ],
)
def test_parse_google_docstring_type_validation(docstring: str, should_raise: bool) -> None:
    """Test that parse_google_docstring properly validates type annotations."""
    if should_raise:
        with pytest.raises(InvalidTypeAnnotationError):
            parse_google_docstring(docstring)
    else:
        # Should parse without raising
        parse_google_docstring(docstring)


def test_error_message_content() -> None:
    """Test that the error message contains useful information."""
    collection_type = "List"
    with pytest.raises(InvalidTypeAnnotationError) as excinfo:
        validate_type_annotation(collection_type)

    # Check that the error message contains the type name and a suggestion
    error_message = str(excinfo.value)
    assert collection_type in error_message
    assert "must include element types" in error_message
    assert "List[str]" in error_message or "List[int]" in error_message


def test_complex_nested_types() -> None:
    """Test with complex nested type annotations."""
    complex_types = [
        "Dict[str, List[Tuple[int, float]]]",
        "Callable[[Dict[str, Any], List[int]], Optional[str]]",
        "Mapping[str, Union[int, List[Dict[str, Any]]]]",
        "Dict[FrozenSet[int], Tuple[List[str], Set[bytes]]]",
    ]

    for type_name in complex_types:
        # These should all be valid - they have their element types
        assert validate_type_annotation(type_name) is True
