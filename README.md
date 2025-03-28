# Google Docstring Parser

> [!IMPORTANT]
> This package requires a PAID LICENSE for all users EXCEPT the Albumentations Team.
> Contact iglovikov@gmail.com to obtain a license before using this software.

A Python package for parsing Google-style docstrings into structured dictionaries.

## License Information

This package is available under a custom license:
- **Free for Albumentations Team projects** (https://github.com/albumentations-team)
- **Paid license required for all other users** (individuals, companies, and other open-source projects)

See the [LICENSE](LICENSE) file for complete details.

## Installation

```bash
pip install google-docstring-parser
```

## Usage

```python
from google_docstring_parser import parse_google_docstring

docstring = '''Apply elastic deformation to images, masks, bounding boxes, and keypoints.

This transformation introduces random elastic distortions to the input data. It's particularly
useful for data augmentation in training deep learning models, especially for tasks like
image segmentation or object detection where you want to maintain the relative positions of
features while introducing realistic deformations.

Args:
    alpha (float): Scaling factor for the random displacement fields. Higher values result in
        more pronounced distortions. Default: 1.0
    sigma (float): Standard deviation of the Gaussian filter used to smooth the displacement
        fields. Higher values result in smoother, more global distortions. Default: 50.0

Example:
    >>> import albumentations as A
    >>> transform = A.ElasticTransform(alpha=1, sigma=50, p=0.5)

References:
    - Original paper: Simard, P. Y., et al. "Best practices for convolutional neural networks applied to visual document analysis." ICDAR 2003
    - Implementation details: https://example.com/elastic-transform
Returns:
    dict[str, Any]: Some info here
'''

parsed = parse_google_docstring(docstring)
print(parsed)
```

Output:
```python
{
    'Description': 'Apply elastic deformation to images, masks, bounding boxes, and keypoints.\n\nThis transformation introduces random elastic distortions to the input data. It\'s particularly\nuseful for data augmentation in training deep learning models, especially for tasks like\nimage segmentation or object detection where you want to maintain the relative positions of\nfeatures while introducing realistic deformations.',
    'Args': [
        {
            'name': 'alpha',
            'type': 'float',
            'description': 'Scaling factor for the random displacement fields. Higher values result in\nmore pronounced distortions. Default: 1.0'
        },
        {
            'name': 'sigma',
            'type': 'float',
            'description': 'Standard deviation of the Gaussian filter used to smooth the displacement\nfields. Higher values result in smoother, more global distortions. Default: 50.0'
        }
    ],
    'Example': '>>> import albumentations as A\n>>> transform = A.ElasticTransform(alpha=1, sigma=50, p=0.5)',
    'References': [
        {
            'description': 'Original paper',
            'source': 'Simard, P. Y., et al. "Best practices for convolutional neural networks applied to visual document analysis." ICDAR 2003'
        },
        {
            'description': 'Implementation details',
            'source': 'https://example.com/elastic-transform'
        }
    ],
    'Returns':
        {
            "type": "dict[str, Any]",
            "description": "Some info here"
        }
}
```

## Features

- Parses Google-style docstrings into structured dictionaries
- Extracts parameter names, types, and descriptions
- Preserves other sections like Examples, Notes, etc.
- Handles multi-line descriptions and indentation properly
- Properly parses and validates References sections with special handling for URLs

### References

The parser can handle reference sections in Google-style docstrings. References can be formatted in two ways:

1. Single reference format:
```python
"""
Reference:
    Paper title: https://example.com/paper
"""
```

2. Multiple references format (requires leading dashes):
```python
"""
References:
    - First paper: https://example.com/paper1
    - Second paper: https://example.com/paper2
"""
```

Each reference is parsed into a dictionary with `description` and `source` keys. URLs in the source are properly handled, ensuring colons in URLs are not confused with the separator colon.

## Pre-commit Hook

This package includes a pre-commit hook that checks if Google-style docstrings in your codebase can be parsed correctly.

### Usage in Other Projects

To use this hook in another project, add the following to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/ternaus/google-docstring-parser
  rev: v0.0.1  # Use the latest version
  hooks:
    - id: check-google-docstrings
      additional_dependencies: ["tomli>=2.0.0"]  # Required for pyproject.toml configuration
```

### Configuration

The hook is configured via pyproject.toml, following modern Python tooling conventions like those used by mypy, ruff, and other tools.

Add a `[tool.docstring_checker]` section to your pyproject.toml:

```toml
[tool.docstring_checker]
paths = ["src", "tests"]                     # Directories or files to scan
require_param_types = true                   # Require parameter types in docstrings
check_references = true                      # Check references for proper format
exclude_files = ["conftest.py", "__init__.py"] # Files to exclude from checks
verbose = false                              # Enable verbose output
```
