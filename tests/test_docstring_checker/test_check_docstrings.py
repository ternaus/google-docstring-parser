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
    assert "BadSection" in result.stdout, "Should detect unknown section headers"
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
