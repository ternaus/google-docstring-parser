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
    'Example': '>>> import albumentations as A\n>>> transform = A.ElasticTransform(alpha=1, sigma=50, p=0.5)'
}
```

## Features

- Parses Google-style docstrings into structured dictionaries
- Extracts parameter names, types, and descriptions
- Preserves other sections like Examples, Notes, etc.
- Handles multi-line descriptions and indentation properly


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
exclude_files = ["conftest.py", "__init__.py"] # Files to exclude from checks
verbose = false                              # Enable verbose output
```

This approach has several advantages:
- Keeps all your project configuration in one place
- Follows modern Python tooling conventions
- Makes it easier to maintain and update configuration
- Provides better IDE support and documentation

For more details, see the [tools README](tools/README.md).
