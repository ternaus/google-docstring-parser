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

__all__ = ["parse_google_docstring"]


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


def parse_google_docstring(docstring: str) -> dict[str, Any]:
    """Parse a Google-style docstring into a structured dictionary.

    Args:
        docstring (str): The docstring to parse

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
        result["Args"] = args

    # Process returns
    if (
        "Returns" in sections
        and (returns_lines := sections["Returns"].split("\n"))
        and (return_match := re.match(r"^(?:(\w+):\s*)?(.*)$", returns_lines[0].strip()))
        and (return_desc := return_match[2])
    ):
        result["Returns"] = [{"type": return_match[1], "description": return_desc.rstrip()}]
    else:
        result["Returns"] = []

    # Add other sections directly using dict union
    return result | {
        section: content.rstrip()
        for section, content in sections.items()
        if section not in ["Description", "Args", "Returns"]
    }
