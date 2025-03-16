"""Tests for the docstring checker tool."""

import os
import subprocess
import sys
from pathlib import Path

import pytest


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
            "test_malformed_docstrings.py,test_check_docstrings.py"
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
