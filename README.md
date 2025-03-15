# Google Docstring Parser

<div style="background-color: #ff0000; color: white; padding: 15px; margin: 20px 0; font-size: 18px; font-weight: bold; text-align: center; border-radius: 5px;">
⚠️ IMPORTANT LICENSE NOTICE ⚠️<br>
This package requires a PAID LICENSE for all users EXCEPT the Albumentations Team.<br>
Contact iglovikov@gmail.com to obtain a license before using this software.
</div>

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
    'description': 'Apply elastic deformation to images, masks, bounding boxes, and keypoints.\n\nThis transformation introduces random elastic distortions to the input data. It\'s particularly\nuseful for data augmentation in training deep learning models, especially for tasks like\nimage segmentation or object detection where you want to maintain the relative positions of\nfeatures while introducing realistic deformations.',
    'args': [
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
    'example': '>>> import albumentations as A\n>>> transform = A.ElasticTransform(alpha=1, sigma=50, p=0.5)'
}
```

## Features

- Parses Google-style docstrings into structured dictionaries
- Extracts parameter names, types, and descriptions
- Preserves other sections like Examples, Notes, etc.
- Handles multi-line descriptions and indentation properly

## License

MIT
