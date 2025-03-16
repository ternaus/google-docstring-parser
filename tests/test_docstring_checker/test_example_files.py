"""Tests for checking docstrings in the example files."""

from pathlib import Path

import pytest

from tools.check_docstrings import check_file, scan_directory


def test_valid_docstrings_file() -> None:
    """Test that the valid docstrings file passes the checker."""
    valid_file = Path(__file__).parent / "test_valid_docstrings.py"
    errors = check_file(valid_file, require_param_types=False, verbose=True)
    assert not errors, f"Found errors in valid docstrings file: {errors}"


def test_malformed_docstrings_file() -> None:
    """Test that the malformed docstrings file fails the checker."""
    malformed_file = Path(__file__).parent / "test_malformed_docstrings.py"
    errors = check_file(malformed_file, require_param_types=False, verbose=True)

    # Check that we found the expected errors
    assert errors, "No errors found in malformed docstrings file"

    # Check for specific error types
    error_text = "\n".join(errors)
    assert "Unknown section header" in error_text
    assert "Unclosed parenthesis" in error_text


def test_require_param_types_on_malformed_file() -> None:
    """Test that requiring parameter types finds additional errors."""
    malformed_file = Path(__file__).parent / "test_malformed_docstrings.py"

    # First check without requiring types
    errors_without_types = check_file(malformed_file, require_param_types=False, verbose=True)

    # Then check with requiring types
    errors_with_types = check_file(malformed_file, require_param_types=True, verbose=True)

    # Should find more errors when requiring types
    assert len(errors_with_types) > len(errors_without_types)

    # Check for missing type errors
    missing_type_errors = [e for e in errors_with_types if "missing a type" in e]
    assert missing_type_errors, "No missing type errors found when requiring types"


def test_scan_directory() -> None:
    """Test scanning a directory for docstring issues."""
    test_dir = Path(__file__).parent

    # Scan with excluding the malformed file
    errors_excluding_malformed = scan_directory(
        test_dir,
        exclude_files=["test_malformed_docstrings.py"],
        require_param_types=False,
        verbose=True,
    )

    # Scan without excluding the malformed file
    errors_including_malformed = scan_directory(
        test_dir,
        exclude_files=[],
        require_param_types=False,
        verbose=True,
    )

    # Should find more errors when including the malformed file
    assert len(errors_including_malformed) > len(errors_excluding_malformed)


@pytest.mark.parametrize(
    "filename,require_types,expected_error_count",
    [
        ("test_valid_docstrings.py", False, 0),
        ("test_valid_docstrings.py", True, 0),  # Valid file should pass even with strict checking
        ("test_malformed_docstrings.py", False, 3),  # At least 3 errors without type checking
        ("test_malformed_docstrings.py", True, 5),   # More errors with type checking
    ],
)
def test_parametrized_file_checks(filename: str, require_types: bool, expected_error_count: int) -> None:
    """Test checking different files with different settings."""
    file_path = Path(__file__).parent / filename
    errors = check_file(file_path, require_param_types=require_types, verbose=True)

    # Check that we found at least the expected number of errors
    assert len(errors) >= expected_error_count, (
        f"Expected at least {expected_error_count} errors in {filename} "
        f"with require_types={require_types}, but found {len(errors)}"
    )
