"""Tests for the docstring checker tool."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from tools.check_docstrings import (
    _config_keys_match,
    _extract_short_description,
    check_short_description_length,
)


def test_config_keys_match() -> None:
    """Test that DEFAULT_CONFIG and _CONFIG_KEYS stay in sync."""
    assert _config_keys_match(), "DEFAULT_CONFIG and _CONFIG_KEYS must have the same keys"


def test_mutually_exclusive_type_consistency_flags(tmp_path: Path) -> None:
    """Test that --check-type-consistency and --no-check-type-consistency cannot be used together."""
    test_file = tmp_path / "test.py"
    test_file.write_text('"""Module."""\ndef foo(): pass\n')

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            str(test_file),
            "--check-type-consistency",
            "--no-check-type-consistency",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "not allowed with" in result.stderr


def test_valid_docstrings() -> None:
    """Test that valid docstrings pass the checker."""
    # Create a temporary directory with only the valid file
    valid_dir = Path(__file__).parent

    # Run the checker on the directory with only the valid file
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            str(valid_dir),
            "--exclude-files",
            "test_malformed_docstrings.py,test_check_docstrings.py",
            "--min-short-description-length",
            "0",
        ],
        capture_output=True,
        text=True,
    )

    # Check that the command succeeded
    assert result.returncode == 0, f"Checker failed on valid docstrings: {result.stdout}"
    assert not result.stdout or "All docstrings parsed successfully" in result.stdout, f"Unexpected output for valid docstrings: {result.stdout}"


def test_malformed_docstrings() -> None:
    """Test that malformed docstrings are detected."""
    malformed_file = Path(__file__).parent / "test_malformed_docstrings.py"

    # Run the checker on the malformed file
    result = subprocess.run(
        [sys.executable, "-m", "tools.check_docstrings", str(malformed_file), "--verbose"],
        capture_output=True,
        text=True,
    )

    # Check that the command failed
    assert result.returncode == 1, "Checker should fail on malformed docstrings"

    # Check that the output contains error messages
    assert "Unclosed parenthesis" in result.stdout, "Should detect unclosed parenthesis"
    assert "__init__" in result.stdout, "Should detect issues in class methods"


def test_require_param_types() -> None:
    """Test that the --require-param-types flag works."""
    malformed_file = Path(__file__).parent / "test_malformed_docstrings.py"

    # Run the checker with --require-param-types
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            str(malformed_file),
            "--require-param-types",
            "--verbose",
        ],
        capture_output=True,
        text=True,
    )

    # Check that the command failed
    assert result.returncode == 1, "Checker should fail when types are required"

    # Check that the output contains missing type errors
    assert "Parameter 'param1' is missing a type" in result.stdout, "Should report which parameter is missing a type"


def test_verbose_output() -> None:
    """Test that the --verbose flag produces more detailed output."""
    malformed_file = Path(__file__).parent / "test_malformed_docstrings.py"

    # Run the checker with --verbose
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            str(malformed_file),
            "--verbose",
        ],
        capture_output=True,
        text=True,
    )

    # Check that the command failed
    assert result.returncode == 1, "Checker should fail on malformed docstrings"

    # Check that the output contains checking messages
    assert "Checking" in result.stdout, "Verbose output should include 'Checking' messages"


def test_config_from_pyproject_toml() -> None:
    """Test that the checker correctly reads configuration from pyproject.toml."""
    # Run the checker with no arguments but with verbose flag to see the configuration
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            "--verbose",
        ],
        capture_output=True,
        text=True,
    )

    # Check the output for configuration values
    assert "Configuration:" in result.stdout, "Should show configuration"

    # Check that it reads the paths from pyproject.toml
    assert "Paths: ['google_docstring_parser', 'tools']" in result.stdout, "Should read paths from pyproject.toml"

    # Check that it reads require_param_types from pyproject.toml
    assert "Require parameter types: True" in result.stdout, "Should read require_param_types from pyproject.toml"

    # Check that it reads exclude_files from pyproject.toml
    assert "Exclude files: ['test_malformed_docstrings.py']" in result.stdout, "Should read exclude_files from pyproject.toml"

    # Check that it reads min_short_description_length from pyproject.toml
    assert "Min short description length: 50" in result.stdout
    assert "Max short description length:" in result.stdout


def test_missing_param_types_in_real_code() -> None:
    """Test that the checker detects missing parameter types in a real file with missing types."""
    # Create a temporary file with a missing parameter type
    temp_dir = Path(__file__).parent
    temp_file = temp_dir / "temp_missing_type.py"

    try:
        # Write a file with a missing parameter type
        with open(temp_file, "w") as f:
            f.write('''
"""Test module with missing parameter type."""

def function_with_missing_type(param1):
    """Function with a missing parameter type.

    Args:
        param1: Parameter without a type

    Returns:
        None
    """
    return None
''')

        # Run the checker on the temporary file with require_param_types
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.check_docstrings",
                str(temp_file),
                "--require-param-types",
                "--verbose",
            ],
            capture_output=True,
            text=True,
        )

        # Check that the command failed
        assert result.returncode == 1, "Checker should fail when types are required"

        # Check that the output contains missing type errors
        assert "Parameter 'param1' is missing a type" in result.stdout, "Should report which parameter is missing a type"

    finally:
        # Clean up the temporary file
        if temp_file.exists():
            temp_file.unlink()


@pytest.mark.parametrize(
    "code,expected_count,expected_message",
    [
        (
            '''
"""Test module with one error."""

def function_with_one_error(param1):
    """Function with a missing parameter type.

    Args:
        param1: Parameter without a type

    Returns:
        None
    """
    return None
''',
            1,
            "Found 1 error",
        ),
        (
            '''
"""Test module with multiple errors."""

def function_with_errors(param1, param2):
    """Function with multiple errors.

    Args:
        param1: First parameter without type
        param2: Second parameter without type

    Returns:
        None
    """
    return None

def another_function(param3):
    """Another function with error.

    Args:
        param3: Third parameter without type

    Returns:
        None
    """
    return None
''',
            3,
            "Found 3 errors",
        ),
    ],
)
def test_error_count_reporting(code: str, expected_count: int, expected_message: str, tmp_path: Path) -> None:
    """Test that the error count is reported correctly.

    Args:
        code (str): Python code to test
        expected_count (int): Expected number of errors
        expected_message (str): Expected error message
        tmp_path (Path): Temporary directory fixture
    """
    temp_file = tmp_path / "test_file.py"
    temp_file.write_text(code)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            str(temp_file),
            "--require-param-types",
            "--min-short-description-length",
            "0",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1, "Checker should fail when errors are found"
    assert expected_message in result.stdout, f"Expected error count message '{expected_message}' not found in output"
    assert result.stdout.count("Parameter") == expected_count, f"Expected {expected_count} parameter type errors"


@pytest.mark.parametrize(
    "code,expected_returncode,expected_output",
    [
        # Valid None return
        (
            '''
"""Test module with None return."""

def function_with_none_return():
    """Function returning None.

    Returns:
        None
    """
    return None
''',
            0,
            "",
        ),
        # Valid typed return
        (
            '''
"""Test module with typed return."""

def function_with_typed_return():
    """Function with typed return.

    Returns:
        bool: Success flag
    """
    return True
''',
            0,
            "",
        ),
        # Invalid return format
        (
            '''
"""Test module with invalid return."""

def function_with_invalid_return():
    """Function with invalid return.

    Returns:
        Just some text without type
    """
    return True
''',
            1,
            "Returns section is missing type annotation",
        ),
        # Missing return type
        (
            '''
"""Test module with missing return type."""

def function_with_missing_return_type():
    """Function with missing return type.

    Returns:
        Success flag
    """
    return True
''',
            1,
            "Returns section is missing type annotation",
        ),
    ],
)
def test_returns_validation(code: str, expected_returncode: int, expected_output: str, tmp_path: Path) -> None:
    """Test that the checker validates Returns sections correctly.

    Args:
        code (str): Python code to test
        expected_returncode (int): Expected return code
        expected_output (str): Expected output (empty for success)
        tmp_path (Path): Temporary directory fixture
    """
    temp_file = tmp_path / "test_file.py"
    temp_file.write_text(code)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            str(temp_file),
            "--verbose",
            "--min-short-description-length",
            "0",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == expected_returncode
    if expected_output:
        assert expected_output in result.stdout


def test_no_paths_specified(tmp_path: Path) -> None:
    """Test that the checker handles the case when no paths are specified.

    Args:
        tmp_path (Path): Temporary directory fixture
    """
    # Create a dummy Python file that would cause errors if checked
    test_file = tmp_path / "test_file.py"
    test_file.write_text('''
def missing_docstring_function(param1):
    # This function has no docstring and would fail checks
    return None
''')

    # Create an empty pyproject.toml to test with no configuration
    empty_pyproject = tmp_path / "pyproject.toml"
    empty_pyproject.write_text('''
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"
''')

    # Get the path to the module we're testing
    project_root = Path(__file__).parent.parent.parent
    tools_module = project_root / "tools" / "check_docstrings.py"

    # Set up environment so imports work
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    # Run the checker with the configuration
    result = subprocess.run(
        [
            sys.executable,
            str(tools_module),
        ],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )

    # Check that the command succeeds (exits with code 0)
    assert result.returncode == 0, f"Checker should succeed when no paths are specified, got stdout: {result.stdout}, stderr: {result.stderr}"

    # Check that the output contains the expected message
    assert "No paths specified for checking" in result.stdout, "Should show message about no paths specified"


def test_configured_paths(tmp_path: Path) -> None:
    """Test that the checker uses paths configured in pyproject.toml.

    Args:
        tmp_path (Path): Temporary directory fixture
    """
    # Create a directory structure
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    # Create a file with an error in the src directory
    src_file = src_dir / "file.py"
    src_file.write_text('''
def function_with_error(param1):
    """Function with missing parameter type.

    Args:
        param1: Parameter without a type

    Returns:
        None
    """
    return None
''')

    # Create another file outside of src directory
    other_file = tmp_path / "other.py"
    other_file.write_text('''
def another_function(param1):
    """Function with missing parameter type.

    Args:
        param1: Parameter without a type

    Returns:
        None
    """
    return None
''')

    # Create a pyproject.toml that only includes the src directory
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('''
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[tool.docstring_checker]
paths = ["src"]
require_param_types = true
''')

    # Get the path to the module we're testing
    project_root = Path(__file__).parent.parent.parent
    tools_module = project_root / "tools" / "check_docstrings.py"

    # Copy the google_docstring_parser module to the tmp_path for imports to work
    # This is a simplified approach for testing - we'll use PYTHONPATH to make imports work
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    # Run the checker with the configuration
    result = subprocess.run(
        [
            sys.executable,
            str(tools_module),
            "--verbose",
        ],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )

    # It should fail because the src/file.py has a docstring error
    assert result.returncode == 1, f"Checker should fail when errors are found, output: {result.stdout}, error: {result.stderr}"

    # The error should be about the file in src, not the one outside
    # Use os.path.join to create a platform-specific path for comparison
    # or check for path components separately to be platform-agnostic
    assert "src" in result.stdout and "file.py" in result.stdout, f"Error should be from src/file.py, got stdout: {result.stdout}, stderr: {result.stderr}"
    assert "other.py" not in result.stdout, "Error should not include other.py"
    assert "Parameter 'param1' is missing a type" in result.stdout, "Should detect missing parameter type"


def test_empty_paths_list(tmp_path: Path) -> None:
    """Test that explicitly setting empty paths list in pyproject.toml behaves the same as no paths.

    Args:
        tmp_path (Path): Temporary directory fixture
    """
    # Create a dummy Python file that would cause errors if checked
    test_file = tmp_path / "test_file.py"
    test_file.write_text('''
def missing_docstring_function(param1):
    # This function has no docstring and would fail checks
    return None
''')

    # Create a pyproject.toml with an explicit empty paths list
    empty_pyproject = tmp_path / "pyproject.toml"
    empty_pyproject.write_text('''
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[tool.docstring_checker]
paths = []
''')

    # Get the path to the module we're testing
    project_root = Path(__file__).parent.parent.parent
    tools_module = project_root / "tools" / "check_docstrings.py"

    # Set up environment so imports work
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    # Run the checker with the configuration
    result = subprocess.run(
        [
            sys.executable,
            str(tools_module),
            "--verbose",
        ],
        cwd=str(tmp_path),
        env=env,
        capture_output=True,
        text=True,
    )

    # Check that the command succeeds (exits with code 0)
    assert result.returncode == 0, f"Checker should succeed when empty paths list is specified, got stdout: {result.stdout}, stderr: {result.stderr}"

    # Check that the output contains the expected message
    assert "No paths specified for checking" in result.stdout, "Should show message about no paths specified"

    # Check that it shows the empty paths in the configuration output
    assert "Paths: []" in result.stdout, "Should show empty paths list in configuration"


@pytest.mark.parametrize(
    "description,expected",
    [
        ("", ""),
        ("One line.", "One line."),
        ("First line.\n\nSecond para.", "First line."),
        ("Line one.\nLine two.\n\nSecond para.", "Line one. Line two."),
        # Multiple blank lines between paragraphs
        ("Para one.\n\n\n\nPara two.", "Para one."),
        # Whitespace-only line counts as blank
        ("Para one.\n   \n\t\nPara two.", "Para one."),
        # Single newline (no blank) - same paragraph
        ("Line one.\nLine two.", "Line one. Line two."),
        # Leading/trailing whitespace stripped
        ("  \n  First para.  \n\n  Second.", "First para."),
        ("  Only line.  ", "Only line."),
        # Multiple sentences in first paragraph
        (
            "First sentence. Second sentence. Third sentence.\n\nMore below.",
            "First sentence. Second sentence. Third sentence.",
        ),
        # Tab and mixed whitespace normalized to single space
        ("Word1\t\tWord2\nWord3", "Word1 Word2 Word3"),
        # Empty after strip
        ("   \n\n   ", ""),
        # Only first paragraph when multiple
        (
            "A. B. C.\n\nD. E.\n\nF.",
            "A. B. C.",
        ),
    ],
)
def test_extract_short_description(description: str, expected: str) -> None:
    """Test that short description is first paragraph (up to first blank line)."""
    assert _extract_short_description(description) == expected


@pytest.mark.parametrize(
    "parsed,min_length,max_length,expected_errors",
    [
        (
            {"Description": "Short."},
            50,
            0,
            ["Short description too short (6 chars, min 50): 'Short.'"],
        ),
        (
            {"Description": "A" * 49},
            50,
            0,
            ["Short description too short (49 chars, min 50): 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA'"],
        ),
        ({"Description": "A" * 50}, 50, 0, []),
        ({"Description": "A" * 60}, 50, 0, []),
        ({"Description": ""}, 50, 0, []),
        ({}, 50, 0, []),
        ({"Description": "Short."}, 0, 0, []),
        ({"Description": "Short."}, 5, 0, []),
        ({"Description": "Short."}, 6, 0, []),
        (
            {"Description": "Short."},
            7,
            0,
            ["Short description too short (6 chars, min 7): 'Short.'"],
        ),
        (
            {"Description": "First line.\n\nSecond paragraph."},
            50,
            0,
            ["Short description too short (11 chars, min 50): 'First line.'"],
        ),
        # First paragraph = up to blank line (multi-line)
        (
            {"Description": "First line. More.\nSecond line of para.\n\nSecond para."},
            0,
            0,
            [],
        ),
        # Max length
        (
            {"Description": "A" * 161},
            0,
            160,
            ["Short description too long (161 chars, max 160): 'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA...'"],
        ),
        ({"Description": "A" * 160}, 0, 160, []),
        ({"Description": "A" * 50}, 50, 160, []),
        (
            {"Description": "Short."},
            50,
            5,
            [
                "Short description too short (6 chars, min 50): 'Short.'",
                "Short description too long (6 chars, max 5): 'Short.'",
            ],
        ),
    ],
)
def test_check_short_description_length(
    parsed: dict[str, Any],
    min_length: int,
    max_length: int,
    expected_errors: list[str],
) -> None:
    """Test that check_short_description_length validates correctly.

    Args:
        parsed (dict): Parsed docstring dict with Description key
        min_length (int): Minimum length threshold
        max_length (int): Maximum length threshold (0 to disable)
        expected_errors (list[str]): Expected error messages
    """
    # Handle parametrize passing string for the invalid test case
    if isinstance(parsed, str):
        parsed = {"Description": parsed}
    result = check_short_description_length(parsed, min_length, max_length)
    assert result == expected_errors


@pytest.mark.parametrize(
    "code,min_len,max_len,expected_returncode,expected_in_output",
    [
        # Short description too short - fails ("X." = 2 chars < min 5)
        (
            '''
"""Test module."""

def foo():
    """X.

    Returns:
        None
    """
    pass
''',
            5,
            0,
            1,
            "Short description too short",
        ),
        # Short description OK (multi-line first para)
        (
            '''
"""Test module."""

def foo():
    """First sentence. Second sentence for more context. Third sentence if needed.

    Returns:
        None
    """
    pass
''',
            50,
            160,
            0,
            "",
        ),
        # Short description too long - fails (6 chars > max 5)
        (
            '''
"""Test module."""

def foo():
    """Short.

    Returns:
        None
    """
    pass
''',
            0,
            5,
            1,
            "Short description too long",
        ),
        # First paragraph = up to blank line (52 chars, min 50)
        (
            '''
"""Test module."""

def foo():
    """First line. Second line. Third line. More text here.

    Returns:
        None
    """
    pass
''',
            50,
            160,
            0,
            "",
        ),
    ],
)
def test_short_description_integration(
    code: str,
    min_len: int,
    max_len: int,
    expected_returncode: int,
    expected_in_output: str,
    tmp_path: Path,
) -> None:
    """Test short description length in full check_file flow."""

    def run_check() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "tools.check_docstrings",
                str(tmp_path / "test.py"),
                "--min-short-description-length",
                str(min_len),
                "--max-short-description-length",
                str(max_len),
            ],
            capture_output=True,
            text=True,
        )

    (tmp_path / "test.py").write_text(code)
    result = run_check()
    assert result.returncode == expected_returncode
    if expected_in_output:
        assert expected_in_output in result.stdout


@pytest.mark.parametrize(
    "code,expected_returncode,expected_in_output",
    [
        # Param type match - no error
        (
            '''
"""Test module with matching types."""

def foo(x: int) -> str:
    """Function with matching docstring types.

    Args:
        x (int): Param x

    Returns:
        str: Result
    """
    return str(x)
''',
            0,
            "",
        ),
        # Param type mismatch - error
        (
            '''
"""Test module with param type mismatch."""

def foo(x: int) -> str:
    """Function with wrong docstring type.

    Args:
        x (str): Docstring says str, annotation says int

    Returns:
        str: Result
    """
    return str(x)
''',
            1,
            "docstring says 'str' but annotation says 'int'",
        ),
        # Return type mismatch - error
        (
            '''
"""Test module with return type mismatch."""

def foo(x: int) -> str:
    """Function with wrong return type in docstring.

    Args:
        x (int): Param x

    Returns:
        int: Docstring says int, annotation says str
    """
    return str(x)
''',
            1,
            "Returns: docstring says 'int' but annotation says 'str'",
        ),
        # Missing annotation in source - skip (no error)
        (
            '''
"""Test module with no annotations."""

def foo(x):
    """Function with no type annotations in source.

    Args:
        x (int): Param x

    Returns:
        str: Result
    """
    return str(x)
''',
            0,
            "",
        ),
        # self skipped - method with self, only x is compared
        (
            '''
"""Test module with self param."""

def method(self, x: int) -> None:
    """Method with self.

    Args:
        x (int): Param x

    Returns:
        None
    """
    pass
''',
            0,
            "",
        ),
        # pos-only param type mismatch
        (
            '''
"""Test module with pos-only param mismatch."""

def foo(x: int, /, y: str) -> None:
    """Function with pos-only param.

    Args:
        x (str): Docstring says str, annotation says int
        y (str): Correct

    Returns:
        None
    """
    pass
''',
            1,
            "docstring says 'str' but annotation says 'int'",
        ),
        # kw-only param type mismatch
        (
            '''
"""Test module with kw-only param mismatch."""

def foo(x: int, *, y: str) -> None:
    """Function with kw-only param.

    Args:
        x (int): Correct
        y (int): Docstring says int, annotation says str

    Returns:
        None
    """
    pass
''',
            1,
            "docstring says 'int' but annotation says 'str'",
        ),
        # *args type mismatch
        (
            '''
"""Test module with *args type mismatch."""

def foo(*args: int) -> None:
    """Function with varargs.

    Args:
        args (str): Docstring says str, annotation says int

    Returns:
        None
    """
    pass
''',
            1,
            "docstring says 'str' but annotation says 'int'",
        ),
        # Returns string "None" vs annotation str - mismatch detected
        (
            '''
"""Test module with Returns as string None."""

def foo() -> str:
    """Function returning str but docstring says None.

    Returns:
        None
    """
    return "x"
''',
            1,
            "Returns: docstring says 'None' but annotation says 'str'",
        ),
        # Whitespace normalization: tuple[int, str] vs tuple[int,str] - no error
        (
            '''
"""Test module with whitespace in type."""

def foo(x: tuple[int, str]) -> int | None:
    """Function with types that may have different whitespace.

    Args:
        x (tuple[int, str]): Param with spaces in docstring

    Returns:
        int | None: Union with spaces
    """
    return None
''',
            0,
            "",
        ),
    ],
)
def test_check_type_consistency(
    code: str, expected_returncode: int, expected_in_output: str, tmp_path: Path
) -> None:
    """Test that check_type_consistency compares docstring types with annotations.

    Args:
        code (str): Python code to test
        expected_returncode (int): Expected return code
        expected_in_output (str): Expected substring in output (empty for success)
        tmp_path (Path): Temporary directory fixture
    """
    temp_file = tmp_path / "test_file.py"
    temp_file.write_text(code)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "tools.check_docstrings",
            str(temp_file),
            "--check-type-consistency",
            "--min-short-description-length",
            "0",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == expected_returncode
    if expected_in_output:
        assert expected_in_output in result.stdout
