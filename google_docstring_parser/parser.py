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

import re


def _extract_sections(docstring: str) -> dict:
    """Extract sections from a docstring.

    Args:
        docstring: The docstring to extract sections from

    Returns:
        A dictionary mapping section names to their content
    """
    sections = {}
    current_section = "description"
    lines = docstring.split("\n")

    section_content = []
    indent_level = None

    for _, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines at the beginning
        if not stripped and not section_content:
            continue

        # Check if this is a section header
        section_match = re.match(r"^(\w+):$", stripped)

        if section_match:
            # Save previous section content
            if section_content:
                sections[current_section] = "\n".join(section_content).strip()
                section_content = []

            # Set new current section
            current_section = section_match.group(1).lower()
            indent_level = None
        else:
            # If this is the first content line after a section header, determine indent level
            if indent_level is None and stripped:
                indent_level = len(line) - len(line.lstrip())

            # Add line to current section content
            if stripped or section_content:  # Only add empty lines if we already have content
                section_content.append(line)

    # Add the last section
    if section_content:
        sections[current_section] = "\n".join(section_content).strip()

    return sections


def parse_google_docstring(docstring: str) -> dict:
    """Parse a Google-style docstring into a structured dictionary.

    Args:
        docstring: The docstring to parse

    Returns:
        A dictionary with parsed docstring sections
    """
    if not docstring:
        return {}

    # Clean up the docstring
    docstring = docstring.strip()

    # Initialize result dictionary
    result = {
        "description": "",
        "args": [],
    }

    # Extract sections
    sections = _extract_sections(docstring)

    # Process description
    if "description" in sections:
        result["description"] = sections["description"]

    # Process args
    if "args" in sections:
        result["args"] = _parse_args_section(sections["args"])

    # Add other sections directly
    result.update({section: content for section, content in sections.items() if section not in ["description", "args"]})

    return result


def _parse_args_section(args_text: str) -> list:
    """Parse the Args section of a Google-style docstring.

    Args:
        args_text: The text content of the Args section

    Returns:
        A list of dictionaries, each containing name, type, and description of a parameter
    """
    args = []
    current_arg = None
    current_description_lines = []
    indent_level = None

    # Split the text into lines and process each line
    lines = args_text.split("\n")

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line defines a new parameter
        param_match = re.match(r"^(\w+)(?:\s+\(([^)]+)\))?:\s*(.*)$", stripped)

        if param_match:
            # Save the previous parameter if there is one
            if current_arg is not None:
                description = "\n".join(current_description_lines).strip()
                args.append(
                    {
                        "name": current_arg["name"],
                        "type": current_arg["type"],
                        "description": description,
                    },
                )

            # Extract parameter information
            name = param_match.group(1)
            type_str = param_match.group(2)  # Could be None
            description_start = param_match.group(3)

            # Set up the new current parameter
            current_arg = {
                "name": name,
                "type": type_str,
                "description": "",
            }

            current_description_lines = [description_start] if description_start else []

            # Determine the indentation level for continuation lines
            if i < len(lines) - 1:
                next_line = lines[i + 1]
                if next_line.strip():
                    indent_level = len(next_line) - len(next_line.lstrip())

        elif current_arg is not None:
            # This is a continuation of the current parameter's description
            # Check if this line has more indentation than the parameter definition
            line_indent = len(line) - len(line.lstrip())

            if indent_level is None or line_indent >= indent_level:
                current_description_lines.append(stripped)

    # Add the last parameter
    if current_arg is not None:
        description = "\n".join(current_description_lines).strip()
        args.append(
            {
                "name": current_arg["name"],
                "type": current_arg["type"],
                "description": description,
            },
        )

    return args
