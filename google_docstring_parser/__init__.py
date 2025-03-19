"""Google Docstring Parser package.

A lightweight, efficient parser for Google-style Python docstrings that converts them into structured dictionaries.
"""

from google_docstring_parser.google_docstring_parser import ReferenceFormatError, parse_google_docstring

__all__ = ["ReferenceFormatError", "parse_google_docstring"]
