"""Type validation utilities for Google-style docstrings.

This module contains functions and classes for validating type annotations in docstrings.

# CUSTOM LICENSE NOTICE FOR GOOGLE DOCSTRING PARSER
#
# Copyright (c) 2025 Vladimir Iglovikov
#
# ⚠️ IMPORTANT LICENSE NOTICE ⚠️
# This package requires a PAID LICENSE for all users EXCEPT the Albumentations Team.
#
# - Free for Albumentations Team projects (https://github.com/albumentations-team)
# - Paid license required for all other users
#
# Contact iglovikov@gmail.com to obtain a license before using this software.
# See the LICENSE file for complete details.
"""

from __future__ import annotations

import re

# Generic collections that require type arguments - exactly as they should appear
COLLECTIONS_REQUIRING_ARGS = [
    "Dict",
    "FrozenSet",
    "Generator",
    "Iterable",
    "Iterator",
    "List",
    "Sequence",
    "Set",
    "Tuple",
    "dict",
    "frozenset",
    "list",
    "set",
    "tuple",
]

# Precompiled regex patterns
COLLECTION_TYPE_PATTERN = re.compile(r"([A-Za-z0-9_]+)\[(.*)\]")


class InvalidTypeAnnotationError(ValueError):
    """Error raised when a type annotation is invalid.

    Args:
        type_name (str): The invalid type annotation
        message (str): Error message explaining the issue
    """

    def __init__(self, type_name: str, message: str = "") -> None:
        self.type_name = type_name
        if not message:
            message = f"Invalid type annotation: {type_name}. Collection types must include element types."
        super().__init__(message)


def is_bare_collection(type_name: str) -> bool:
    """Check if the type is a bare collection without arguments.

    Args:
        type_name (str): The type name to check

    Returns:
        bool: True if the type is a bare collection, False otherwise
    """
    return type_name in COLLECTIONS_REQUIRING_ARGS


def parse_nested_type_args(inner_types: str, outer_type: str) -> list[str]:
    """Parse comma-separated type arguments from a complex type.

    Args:
        inner_types (str): The inner part of the complex type (between brackets)
        outer_type (str): The outer type name

    Returns:
        List[str]: List of parsed type arguments
    """
    # Special case for Callable with multiple argument lists
    if outer_type == "Callable" and inner_types.startswith("["):
        return []  # Skip detailed Callable validation

    # Split by commas, handling nested brackets properly
    depth = 0
    current_arg = ""
    args = []

    for char in inner_types:
        if char == "[":
            depth += 1
            current_arg += char
        elif char == "]":
            depth -= 1
            current_arg += char
        elif char == "," and depth == 0:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            current_arg += char

    if current_arg:
        args.append(current_arg.strip())

    return args


def validate_type_annotation(type_name: str | None) -> bool:
    """Validate that type annotations follow proper format.

    Args:
        type_name (str | None): The type annotation to validate

    Returns:
        bool: True if the type annotation is valid

    Raises:
        InvalidTypeAnnotationError: If a collection type doesn't include element types
    """
    if not type_name:
        return True

    # Check for bare collection types without arguments - exact match only
    if is_bare_collection(type_name):
        raise InvalidTypeAnnotationError(
            type_name,
            f"Collection type '{type_name}' must include element types (e.g., {type_name}[str])",
        )

    # Check for nested types in complex type annotations
    bracket_match = COLLECTION_TYPE_PATTERN.search(type_name)
    if not bracket_match:
        return True

    outer_type = bracket_match.group(1)
    inner_types = bracket_match.group(2)

    # Process nested types
    if not inner_types:
        return True

    if "," in inner_types:
        # Handle comma-separated type arguments
        args = parse_nested_type_args(inner_types, outer_type)

        # Validate each argument type
        for arg in args:
            validate_type_annotation(arg)
    else:
        # Single type argument
        validate_type_annotation(inner_types)

    return True


def check_pattern_for_bare_collection(type_string: str, collection: str) -> bool:
    """Check if a collection appears as a bare type in a complex type expression.

    Args:
        type_string (str): The full type string to check
        collection (str): The collection name to look for

    Returns:
        bool: True if the bare collection was found and raised an exception, False otherwise

    Raises:
        InvalidTypeAnnotationError: If a nested collection is used without element types
    """
    # Skip if this collection isn't in the type string
    if collection not in type_string:
        return False

    # Skip if it's properly parameterized (e.g., List[int])
    if f"{collection}[" in type_string:
        return False

    # Patterns to catch:
    # 1. Inside square brackets followed by comma or closing bracket: [List, or [List]
    # 2. After comma followed by space or closing bracket: , List, or , List]
    patterns = [
        rf"\[{collection}[,\]]",  # [List] or [List,
        rf", {collection}[\s,\]]",  # , List or , List]
    ]

    for pattern in patterns:
        if re.search(pattern, type_string):
            raise InvalidTypeAnnotationError(
                collection,
                f"Nested collection type '{collection}' must include element types",
            )

    return False


def check_bracket_args_for_bare_collections(content: str) -> None:
    """Check the content of brackets for bare collection types.

    Args:
        content (str): Content inside brackets to check

    Raises:
        InvalidTypeAnnotationError: If a bare collection is found
    """
    # Split by commas, handling possible spaces
    args = [arg.strip() for arg in content.split(",")]

    for arg in args:
        # Check if any argument is just a bare collection type
        if arg in COLLECTIONS_REQUIRING_ARGS:
            raise InvalidTypeAnnotationError(
                arg,
                f"Nested collection type '{arg}' must include element types",
            )


def check_for_bare_nested_collections(type_string: str) -> None:
    """Check for bare nested collection types in a type string.

    Args:
        type_string (str): The type string to check

    Raises:
        InvalidTypeAnnotationError: If a nested collection type is used without element types
    """
    # First, validate the type itself
    validate_type_annotation(type_string)

    # Look for patterns like Dict[str, List] or Tuple[int, Dict]
    for collection in COLLECTIONS_REQUIRING_ARGS:
        if check_pattern_for_bare_collection(type_string, collection):
            return

    # Also handle the case where we have properly formatted outer brackets
    # but bare collections inside as arguments
    if "[" in type_string and "]" in type_string:
        # Extract the content inside brackets
        bracket_matches = re.findall(r"\[(.*?)\]", type_string)

        for content in bracket_matches:
            check_bracket_args_for_bare_collections(content)
