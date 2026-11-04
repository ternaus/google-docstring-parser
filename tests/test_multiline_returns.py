"""Wrapped return annotations retain their type and checker consistency."""

from pathlib import Path

import pytest

from google_docstring_parser import parse_google_docstring
from google_docstring_parser.type_validation import BracketValidationError, InvalidTypeAnnotationError
from tools.check_docstrings import check_file


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        ("int |\n    str", "int | str"),
        ("int\n    | str", "int | str"),
        ("dict[\n    str,\n    list[int]\n]", "dict[str, list[int]]"),
        ('Literal[\n    "a:b",\n    "c",\n]', "Literal['a:b', 'c']"),
        ('Literal[\n    "]",\n    "tail",\n]', "Literal[']', 'tail']"),
        ("(\n    int |\n    str\n)", "int | str"),
        ("dict\n    [str, int]", "dict[str, int]"),
        ('Literal[\n    "a  b",\n    "x:y|[]",\n]', "Literal['a  b', 'x:y|[]']"),
        ('Literal[\n    "a\\\"b:c",\n    "tail",\n]', '''Literal['a"b:c', 'tail']'''),
        ("(\n    int\n    | str\n)", "int | str"),
        ("dict\n  [str,\n      int]", "dict[str, int]"),
        ('Annotated[\n    str,\n    {"key:[]": "value"}\n]', "Annotated[str, {'key:[]': 'value'}]"),
    ],
)
def test_wrapped_return_annotation(annotation: str, expected: str) -> None:
    parsed = parse_google_docstring(f"Example.\n\nReturns:\n    {annotation}: Result.")

    assert parsed["Returns"] == {"type": expected, "description": "Result."}
    assert "errors" not in parsed


@pytest.mark.parametrize(
    "description",
    [
        "Result description\n    Extra details: more text.",
        "A normalized value in [0,\n    1]: endpoints included.",
        "A result description\n    | Column: value |",
        "Result\n\n    | str: unrelated prose.",
        'Literal["a:b"]',
        "42\n    | 137: numeric prose.",
    ],
)
def test_returns_without_annotation_stay_untyped(description: str) -> None:
    parsed = parse_google_docstring(f"Example.\n\nReturns:\n    {description}")

    assert parsed["Returns"]["type"] is None
    assert "errors" not in parsed


def test_large_incomplete_return_annotation_stays_untyped() -> None:
    text = "Example.\n\nReturns:\n    list[\n" + "        int,\n" * 10_000

    assert parse_google_docstring(text)["Returns"]["type"] is None


@pytest.mark.parametrize(
    ("annotation", "documented", "expected_error"),
    [
        ("int | str", "int |\n            str", None),
        ("dict[str, int]", "dict\n            [str, int]", None),
        ("int | str", "(\n            int | str\n        )", None),
        ('Literal["a:b", "]"]', 'Literal[\n            "a:b",\n            "]"\n        ]', None),
        ('Literal["a  b"]', 'Literal[\n            "a  b"\n        ]', None),
        ("Literal['a:b']", 'Literal["a:b"]', None),
        (
            "np.ndarray[tuple[int, ...], np.dtype[np.uint8] | np.dtype[np.float32]]",
            "np.ndarray[\n            tuple[int, ...],\n            np.dtype[np.uint8] | np.dtype[np.float32]\n        ]",
            None,
        ),
        ('Literal["a b"]', 'Literal[\n            "a  b"\n        ]', "Returns: docstring says"),
        ("int", "int |\n            str", "Returns: docstring says"),
    ],
)
def test_checker_compares_wrapped_types(
    tmp_path: Path, annotation: str, documented: str, expected_error: str | None
) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        '"""Example module."""\n'
        f'def choose() -> {annotation}:\n'
        '    """Choose a result.\n\n'
        '    Returns:\n'
        f'        {documented}: Result.\n'
        '    """\n'
        '    return 137\n',
        encoding="utf-8",
    )
    errors = check_file(source, require_param_types=True, check_type_consistency=True)

    if expected_error is None:
        assert errors == []
    else:
        assert len(errors) == 1
        assert expected_error in errors[0]


@pytest.mark.parametrize(
    ("annotation", "error_type"),
    [
        ("list(int)", BracketValidationError),
        ("list[\n    dict\n]", InvalidTypeAnnotationError),
    ],
)
def test_return_validation_error_modes(annotation: str, error_type: type[InvalidTypeAnnotationError]) -> None:
    docstring = f"Example.\n\nReturns:\n    {annotation}: Result."

    collected = parse_google_docstring(docstring)
    assert len(collected["errors"]) == 1
    assert collected["Returns"]["type"] is not None

    with pytest.raises(error_type):
        parse_google_docstring(docstring, collect_errors=False)

    unchecked = parse_google_docstring(docstring, validate_types=False)
    assert "errors" not in unchecked
    assert unchecked["Returns"] == collected["Returns"]


def test_argument_bracket_errors_are_collected() -> None:
    docstring = "Example.\n\nArgs:\n    value (list[int}): Invalid brackets."

    parsed = parse_google_docstring(docstring)

    assert len(parsed["errors"]) == 1
    assert "bracket" in parsed["errors"][0].lower()
