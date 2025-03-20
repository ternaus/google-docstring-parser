import pytest

from google_docstring_parser import parse_google_docstring
from google_docstring_parser.google_docstring_parser import ReferenceFormatError


def test_parse_references_multiple_with_dash() -> None:
    docstring = '''Test function with references.

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - Documentation for library: https://example.com/docs
        - Research paper: Author, A. (Year). Title. Journal, Volume(Issue), pages.
        - Stack Overflow: https://stackoverflow.com/a/12345
    '''

    result = parse_google_docstring(docstring)

    assert 'References' in result
    references = result['References']
    assert len(references) == 3

    assert references[0]['description'] == 'Documentation for library'
    assert references[0]['source'] == 'https://example.com/docs'

    assert references[1]['description'] == 'Research paper'
    assert references[1]['source'] == 'Author, A. (Year). Title. Journal, Volume(Issue), pages.'

    assert references[2]['description'] == 'Stack Overflow'
    assert references[2]['source'] == 'https://stackoverflow.com/a/12345'


def test_parse_references_single_line() -> None:
    docstring = '''Test function with a single reference.

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        Documentation: https://example.com/docs
    '''

    result = parse_google_docstring(docstring)

    assert 'Reference' in result
    references = result['Reference']
    assert len(references) == 1

    assert references[0]['description'] == 'Documentation'
    assert references[0]['source'] == 'https://example.com/docs'


def test_parse_references_single_with_dash_error() -> None:
    """Test function with a single reference with dash.

    This test verifies that a single reference (Reference: section) cannot use
    a dash prefix, as dashes are only for multiple references.
    """
    docstring = '''Test function with a single reference with dash.

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        - Documentation: https://example.com/docs
    '''

    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_multiple_lines() -> None:
    """Test that multiple main references without dashes should raise an error.

    Each separate reference (not continuation lines) should start with a dash.
    """
    docstring = '''Test function with multiple references without dashes.

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        Documentation: https://example.com/docs
        Research paper: Author, A. (Year). Title. Journal, Volume(Issue), pages.
        Stack Overflow: https://stackoverflow.com/a/12345
    '''

    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_no_references() -> None:
    docstring = '''Test function without references.

    Args:
        x: A parameter

    Returns:
        Result value
    '''

    result = parse_google_docstring(docstring)

    assert 'References' not in result
    assert 'Reference' not in result


def test_parse_references_missing_dash() -> None:
    """Test error raised when some references don't start with dashes.

    When there are multiple references, all main references should start with dashes,
    even when some references have multi-line descriptions.
    """
    docstring = '''Test function with invalid references (missing dash).

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - First reference: https://example.com/first
        Second reference without dash: https://example.com/second
    '''

    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_missing_colon() -> None:
    docstring = '''Test function with invalid reference (missing colon).

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - Documentation for library https://example.com/docs
    '''

    # Single line with dash will raise DashInSingleReferenceError even if it's missing a colon
    # because that check comes after the colon check in our implementation
    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_missing_colon_multiline() -> None:
    docstring = '''Test function with invalid references (missing colon).

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - First reference: https://example.com/first
        - Second reference without-colon http example.com/second
    '''

    # Just check that it raises any ValueError - specific message is implementation detail
    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_single_missing_colon() -> None:
    docstring = '''Test function with invalid single reference (missing colon).

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        Documentation for library without colon
    '''

    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_colon_only_in_url() -> None:
    docstring = '''Test function with reference where colon only exists in URL.

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        Documentation for library https://example.com/docs
    '''

    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_colon_only_in_url_multiline() -> None:
    docstring = '''Test function with references where colon only exists in URL.

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - Documentation for library https://example.com/docs
        - Another reference https://stackoverflow.com/q/12345
    '''

    with pytest.raises(ReferenceFormatError):
        parse_google_docstring(docstring)


def test_parse_references_single_with_dash_error_code() -> None:
    docstring = '''Test function with a single reference with dash.

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        - Documentation: https://example.com/docs
    '''

    with pytest.raises(ReferenceFormatError) as excinfo:
        parse_google_docstring(docstring)

    assert excinfo.value.code == "dash_in_single"


def test_parse_references_multiple_missing_dash_error_code() -> None:
    docstring = '''Test function with multiple references without dashes.

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        Documentation: https://example.com/docs
        Research paper: Author, A. (Year). Title. Journal, Volume(Issue), pages.
    '''

    with pytest.raises(ReferenceFormatError) as excinfo:
        parse_google_docstring(docstring)

    assert excinfo.value.code == "missing_dash"


def test_parse_references_missing_colon_error_code() -> None:
    docstring = '''Test function with invalid reference (missing colon).

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        Documentation for library without colon
    '''

    with pytest.raises(ReferenceFormatError) as excinfo:
        parse_google_docstring(docstring)

    assert excinfo.value.code == "missing_colon"


def test_parse_references_empty_description_error_code() -> None:
    docstring = '''Test function with invalid reference (empty description).

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        : https://example.com/docs
    '''

    with pytest.raises(ReferenceFormatError) as excinfo:
        parse_google_docstring(docstring)

    assert excinfo.value.code == "empty_description"


def test_parse_references_with_multiline_description() -> None:
    """Test parsing references with multi-line descriptions based on indentation."""
    docstring = '''Test function with references including a multi-line reference.

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - Bleach method: https://github.com/UjjwalSaxena/Automold--Road-Augmentation-Library
        - Texture method: Inspired by computer graphics techniques for snow rendering
           and atmospheric scattering simulations.
    '''

    result = parse_google_docstring(docstring)

    assert 'References' in result
    references = result['References']
    assert len(references) == 2

    assert references[0]['description'] == 'Bleach method'
    assert references[0]['source'] == 'https://github.com/UjjwalSaxena/Automold--Road-Augmentation-Library'

    assert references[1]['description'] == 'Texture method'
    assert references[1]['source'] == 'Inspired by computer graphics techniques for snow rendering and atmospheric scattering simulations.'


def test_parse_references_with_two_multiline_descriptions() -> None:
    """Test parsing references where multiple references have multi-line descriptions."""
    docstring = '''Test function with references where all have multi-line descriptions.

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - First reference: This is a description that spans
          multiple lines with consistent indentation.
        - Second reference: Another description with
          multiple lines and
          even more text.
    '''

    result = parse_google_docstring(docstring)

    assert 'References' in result
    references = result['References']
    assert len(references) == 2

    assert references[0]['description'] == 'First reference'
    assert references[0]['source'] == 'This is a description that spans multiple lines with consistent indentation.'

    assert references[1]['description'] == 'Second reference'
    assert references[1]['source'] == 'Another description with multiple lines and even more text.'


def test_parse_references_mixed_formatting() -> None:
    """Test parsing references with a mix of single-line and multi-line descriptions."""
    docstring = '''Test function with mixed reference formatting.

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - Simple reference: https://example.com/docs
        - Complex reference: This is a description that spans
          multiple lines and contains technical details
          about the implementation.
        - Another simple one: Just a short note.
    '''

    result = parse_google_docstring(docstring)

    assert 'References' in result
    references = result['References']
    assert len(references) == 3

    assert references[0]['description'] == 'Simple reference'
    assert references[0]['source'] == 'https://example.com/docs'

    assert references[1]['description'] == 'Complex reference'
    assert references[1]['source'] == 'This is a description that spans multiple lines and contains technical details about the implementation.'

    assert references[2]['description'] == 'Another simple one'
    assert references[2]['source'] == 'Just a short note.'
