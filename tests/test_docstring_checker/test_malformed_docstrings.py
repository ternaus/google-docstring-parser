"""Test file with malformed docstrings.

This file contains intentionally malformed docstrings to test the docstring checker.
"""
from typing import Dict, Any


def missing_arg_type() -> bool:
    """Function with missing argument type.

    Args:
        param1: This parameter is missing a type
        param2 (int): This parameter has a type

    Returns:
        bool: True if successful
    """
    return True


def malformed_section() -> bool:
    """Function with malformed section.

    Args:
        param1 (str): A string parameter

    BadSection:
        This section has an invalid name

    Returns:
        bool: True if successful
    """
    return True


def unclosed_parenthesis() -> Dict[str, Any]:
    """Function with unclosed parenthesis in type.

    Args:
        param1 (list[str): Parameter with unclosed bracket in type

    Returns:
        dict: A dictionary
    """
    return {}


class MalformedClass:
    """Class with malformed docstring.

    This class has a malformed docstring in one of its methods.
    """

    def __init__(self, value: Any) -> None:
        """Initialize the class.

        Args:
            value (int: Missing closing parenthesis in type
        """
        self.value = value

    def good_method(self, param: str) -> int:
        """This method has a good docstring.

        Args:
            param (str): A string parameter

        Returns:
            int: The length of the parameter
        """
        return len(param)


def multiple_issues() -> None:
    """Function with multiple issues.

    Args:
        param1: Missing type
        param2 (dict[str, list[int): Unclosed bracket
        param3 (invalid type): Invalid type

    Returns:
        Something
    """
    return None
