"""Wrapped return annotations retain their type and checker consistency."""

from pathlib import Path

import pytest

from google_docstring_parser import parse_google_docstring
from tools.check_docstrings import check_file


@pytest.mark.parametrize(
    ("annotation", "expected"),
    [
        ("int |\n    str", "int | str"),
        ("int\n    | str", "int | str"),
        ("dict[\n    str,\n    list[int]\n]", "dict[ str, list[int] ]"),
    ],
)
def test_wrapped_return_annotation(annotation: str, expected: str) -> None:
    parsed = parse_google_docstring(f"Example.\n\nReturns:\n    {annotation}: Result.")

    assert parsed["Returns"] == {"type": expected, "description": "Result."}


def test_untyped_return_description_stays_untyped() -> None:
    parsed = parse_google_docstring("Example.\n\nReturns:\n    Result description\n        Extra details: more text.")

    assert parsed["Returns"]["type"] is None


def test_checker_accepts_wrapped_return_annotation(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text(
        '"""Example module."""\n\n'
        'def choose() -> int | str:\n'
        '    """Choose a result.\n\n'
        '    Returns:\n'
        '        int |\n'
        '            str: Result.\n'
        '    """\n'
        '    return 137\n'
    )

    assert check_file(source, require_param_types=True, check_type_consistency=True) == []
