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
        dict[str, str]: A dictionary mapping section names to their content
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
        int: The index of the separator colon, or -1 if not found
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
        dict[str, str]: A dictionary with 'description' and 'source' keys

    Raises:
        ReferenceFormatError: If the reference format is invalid
    """
    # Check if single reference has a dash (which it shouldn't)
    if is_single and line.lstrip().startswith("-"):
        raise ReferenceFormatError("dash_in_single")

    # Remove dash if present
    content = line[1:].strip() if line.lstrip().startswith("-") else line.strip()

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


def _identify_main_reference_lines(lines: list[str]) -> list[str]:
    """Identify lines that are main reference lines vs continuations.

    A line is considered a main reference line if:
    1. It starts with a dash, or
    2. It's the first line, or
    3. It's indented the same or less than the previous reference line and contains a colon

    Args:
        lines (list[str]): List of lines to process

    Returns:
        list[str]: List of main reference lines
    """
    main_ref_lines: list[str] = []

    # Always consider first line as a main reference line
    if not lines:
        return main_ref_lines

    main_ref_lines.append(lines[0])
    prev_indent = len(lines[0]) - len(lines[0].lstrip())

    # Check remaining lines
    for i in range(1, len(lines)):
        line = lines[i]
        line_indent = len(line) - len(line.lstrip())
        is_dashed = line.lstrip().startswith("-")
        has_colon = ":" in line

        if is_dashed:
            # Definitely a main reference
            main_ref_lines.append(line)
            prev_indent = line_indent
        elif line_indent <= prev_indent and has_colon:
            # Same or less indentation than previous with a colon - likely a new reference
            main_ref_lines.append(line)
            prev_indent = line_indent

    return main_ref_lines


def _process_single_reference(main_line: str, all_lines: list[str]) -> dict[str, str]:
    """Process a single reference entry.

    Args:
        main_line (str): The main reference line
        all_lines (list[str]): All lines in the reference section

    Returns:
        dict[str, str]: A dictionary containing the reference information with 'description' and 'source' keys
    """
    # Single reference - should not have a dash
    if main_line.lstrip().startswith("-"):
        raise ReferenceFormatError("dash_in_single")

    # Process all lines for this reference
    ref_lines = [main_line]
    line_indent = len(main_line) - len(main_line.lstrip())

    # Add continuation lines if any
    main_index = all_lines.index(main_line)
    for j in range(main_index + 1, len(all_lines)):
        next_line = all_lines[j]
        next_indent = len(next_line) - len(next_line.lstrip())
        if next_indent > line_indent:  # More indented means continuation
            ref_lines.append(next_line)

    # Join all lines for this reference
    reference_text = " ".join(line.strip() for line in ref_lines)

    # Parse the reference
    return _parse_reference_line(reference_text, is_single=True)


def _process_multiple_references(lines: list[str]) -> list[dict[str, str]]:
    """Process multiple reference entries.

    Args:
        lines (list[str]): Lines containing multiple references

    Returns:
        list[dict[str, str]]: List of dictionaries containing reference information, each with 'description'
            and 'source' keys
    """
    references = []
    i = 0

    while i < len(lines):
        current_line = lines[i].rstrip()

        # Check if this is a new reference (starts with dash)
        if current_line.lstrip().startswith("-"):
            # Reference with dash - determine if multiline by looking ahead
            current_indent = len(current_line) - len(current_line.lstrip())
            ref_lines = [current_line]

            # Look ahead for continuation lines (properly indented, no dash)
            j = i + 1
            while j < len(lines):
                next_line = lines[j].rstrip()
                next_indent = len(next_line) - len(next_line.lstrip())

                # If next line is indented more than current and doesn't start with dash,
                # it's a continuation of the current reference description
                if next_indent > current_indent and not next_line.lstrip().startswith("-"):
                    ref_lines.append(next_line)
                    j += 1
                else:
                    break

            # Join all lines for this reference and parse
            full_ref_text = " ".join(line.strip() for line in ref_lines)
            ref = _parse_reference_line(full_ref_text)
            references.append(ref)

            # Skip the lines we processed
            i = j - 1
        else:
            # A non-dashed line in a multi-reference context is an error
            # (unless it's a continuation line, which we've already handled)
            raise ReferenceFormatError("missing_dash")

        i += 1

    return references


def _parse_references(reference_content: str) -> list[dict[str, str]]:
    """Parse references section content.

    Args:
        reference_content (str): Content of the references section

    Returns:
        list[dict[str, str]]: List of dictionaries containing reference information, each with
            'description' and 'source' keys
    """
    references: list[dict[str, str]] = []
    lines = [line for line in reference_content.strip().split("\n") if line.strip()]

    # Handle empty reference content
    if not lines:
        return references

    # Identify main reference lines (not continuations)
    main_ref_lines = _identify_main_reference_lines(lines)

    # Validate that multiple references all have dashes
    if len(main_ref_lines) > 1 and not all(line.lstrip().startswith("-") for line in main_ref_lines):
        raise ReferenceFormatError("missing_dash")

    # Handle different cases based on number of references
    if len(main_ref_lines) == 1:
        # Single reference case
        references.append(_process_single_reference(main_ref_lines[0], lines))
    else:
        # Multiple references case
        references = _process_multiple_references(lines)

    return references


def _is_continuation_line(line: str, all_lines: list[str]) -> bool:
    """Check if a line is a continuation of a previous line.

    Args:
        line (str): The line to check
        all_lines (list[str]): All lines in the section

    Returns:
        bool: True if the line is a continuation line, False otherwise
    """
    line_index = all_lines.index(line)
    if line_index == 0:
        return False

    current_indent = len(line) - len(line.lstrip())
    prev_line = all_lines[line_index - 1]
    prev_indent = len(prev_line) - len(prev_line.lstrip())

    return current_indent > prev_indent and not line.lstrip().startswith("-")


def _process_args_section(args: list[dict[str, str | None]], *, validate_types: bool) -> None:
    """Process the Args section of a docstring.

    Args:
        args (list[dict[str, str | None]]): List of argument dictionaries
        validate_types (bool): Whether to validate type annotations

    Returns:
        None
    """
    if not validate_types:
        return

    # Validate type annotations and check for bare nested collections
    for arg in args:
        if arg["type"] and validate_types:
            validate_type_annotation(arg["type"])

            # Check for nested types - if this is a complex type like Dict[str, List],
            # the bare 'List' would be caught here
            if "[" in arg["type"] and "]" in arg["type"]:
                check_text_for_bare_collections(arg["type"])


def _process_returns_section(sections: dict[str, str], *, validate_types: bool) -> dict[str, str]:
    """Process the Returns section of a docstring.

    Args:
        sections (dict[str, str]): Dictionary of docstring sections
        validate_types (bool): Whether to validate type annotations

    Returns:
        dict[str, str]: Dictionary containing 'type' and 'description' keys for the return value
    """
    if (
        "Returns" not in sections
        or not (returns_lines := sections["Returns"].split("\n"))
        or not (return_match := re.match(r"^(?:([^:]+):\s*)?(.*)$", returns_lines[0].strip()))
    ):
        return {}

    return_type = return_match[1]
    return_desc = return_match[2].strip()

    # If type exists -> description must exist
    # If type is None -> description must be empty
    if (return_type and not return_desc) or (not return_type and return_desc):
        return {}

    if return_type and validate_types:
        # Validate the return type
        validate_type_annotation(return_type)

        # Check for nested types in return type
        if "[" in return_type and "]" in return_type:
            check_text_for_bare_collections(return_type)

    return {"type": return_type, "description": return_desc.rstrip()}


def parse_google_docstring(docstring: str, *, validate_types: bool = True) -> dict[str, Any]:
    """Parse a Google-style docstring.

    Args:
        docstring (str): The docstring to parse
        validate_types (bool): Whether to validate type annotations

    Returns:
        dict[str, Any]: Dictionary containing the parsed docstring information with the following keys:
            - Description (str): The main description of the function/class
            - Args (list[dict[str, str | None]], optional): List of argument dictionaries
            - Returns (dict[str, str], optional): Return type and description
            - References/Reference (list[dict[str, str]], optional): List of references
            - Other sections are included as is
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
        _process_args_section(args, validate_types=validate_types)
        result["Args"] = args

    # Process returns only if present
    if "Returns" in sections:
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
