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
from re import Match
from typing import AnyStr

# Generic collections that require type arguments - exactly as they should appear
COLLECTIONS_REQUIRING_ARGS = (
    # Lowercase versions
    "dict",
    "list",
    "set",
    "frozenset",
    "tuple",
    "type",
    "iterable",
    "iterator",
    "generator",
    "sequence",
    "literal",
    "typing.dict",
    "typing.list",
    "typing.set",
    "typing.frozenset",
    "typing.tuple",
    "typing.type",
    "typing.iterable",
    "typing.iterator",
    "typing.generator",
    "typing.sequence",
    "typing.literal",
    # Capitalized versions (for backward compatibility)
    "Dict",
    "List",
    "Set",
    "FrozenSet",
    "Tuple",
    "Type",
    "Iterable",
    "Iterator",
    "Generator",
    "Sequence",
    "Literal",
    "typing.Dict",
    "typing.List",
    "typing.Set",
    "typing.FrozenSet",
    "typing.Tuple",
    "typing.Type",
    "typing.Iterable",
    "typing.Iterator",
    "typing.Generator",
    "typing.Sequence",
    "typing.Literal",
)

# Precompiled regex patterns
COLLECTION_TYPE_PATTERN = re.compile(r"([A-Za-z0-9_]+)\[(.*)\]")

# Special characters for bracket handling
OPEN_BRACKET = "["
CLOSE_BRACKET = "]"
OPEN_PAREN = "("
CLOSE_PAREN = ")"
OPEN_BRACE = "{"
CLOSE_BRACE = "}"

# Constants for validation
MAX_WORD_COUNT_FOR_TYPE = 3
NESTING_KEYWORD = "with"


class InvalidTypeAnnotationError(ValueError):
    """Error raised when a type annotation is invalid.

    Args:
        message (str): The error message.
    """

    BARE_COLLECTION = "Collection must include element types"
    INVALID_BRACKET_USAGE = "Collection must be followed by type arguments in brackets"
    INVALID_NESTED_TYPE = "Invalid nested type: {}"

    def __init__(self, message: str) -> None:
        """Initialize the error with a message.

        Args:
            message (str): The error message.

        Returns:
            None
        """
        self.message = message
        super().__init__(message)


class BracketValidationError(ValueError):
    """Error raised when brackets in a type annotation are not balanced or mismatched.

    Contains specific error types for different bracket validation issues.
    """

    UNBALANCED_CLOSING = "Closing bracket without matching opening bracket"
    MISMATCHED_PAIR = "Mismatched bracket pair"
    UNCLOSED_BRACKETS = "Unclosed brackets in type annotation"
    COLLECTION_MUST_HAVE_ARGS = "Collection must include element types"
    WRONG_BRACKET_TYPE = "Collection '{}' must use square brackets for type arguments, not '{}'"

    def __init__(self, error_type: str) -> None:
        """Initialize with a specific error type.

        Args:
            error_type (str): One of the predefined error types.

        Returns:
            None
        """
        super().__init__(error_type)


def is_collection_type(type_name: str) -> bool:
    """Check if a type name is a known collection type.

    Args:
        type_name (str): The type name to check.

    Returns:
        bool: True if the type is a collection, False otherwise
    """
    return type_name in COLLECTIONS_REQUIRING_ARGS


def is_bare_collection(type_name: str) -> bool:
    """Check if a type name is a bare collection without element types.

    Args:
        type_name (str): The type name to check.

    Returns:
        bool: True if the type is a bare collection, False otherwise
    """
    return is_collection_type(type_name) and "[" not in type_name


def validate_type_annotation(type_annotation: str) -> None:
    """Validate a type annotation for proper syntax and collection usage.

    Args:
        type_annotation (str): The type annotation to validate.

    Returns:
        None

    Raises:
        InvalidTypeAnnotationError: If the type annotation is invalid.
    """
    if not type_annotation:
        return

    # Check for bare collection types without arguments - exact match only
    if is_bare_collection(type_annotation):
        error_msg = f"Collection '{type_annotation}' must include element types (e.g., {type_annotation}[str])"
        raise InvalidTypeAnnotationError(error_msg)

    # Check for nested types in complex type annotations
    _validate_type_declaration(type_annotation)


def check_text_for_bare_collections(text: str) -> None:
    """Check text for bare collection types that require brackets with arguments.

    This function examines a section of text, looking for collection types that
    are used without proper type arguments in brackets (e.g., 'List' without '[int]').

    Args:
        text (str): The text to check for bare collection types.

    Returns:
        None

    Raises:
        InvalidTypeAnnotationError: If a collection requiring arguments is used
            without proper bracket notation.
    """
    # Extract type declarations from the text first
    type_pattern = r"\(\s*([^)]+)\s*\):"  # Match docstring parameter type declarations
    return_pattern = r"^([A-Za-z0-9_\[\],\s]+):"  # Match return type declarations

    type_matches = re.findall(type_pattern, text)
    return_matches = re.findall(return_pattern, text, re.MULTILINE)

    # For each extracted type, validate it
    for type_decl in type_matches + return_matches:
        # Skip if empty
        if not type_decl.strip():
            continue

        # Validate extracted type
        try:
            validate_type_annotation(type_decl.strip())
        except InvalidTypeAnnotationError:
            # Only re-raise if we're confident this is actually a type annotation
            # This prevents false positives on text that happens to contain collection names
            if _looks_like_type_annotation(type_decl):
                raise

    # Next handle bare collections in the text (not in proper parentheses)
    for collection in COLLECTIONS_REQUIRING_ARGS:
        # Pattern to match bare collection not followed by opening bracket
        # Only match when it appears to be a type (near parentheses or colons)
        pattern = rf"(\(|\s){collection}\s*(?![\[\(\{{])[:\)]"
        matches = list(re.finditer(pattern, text))

        for match in matches:
            # Skip if within string literals
            if _is_within_string_literal(text, match.start()):
                continue

            # Skip if part of a qualified name
            before = text[: match.start()].rstrip()
            if before.endswith("."):
                continue

            # This is a bare collection used as a type
            error_msg = f"Collection '{collection}' must be followed by type arguments in brackets"
            raise InvalidTypeAnnotationError(error_msg)


def _is_within_string_literal(text: str, position: int) -> bool:
    """Check if a position in text is within a string literal.

    Args:
        text (str): The text to check
        position (int): The position to check

    Returns:
        bool: True if the position is within a string literal, False otherwise
    """
    # Count quotes before the position to determine if we're in a string
    single_quotes = text[:position].count("'") % 2
    double_quotes = text[:position].count('"') % 2
    return single_quotes == 1 or double_quotes == 1


def _looks_like_type_annotation(text: str) -> bool:
    """Check if text looks like a type annotation.

    Args:
        text (str): The text to check

    Returns:
        bool: True if the text looks like a type annotation, False otherwise
    """
    # Simple heuristic: contains a collection name and brackets
    for collection in COLLECTIONS_REQUIRING_ARGS:
        if collection in text and any(char in text for char in "[](){}"):
            return True
    return False


def _process_string_literals(text: str) -> tuple[str, list[str]]:
    """Process string literals in text.

    Args:
        text (str): The text to process

    Returns:
        tuple[str, list[str]]: A tuple containing:
            - The processed text with literals replaced by placeholders
            - List of extracted string literals
    """
    # Extract string literals to avoid false positives in brackets
    pattern = r'(?:"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')'
    matches = list(re.finditer(pattern, text))
    result = text
    extracted: list[str] = []

    # Replace each match with a placeholder
    for i, match in enumerate(reversed(matches)):
        placeholder = f"STR_LITERAL_{len(matches) - i - 1}"
        start, end = match.span()
        extracted.insert(0, text[start:end])
        result = result[:start] + placeholder + result[end:]

    return result, extracted


def replace_string_literals(match: Match[AnyStr], literals: list[str]) -> str:
    """Replace string literal placeholders with actual literals.

    Args:
        match (Match[AnyStr]): The regex match object
        literals (list[str]): List of string literals

    Returns:
        str: The text with placeholders replaced by actual literals
    """
    placeholder = str(match.group(0))
    if placeholder.startswith("STR_LITERAL_"):
        idx = int(placeholder.split("_")[-1])
        if idx < len(literals):
            return literals[idx]
    return placeholder


def _tokenize_type_declaration(declaration: str) -> list[str]:
    """Tokenize a type declaration into individual components.

    Args:
        declaration (str): The type declaration to tokenize

    Returns:
        list[str]: List of tokens from the type declaration
    """
    # Process string literals to avoid treating brackets in strings as real brackets
    processed_text, string_literals = _process_string_literals(declaration)

    # Initialize empty list for tokens
    tokens: list[str] = []

    # Define special characters
    special_chars = "[](){},"

    # Process the text character by character
    i = 0
    current_token = ""

    while i < len(processed_text):
        char = processed_text[i]

        # Handle special characters (brackets and comma)
        if char in special_chars:
            # If we have a current token, add it to the list
            if current_token:
                tokens.append(current_token)
                current_token = ""
            # Add the special character as its own token
            tokens.append(char)
        # Handle whitespace as a token separator
        elif char.isspace():
            # If we have a current token, add it to the list
            if current_token:
                tokens.append(current_token)
                current_token = ""
        # Handle regular characters as part of a token
        else:
            current_token += char

        i += 1

    # Add the last token if there is one
    if current_token:
        tokens.append(current_token)

    # Restore string literals in the tokens
    pattern = r"STR_LITERAL_\d+"
    for i, token in enumerate(tokens):
        if re.match(pattern, token):
            tokens[i] = re.sub(pattern, lambda m: replace_string_literals(m, string_literals), token)

    return tokens


def _check_for_opening_bracket(
    tokens: list[str],
    i: int,
    token: str,
    bracket_stack: list[str],
    collection_stack: list[tuple[str, str]],
) -> None:
    """Check for opening bracket in type declaration.

    Args:
        tokens (list[str]): List of tokens
        i (int): Current token index
        token (str): Current token
        bracket_stack (list[str]): Stack of open brackets
        collection_stack (list[tuple[str, str]]): Stack of collection types

    Returns:
        None

    Raises:
        BracketValidationError: If bracket usage is invalid
    """
    bracket_stack.append(token)

    # Check if the previous token is a collection requiring arguments
    if i > 0 and tokens[i - 1] in COLLECTIONS_REQUIRING_ARGS:
        collection_stack.append((tokens[i - 1], token))


def _check_for_closing_bracket(token: str, bracket_stack: list[str], collection_stack: list[tuple[str, str]]) -> None:
    """Check for closing bracket in type declaration.

    Args:
        token (str): Current token
        bracket_stack (list[str]): Stack of open brackets
        collection_stack (list[tuple[str, str]]): Stack of collection types

    Returns:
        None

    Raises:
        BracketValidationError: If bracket usage is invalid
    """
    if not bracket_stack:
        raise BracketValidationError(BracketValidationError.UNBALANCED_CLOSING)

    # Check for mismatched bracket pairs
    last_open = bracket_stack.pop()
    if (
        (last_open == OPEN_BRACKET and token != CLOSE_BRACKET)
        or (last_open == OPEN_PAREN and token != CLOSE_PAREN)
        or (last_open == OPEN_BRACE and token != CLOSE_BRACE)
    ):
        raise BracketValidationError(BracketValidationError.MISMATCHED_PAIR)

    # If we're closing a collection's brackets, remove it from the stack
    if collection_stack and collection_stack[-1][1] == last_open:
        collection_stack.pop()


def _check_for_bare_collection(tokens: list[str], i: int, token: str) -> None:
    """Check for bare collection type usage.

    Args:
        tokens (list[str]): List of tokens
        i (int): Current token index
        token (str): Current token

    Returns:
        None

    Raises:
        InvalidTypeAnnotationError: If a bare collection type is found
    """
    if token in COLLECTIONS_REQUIRING_ARGS:
        # Skip if this collection is followed by an opening bracket
        if i < len(tokens) - 1 and tokens[i + 1] in (OPEN_BRACKET, OPEN_PAREN, OPEN_BRACE):
            return

        # Skip if this is part of a qualified name (e.g., module.List)
        if i > 0 and tokens[i - 1] == ".":
            return

        error_msg = f"Collection '{token}' must be followed by type arguments in brackets"
        raise InvalidTypeAnnotationError(error_msg)


def _is_bare_collection_in_nested_type(token: str, tokens: list[str], i: int, bracket_stack: list[str]) -> bool:
    """Check if a collection type is used without type arguments in a nested type.

    Args:
        token (str): The current token
        tokens (list[str]): The list of all tokens
        i (int): The current token index
        bracket_stack (list[str]): The stack of open brackets

    Returns:
        bool: True if the collection is used without type arguments in a nested type
    """
    is_collection: bool = token in COLLECTIONS_REQUIRING_ARGS
    has_brackets: bool = bool(bracket_stack)
    has_next_token: bool = i < len(tokens) - 1
    next_token_not_bracket: bool = tokens[i + 1] != OPEN_BRACKET if has_next_token else False

    return is_collection and has_brackets and has_next_token and next_token_not_bracket


def _check_tokens_for_collection_type_usage(tokens: list[str]) -> None:
    """Check tokens for proper collection type usage.

    Args:
        tokens (list[str]): List of tokens to check

    Returns:
        None

    Raises:
        InvalidTypeAnnotationError: If collection type usage is invalid
        BracketValidationError: If bracket usage is invalid
    """
    bracket_stack: list[str] = []
    collection_stack: list[tuple[str, str]] = []

    # Check for balanced brackets and proper collection type usage
    for i, token in enumerate(tokens):
        # Handle opening brackets
        if token in (OPEN_BRACKET, OPEN_PAREN, OPEN_BRACE):
            _check_for_opening_bracket(tokens, i, token, bracket_stack, collection_stack)

        # Handle closing brackets
        elif token in (CLOSE_BRACKET, CLOSE_PAREN, CLOSE_BRACE):
            _check_for_closing_bracket(token, bracket_stack, collection_stack)

        # Check for bare collections in nested types
        elif _is_bare_collection_in_nested_type(token, tokens, i, bracket_stack):
            error_msg = f"Invalid nested type: collection type '{token}' requires element types"
            raise InvalidTypeAnnotationError(error_msg)

    # Check for unclosed brackets at the end
    if bracket_stack:
        raise BracketValidationError(BracketValidationError.UNCLOSED_BRACKETS)

    # Check for bare collections (without brackets)
    for i, token in enumerate(tokens):
        _check_for_bare_collection(tokens, i, token)

    # Check for mismatched bracket types for collection arguments
    for i, token in enumerate(tokens):
        if (
            token in COLLECTIONS_REQUIRING_ARGS
            and i < len(tokens) - 2
            and tokens[i + 1] != OPEN_BRACKET
            and tokens[i + 1] in (OPEN_BRACE, OPEN_PAREN)
        ):
            # Format the error message using the class constant
            error_msg = BracketValidationError.WRONG_BRACKET_TYPE.format(token, tokens[i + 1])
            raise BracketValidationError(error_msg)


def _validate_type_declaration(declaration: str) -> None:
    """Validate a type declaration.

    Args:
        declaration (str): The type declaration to validate

    Returns:
        None

    Raises:
        InvalidTypeAnnotationError: If the type declaration is invalid
        BracketValidationError: If bracket usage is invalid
    """
    # Skip validation if it's clearly not a type annotation
    if len(declaration.split()) > MAX_WORD_COUNT_FOR_TYPE and NESTING_KEYWORD in declaration.split():
        # This looks like a test description rather than a type declaration
        return

    # Convert the declaration to tokens
    tokens = _tokenize_type_declaration(declaration)

    if not tokens:
        return

    # Check tokens for proper collection type usage and balanced brackets
    _check_tokens_for_collection_type_usage(tokens)
