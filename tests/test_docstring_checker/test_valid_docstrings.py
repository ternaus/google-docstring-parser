"""Test file with valid docstrings.

This file contains properly formatted docstrings to test the docstring checker.
"""
from typing import Dict, List, Any, Union


def simple_function() -> bool:
    """A simple function with a valid docstring."""
    return True


def function_with_args(param1: int, param2: str) -> bool:
    """Function with arguments.

    Args:
        param1 (int): An integer parameter
        param2 (str): A string parameter

    Returns:
        bool: True if successful
    """
    return True


def function_with_sections(param: Dict[str, Any]) -> List[Any]:
    """Function with multiple sections.

    Args:
        param (dict[str, Any]): A dictionary parameter

    Returns:
        list[str]: A list of items

    Raises:
        ValueError: If param is empty

    Example:
        >>> function_with_sections({"key": "value"})
        ["key", "value"]
    """
    if not param:
        raise ValueError("Param cannot be empty")
    return list(param.keys()) + list(param.values())


class ValidClass:
    """A class with valid docstrings.

    This class demonstrates proper docstring formatting for classes and methods.
    """

    def __init__(self, value: int) -> None:
        """Initialize the class.

        Args:
            value (int): An integer value
        """
        self.value = value

    def get_value(self) -> int:
        """Get the stored value.

        Returns:
            int: The stored value
        """
        return self.value

    def set_value(self, new_value: int) -> None:
        """Set a new value.

        Args:
            new_value (int): The new value to store
        """
        self.value = new_value
