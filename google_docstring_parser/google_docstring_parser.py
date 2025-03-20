"""Parser for Google-style docstrings.

This module provides functions to parse Google-style docstrings into structured dictionaries.

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
from typing import Any

from docstring_parser import parse

from google_docstring_parser.type_validation import (
    InvalidTypeAnnotationError,
    check_text_for_bare_collections,
    validate_type_annotation,
)

__all__ = [
    "InvalidTypeAnnotationError",
    "ReferenceFormatError",
    "parse_google_docstring",
]


class ReferenceFormatError(ValueError):
    """Error raised when a reference format is invalid.

    Args:
        code (str): Error code identifying the specific format issue
        line (str): The reference line that caused the error (optional)
    """

    def __init__(self, code: str, line: str = "") -> None:
        messages = {
            "missing_dash": "Multiple references must all start with dash (-)",
            "dash_in_single": "Single reference should not start with dash (-)",
            "missing_colon": f"Invalid reference format, missing colon separator: {line}",
            "empty_description": f"Invalid reference format, empty description: {line}",
        }
        self.code = code
        super().__init__(messages.get(code, "Reference Format Error"))


# Legacy error classes - kept for backward compatibility
class MissingDashError(ReferenceFormatError):
    """Error raised when a multiple reference doesn't start with a dash."""

    def __init__(self) -> None:
        super().__init__("missing_dash")


class DashInSingleReferenceError(ReferenceFormatError):
    """Error raised when a single reference starts with a dash."""

    def __init__(self) -> None:
        super().__init__("dash_in_single")


class MissingColonError(ReferenceFormatError):
    """Error raised when a reference is missing a colon separator."""

    def __init__(self, line: str) -> None:
        super().__init__("missing_colon", line)


class EmptyDescriptionError(ReferenceFormatError):
    """Error raised when a reference has an empty description."""

    def __init__(self, line: str) -> None:
        super().__init__("empty_description", line)


def _extract_sections(docstring: str) -> dict[str, str]:
    """Extract sections from a docstring.

    Args:
        docstring (str): The docstring to extract sections from

    Returns:
        A dictionary mapping section names to their content
    """
    sections: dict[str, str] = {}
    current_section = "Description"
    lines = docstring.split("\n")

    section_content: list[str] = []
    indent_level: int | None = None

    for line in lines:
        if not (stripped := line.strip()) and not section_content:
            continue

        # Check if this is a section header
        if section_match := re.match(r"^([A-Za-z][A-Za-z0-9 ]+):$", stripped):
            # Save previous section content
            if section_content:
                sections[current_section] = "\n".join(section_content).strip()
                section_content = []

            # Set new current section
            current_section = section_match[1]
            indent_level = None
        else:
            # If this is the first content line after a section header, determine indent level
            if indent_level is None and stripped:
                indent_level = len(line) - len(line.lstrip())

            # Add line to current section content, removing one level of indentation
            if stripped or section_content:  # Only add empty lines if we already have content
                if indent_level is not None and line.startswith(" " * indent_level):
                    # Remove one level of indentation
                    processed_line = line[indent_level:]
                    section_content.append(processed_line)
                else:
                    section_content.append(line)

    # Add the last section
    if section_content:
        sections[current_section] = "\n".join(section_content).strip()

    return sections


def _find_separator_colon(content: str) -> int:
    """Find the index of a colon separator that's not part of a URL.

    Args:
        content (str): The content to search in

    Returns:
        The index of the separator colon, or -1 if not found
    """
    # Skip colon in URLs like http://, https://, ftp://, etc.
    content_parts = content.split("://", 1)

    # If there was a protocol in the content, look for a colon after the protocol part
    if len(content_parts) > 1:
        protocol = content_parts[0]
        rest = content_parts[1]

        # Search for a colon in the part after the protocol
        if ":" in rest:
            return len(protocol) + 3 + rest.index(":")  # 3 is for "://"
        # If no colon in rest, check for a colon before the protocol (in the description)
        if ":" in protocol:
            return protocol.index(":")
    elif ":" in content:
        # No protocol found, just find the first colon
        return content.index(":")

    # No colon found
    return -1


def _parse_reference_line(line: str, *, is_single: bool = False) -> dict[str, str]:
    """Parse a single reference line.

    Args:
        line (str): The line to parse
        is_single (bool): Whether this is a single reference (not part of a list)

    Returns:
        A dictionary with 'description' and 'source' keys

    Raises:
        ReferenceFormatError: If the reference format is invalid
    """
    # Check if single reference has a dash (which it shouldn't)
    if is_single and line.startswith("-"):
        raise ReferenceFormatError("dash_in_single")

    # Remove dash if present
    content = line[1:].strip() if line.startswith("-") else line

    # Find separator colon
    colon_index = _find_separator_colon(content)

    # If no valid colon found, raise an error
    if colon_index == -1:
        raise ReferenceFormatError("missing_colon", line)

    description = content[:colon_index].strip()
    source = content[colon_index + 1 :].strip()

    # Make sure the description isn't empty
    if not description:
        raise ReferenceFormatError("empty_description", line)

    return {
        "description": description,
        "source": source,
    }


def _parse_references(reference_content: str) -> list[dict[str, str]]:
    """Parse references section into structured format.

    Args:
        reference_content (str): The content of the References section

    Returns:
        A list of dictionaries with 'description' and 'source' keys

    Raises:
        ReferenceFormatError: If the reference format is invalid
    """
    references: list[dict[str, str]] = []
    lines = [line.strip() for line in reference_content.strip().split("\n") if line.strip()]

    # Handle empty reference content
    if not lines:
        return references

    # If we have multiple lines, all should start with dash
    if len(lines) > 1:
        if not all(line.startswith("-") for line in lines):
            raise ReferenceFormatError("missing_dash")

        # Process each line in the multi-line case using list comprehension
        references.extend(_parse_reference_line(line) for line in lines)
    else:
        # Single reference case
        references.append(_parse_reference_line(lines[0], is_single=True))

    return references


def _process_args_section(args: list[dict[str, str | None]], sections: dict[str, str], *, validate_types: bool) -> None:
    """Process and validate the Args section of a docstring.

    Args:
        args (list[dict[str, str | None]]): A list of dictionaries containing information about the arguments.
        sections (dict[str, str]): A dictionary mapping section names to their content.
        validate_types (bool): Whether to validate type annotations.

    Raises:
        InvalidTypeAnnotationError: If a type annotation is invalid.
    """
    if not validate_types:
        return

    # Check the entire Args section text for potential bare collections
    # This catches issues like "Dict[str, List]" that might not be caught by individual parameter validation
    check_text_for_bare_collections(sections["Args"])

    # Validate type annotations and check for bare nested collections
    for arg in args:
        if arg["type"] and validate_types:
            validate_type_annotation(arg["type"])

            # Check for nested types - if this is a complex type like Dict[str, List],
            # the bare 'List' would be caught here
            if "[" in arg["type"] and "]" in arg["type"]:
                check_text_for_bare_collections(arg["type"])


def _process_returns_section(sections: dict[str, str], *, validate_types: bool) -> list[dict[str, str]]:
    """Process and validate the Returns section of a docstring.

    Args:
        sections (dict[str, str]): A dictionary mapping section names to their content.
        validate_types (bool): Whether to validate type annotations.

    Returns:
        list[dict[str, str]]: A list of dictionaries containing information about the return values.

    Raises:
        InvalidTypeAnnotationError: If a type annotation is invalid.
    """
    if (
        "Returns" not in sections
        or not (returns_lines := sections["Returns"].split("\n"))
        or not (return_match := re.match(r"^(?:(\w+):\s*)?(.*)$", returns_lines[0].strip()))
        or not (return_desc := return_match[2])
    ):
        return []

    return_type = return_match[1]

    # Check the entire Returns section text for potential bare collections
    if validate_types:
        check_text_for_bare_collections(sections["Returns"])

    if return_type and validate_types:
        # Validate the return type
        validate_type_annotation(return_type)

        # Check for nested types in return type
        if "[" in return_type and "]" in return_type:
            check_text_for_bare_collections(return_type)

    return [{"type": return_type, "description": return_desc.rstrip()}]


def parse_google_docstring(docstring: str, *, validate_types: bool = True) -> dict[str, Any]:
    """Parse a Google-style docstring into a structured dictionary.

    Args:
        docstring (str): The docstring to parse
        validate_types (bool): Whether to validate type annotations. Default is True.

    Returns:
        A dictionary with parsed docstring sections
    """
    if not docstring:
        return {}

    # Clean up the docstring
    docstring = docstring.strip()

    # Initialize result dictionary with only description
    result: dict[str, Any] = {"Description": ""}

    # Extract sections and parse docstring
    sections = _extract_sections(docstring)
    parsed = parse(docstring)

    # Process description
    if parsed.description:
        result["Description"] = parsed.description.rstrip()

    # Process args (only if present)
    if "Args" in sections and (
        args := [
            {
                "name": arg.arg_name.rstrip() if arg.arg_name is not None else None,
                "type": arg.type_name.rstrip() if arg.type_name is not None else None,
                "description": arg.description.rstrip() if arg.description is not None else None,
            }
            for arg in parsed.params
        ]
    ):
        _process_args_section(args, sections, validate_types=validate_types)
        result["Args"] = args

    # Process returns
    result["Returns"] = _process_returns_section(sections, validate_types=validate_types)

    # Process references section
    for ref_section in ["References", "Reference"]:
        if ref_section in sections:
            result[ref_section] = _parse_references(sections[ref_section])
            # Don't add this section to the general sections mapping later
            sections.pop(ref_section, None)
            break

    # Add other sections directly using dict union
    return result | {
        section: content.rstrip()
        for section, content in sections.items()
        if section not in ["Description", "Args", "Returns"]
    }
