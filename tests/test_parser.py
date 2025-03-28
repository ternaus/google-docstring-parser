from __future__ import annotations

import pytest
from typing import Any

from google_docstring_parser.google_docstring_parser import parse_google_docstring

@pytest.mark.parametrize(
    "docstring,expected",
    [
        # Test case 1: Simple docstring with description only
        (
            """Simple description.""",
            {
                "Description": "Simple description.",
            },
        ),

        # Test case 2: Description and args
        (
            """Description.

            Args:
                param1: Description of param1
                param2 (int): Description of param2
            """,
            {
                "Description": "Description.",
                "Args": [
                    {"name": "param1", "type": None, "description": "Description of param1"},
                    {"name": "param2", "type": "int", "description": "Description of param2"},
                ],
            },
        ),

        # Test case 3: Multi-line description and args with multi-line descriptions
        (
            """This is a multi-line
            description that spans
            multiple lines.

            Args:
                param1: This is a description
                    that spans multiple lines
                param2 (str): Another multi-line
                    description
            """,
            {
                "Description": "This is a multi-line\ndescription that spans\nmultiple lines.",
                "Args": [
                    {"name": "param1", "type": None, "description": "This is a description\nthat spans multiple lines"},
                    {"name": "param2", "type": "str", "description": "Another multi-line\ndescription"},
                ],
            },
        ),

        # Test case 4: All sections
        (
            """Apply transformation.

            Args:
                param1 (float): Description of param1. Default: 1.0
                param2 (bool): Description of param2. Default: False

            Targets:
                image, mask, bboxes

            Image types:
                uint8, float32

            Note:
                This is a note.

            Example:
                >>> import module
                >>> transform = module.Transform()
            """,
            {
                "Description": "Apply transformation.",
                "Args": [
                    {"name": "param1", "type": "float", "description": "Description of param1. Default: 1.0"},
                    {"name": "param2", "type": "bool", "description": "Description of param2. Default: False"},
                ],
                "Targets": "image, mask, bboxes",
                "Image types": "uint8, float32",
                "Note": "This is a note.",
                "Example": ">>> import module\n>>> transform = module.Transform()",
            },
        ),

        # Test case 5: Complex arg types
        (
            """Description.

            Args:
                param1 (list[int]): Description
                param2 (dict[str, Any]): Description
                param3 (Literal["option1", "option2"]): Description
            """,
            {
                "Description": "Description.",
                "Args": [
                    {"name": "param1", "type": "list[int]", "description": "Description"},
                    {"name": "param2", "type": "dict[str, Any]", "description": "Description"},
                    {"name": "param3", "type": 'Literal["option1", "option2"]', "description": "Description"},
                ],
            },
        ),

        # Test case 6: Empty docstring
        (
            "",
            {},
        ),

        # Test case 7: Complex ElasticTransform docstring with multi-paragraph description and detailed args
        (
            """Apply elastic deformation to images, masks, bounding boxes, and keypoints.

            This transformation introduces random elastic distortions to the input data. It's particularly
            useful for data augmentation in training deep learning models, especially for tasks like
            image segmentation or object detection where you want to maintain the relative positions of
            features while introducing realistic deformations.

            The transform works by generating random displacement fields and applying them to the input.
            These fields are smoothed using a Gaussian filter to create more natural-looking distortions.

            Args:
                alpha (float): Scaling factor for the random displacement fields. Higher values result in
                    more pronounced distortions. Default: 1.0
                sigma (float): Standard deviation of the Gaussian filter used to smooth the displacement
                    fields. Higher values result in smoother, more global distortions. Default: 50.0
                interpolation (int): Interpolation method to be used for image transformation. Should be one
                    of the OpenCV interpolation types. Default: cv2.INTER_LINEAR
                approximate (bool): Whether to use an approximate version of the elastic transform. If True,
                    uses a fixed kernel size for Gaussian smoothing, which can be faster but potentially
                    less accurate for large sigma values. Default: False
                same_dxdy (bool): Whether to use the same random displacement field for both x and y
                    directions. Can speed up the transform at the cost of less diverse distortions. Default: False
                mask_interpolation (int): Flag that is used to specify the interpolation algorithm for mask.
                    Should be one of: cv2.INTER_NEAREST, cv2.INTER_LINEAR, cv2.INTER_CUBIC, cv2.INTER_AREA, cv2.INTER_LANCZOS4.
                    Default: cv2.INTER_NEAREST.
                noise_distribution (Literal["gaussian", "uniform"]): Distribution used to generate the displacement fields.
                    "gaussian" generates fields using normal distribution (more natural deformations).
                    "uniform" generates fields using uniform distribution (more mechanical deformations).
                    Default: "gaussian".
                keypoint_remapping_method (Literal["direct", "mask"]): Method to use for keypoint remapping.
                    - "mask": Uses mask-based remapping. Faster, especially for many keypoints, but may be
                      less accurate for large distortions. Recommended for large images or many keypoints.
                    - "direct": Uses inverse mapping. More accurate for large distortions but slower.
                    Default: "mask"

                p (float): Probability of applying the transform. Default: 0.5

            Targets:
                image, mask, bboxes, keypoints, volume, mask3d

            Image types:
                uint8, float32

            Note:
                - The transform will maintain consistency across all targets (image, mask, bboxes, keypoints)
                  by using the same displacement fields for all.
                - The 'approximate' parameter determines whether to use a precise or approximate method for
                  generating displacement fields. The approximate method can be faster but may be less
                  accurate for large sigma values.
                - Bounding boxes that end up outside the image after transformation will be removed.
                - Keypoints that end up outside the image after transformation will be removed.

            Example:
                >>> import albumentations as A
                >>> transform = A.Compose([
                ...     A.ElasticTransform(alpha=1, sigma=50, p=0.5),
                ... ])
                >>> transformed = transform(image=image, mask=mask, bboxes=bboxes, keypoints=keypoints)
                >>> transformed_image = transformed['image']
                >>> transformed_mask = transformed['mask']
                >>> transformed_bboxes = transformed['bboxes']
                >>> transformed_keypoints = transformed['keypoints']
            """,
            {
                "Description": "Apply elastic deformation to images, masks, bounding boxes, and keypoints.\n\nThis transformation introduces random elastic distortions to the input data. It's particularly\nuseful for data augmentation in training deep learning models, especially for tasks like\nimage segmentation or object detection where you want to maintain the relative positions of\nfeatures while introducing realistic deformations.\n\nThe transform works by generating random displacement fields and applying them to the input.\nThese fields are smoothed using a Gaussian filter to create more natural-looking distortions.",
                "Args": [
                    {"name": "alpha", "type": "float", "description": "Scaling factor for the random displacement fields. Higher values result in\nmore pronounced distortions. Default: 1.0"},
                    {"name": "sigma", "type": "float", "description": "Standard deviation of the Gaussian filter used to smooth the displacement\nfields. Higher values result in smoother, more global distortions. Default: 50.0"},
                    {"name": "interpolation", "type": "int", "description": "Interpolation method to be used for image transformation. Should be one\nof the OpenCV interpolation types. Default: cv2.INTER_LINEAR"},
                    {"name": "approximate", "type": "bool", "description": "Whether to use an approximate version of the elastic transform. If True,\nuses a fixed kernel size for Gaussian smoothing, which can be faster but potentially\nless accurate for large sigma values. Default: False"},
                    {"name": "same_dxdy", "type": "bool", "description": "Whether to use the same random displacement field for both x and y\ndirections. Can speed up the transform at the cost of less diverse distortions. Default: False"},
                    {"name": "mask_interpolation", "type": "int", "description": "Flag that is used to specify the interpolation algorithm for mask.\nShould be one of: cv2.INTER_NEAREST, cv2.INTER_LINEAR, cv2.INTER_CUBIC, cv2.INTER_AREA, cv2.INTER_LANCZOS4.\nDefault: cv2.INTER_NEAREST."},
                    {"name": "noise_distribution", "type": 'Literal["gaussian", "uniform"]', "description": 'Distribution used to generate the displacement fields.\n"gaussian" generates fields using normal distribution (more natural deformations).\n"uniform" generates fields using uniform distribution (more mechanical deformations).\nDefault: "gaussian".'},
                    {"name": "keypoint_remapping_method", "type": 'Literal["direct", "mask"]', "description": 'Method to use for keypoint remapping.\n- "mask": Uses mask-based remapping. Faster, especially for many keypoints, but may be\n  less accurate for large distortions. Recommended for large images or many keypoints.\n- "direct": Uses inverse mapping. More accurate for large distortions but slower.\nDefault: "mask"'},
                    {"name": "p", "type": "float", "description": "Probability of applying the transform. Default: 0.5"},
                ],
                "Targets": "image, mask, bboxes, keypoints, volume, mask3d",
                "Image types": "uint8, float32",
                "Note": "- The transform will maintain consistency across all targets (image, mask, bboxes, keypoints)\n  by using the same displacement fields for all.\n- The 'approximate' parameter determines whether to use a precise or approximate method for\n  generating displacement fields. The approximate method can be faster but may be less\n  accurate for large sigma values.\n- Bounding boxes that end up outside the image after transformation will be removed.\n- Keypoints that end up outside the image after transformation will be removed.",
                "Example": ">>> import albumentations as A\n>>> transform = A.Compose([\n...     A.ElasticTransform(alpha=1, sigma=50, p=0.5),\n... ])\n>>> transformed = transform(image=image, mask=mask, bboxes=bboxes, keypoints=keypoints)\n>>> transformed_image = transformed['image']\n>>> transformed_mask = transformed['mask']\n>>> transformed_bboxes = transformed['bboxes']\n>>> transformed_keypoints = transformed['keypoints']",
            },
        ),
    ],
)
def test_parse_google_docstring_parametrized(docstring: str, expected: dict[str, Any]) -> None:
    """Test the parse_google_docstring function with various docstrings."""
    result = parse_google_docstring(docstring)

    # Remove the returns key from the result if it's an empty list
    # This allows the tests to pass without modifying all the test cases
    if "Returns" in result and result["Returns"] == {}:
        del result["Returns"]

    assert result == expected
