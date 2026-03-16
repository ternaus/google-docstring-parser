---
name: pytest-parametrize
description: Write pytest tests using parametrize for similar cases, fixtures, and project test layout. Use when adding tests, writing test cases, parametrizing, or when asked to test new code.
---

# Pytest and Parametrize (Project)

## Test layout

- `tests/test_*.py` for top-level tests
- `tests/test_docstring_checker/` for checker-specific tests
- Use `pytest` and `@pytest.mark.parametrize`

## Parametrize pattern

```python
import pytest

@pytest.mark.parametrize(
    "docstring,expected",
    [
        (
            """Description.

            Args:
                x (int): Param x
            """,
            {"Description": "Description.", "Args": [{"name": "x", "type": "int", "description": "Param x"}]},
        ),
        # More cases...
    ],
)
def test_parse(docstring: str, expected: dict) -> None:
    assert parse_google_docstring(docstring) == expected
```

## Guidelines

- Use parametrize when testing multiple similar inputs/outputs (same structure, different values)
- Keep each case as a `(input, expected)` tuple for clarity
- Use fixtures for shared setup (e.g. sample docstrings, config)
- Follow project style: type hints on test functions, no `# type: ignore` unless necessary

## Run tests

```bash
pytest
```
