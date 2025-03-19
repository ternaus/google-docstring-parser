import pytest

from google_docstring_parser import parse_google_docstring
from google_docstring_parser.google_docstring_parser import MissingDashError, DashInSingleReferenceError, MissingColonError


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
    docstring = '''Test function with a single reference with dash.

    Args:
        x: A parameter

    Returns:
        Result value

    Reference:
        - Documentation: https://example.com/docs
    '''

    with pytest.raises(DashInSingleReferenceError):
        parse_google_docstring(docstring)


def test_parse_references_multiple_lines() -> None:
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

    with pytest.raises(MissingDashError):
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
    docstring = '''Test function with invalid references (missing dash).

    Args:
        x: A parameter

    Returns:
        Result value

    References:
        - First reference: https://example.com/first
        Second reference without dash: https://example.com/second
    '''

    with pytest.raises(MissingDashError):
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
    with pytest.raises(DashInSingleReferenceError):
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
    with pytest.raises(MissingColonError):
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

    with pytest.raises(MissingColonError):
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

    with pytest.raises(MissingColonError):
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

    with pytest.raises(MissingColonError):
        parse_google_docstring(docstring)
