import pytest
from typing import Any

from google_docstring_parser.parser import parse_google_docstring, _parse_args_section

@pytest.mark.parametrize(
    "docstring,expected",
    [
        # Test case 1: Simple docstring with description only
        (
            """Simple description.""",
            {
                "description": "Simple description.",
                "args": [],
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
                "description": "Description.",
                "args": [
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
                "description": "This is a multi-line\n            description that spans\n            multiple lines.",
                "args": [
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
                "description": "Apply transformation.",
                "args": [
                    {"name": "param1", "type": "float", "description": "Description of param1. Default: 1.0"},
                    {"name": "param2", "type": "bool", "description": "Description of param2. Default: False"},
                ],
                "targets": "image, mask, bboxes\n\n            Image types:\n                uint8, float32",
                "note": "This is a note.",
                "example": ">>> import module\n                >>> transform = module.Transform()",
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
                "description": "Description.",
                "args": [
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
                "description": "Apply elastic deformation to images, masks, bounding boxes, and keypoints.\n\n            This transformation introduces random elastic distortions to the input data. It's particularly\n            useful for data augmentation in training deep learning models, especially for tasks like\n            image segmentation or object detection where you want to maintain the relative positions of\n            features while introducing realistic deformations.\n\n            The transform works by generating random displacement fields and applying them to the input.\n            These fields are smoothed using a Gaussian filter to create more natural-looking distortions.",
                "args": [
                    {"name": "alpha", "type": "float", "description": "Scaling factor for the random displacement fields. Higher values result in\nmore pronounced distortions. Default: 1.0"},
                    {"name": "sigma", "type": "float", "description": "Standard deviation of the Gaussian filter used to smooth the displacement\nfields. Higher values result in smoother, more global distortions. Default: 50.0"},
                    {"name": "interpolation", "type": "int", "description": "Interpolation method to be used for image transformation. Should be one\nof the OpenCV interpolation types. Default: cv2.INTER_LINEAR"},
                    {"name": "approximate", "type": "bool", "description": "Whether to use an approximate version of the elastic transform. If True,\nuses a fixed kernel size for Gaussian smoothing, which can be faster but potentially\nless accurate for large sigma values. Default: False"},
                    {"name": "same_dxdy", "type": "bool", "description": "Whether to use the same random displacement field for both x and y\ndirections. Can speed up the transform at the cost of less diverse distortions. Default: False"},
                    {"name": "mask_interpolation", "type": "int", "description": "Flag that is used to specify the interpolation algorithm for mask.\nShould be one of: cv2.INTER_NEAREST, cv2.INTER_LINEAR, cv2.INTER_CUBIC, cv2.INTER_AREA, cv2.INTER_LANCZOS4."},
                    {"name": "Default", "type": None, "description": "cv2.INTER_NEAREST."},
                    {"name": "noise_distribution", "type": 'Literal["gaussian", "uniform"]', "description": 'Distribution used to generate the displacement fields.\n"gaussian" generates fields using normal distribution (more natural deformations).\n"uniform" generates fields using uniform distribution (more mechanical deformations).'},
                    {"name": "Default", "type": None, "description": '"gaussian".'},
                    {"name": "keypoint_remapping_method", "type": 'Literal["direct", "mask"]', "description": 'Method to use for keypoint remapping.\n- "mask": Uses mask-based remapping. Faster, especially for many keypoints, but may be\nless accurate for large distortions. Recommended for large images or many keypoints.\n- "direct": Uses inverse mapping. More accurate for large distortions but slower.'},
                    {"name": "Default", "type": None, "description": '"mask"'},
                    {"name": "p", "type": "float", "description": "Probability of applying the transform. Default: 0.5"},
                ],
                "targets": "image, mask, bboxes, keypoints, volume, mask3d\n\n            Image types:\n                uint8, float32",
                "note": "- The transform will maintain consistency across all targets (image, mask, bboxes, keypoints)\n                  by using the same displacement fields for all.\n                - The 'approximate' parameter determines whether to use a precise or approximate method for\n                  generating displacement fields. The approximate method can be faster but may be less\n                  accurate for large sigma values.\n                - Bounding boxes that end up outside the image after transformation will be removed.\n                - Keypoints that end up outside the image after transformation will be removed.",
                "example": ">>> import albumentations as A\n                >>> transform = A.Compose([\n                ...     A.ElasticTransform(alpha=1, sigma=50, p=0.5),\n                ... ])\n                >>> transformed = transform(image=image, mask=mask, bboxes=bboxes, keypoints=keypoints)\n                >>> transformed_image = transformed['image']\n                >>> transformed_mask = transformed['mask']\n                >>> transformed_bboxes = transformed['bboxes']\n                >>> transformed_keypoints = transformed['keypoints']",
            },
        ),

        # Test case 8: Affine transformation docstring with complex parameters
        (
            """Augmentation to apply affine transformations to images.

    Affine transformations involve:

        - Translation ("move" image on the x-/y-axis)
        - Rotation
        - Scaling ("zoom" in/out)
        - Shear (move one side of the image, turning a square into a trapezoid)

    All such transformations can create "new" pixels in the image without a defined content, e.g.
    if the image is translated to the left, pixels are created on the right.
    A method has to be defined to deal with these pixel values.
    The parameters `fill` and `fill_mask` of this class deal with this.

    Some transformations involve interpolations between several pixels
    of the input image to generate output pixel values. The parameters `interpolation` and
    `mask_interpolation` deals with the method of interpolation used for this.

    Args:
        scale (number, tuple of number or dict): Scaling factor to use, where ``1.0`` denotes "no change" and
            ``0.5`` is zoomed out to ``50`` percent of the original size.
                * If a single number, then that value will be used for all images.
                * If a tuple ``(a, b)``, then a value will be uniformly sampled per image from the interval ``[a, b]``.
                  That the same range will be used for both x- and y-axis. To keep the aspect ratio, set
                  ``keep_ratio=True``, then the same value will be used for both x- and y-axis.
                * If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.
                  Each of these keys can have the same values as described above.
                  Using a dictionary allows to set different values for the two axis and sampling will then happen
                  *independently* per axis, resulting in samples that differ between the axes. Note that when
                  the ``keep_ratio=True``, the x- and y-axis ranges should be the same.
        translate_percent (None, number, tuple of number or dict): Translation as a fraction of the image height/width
            (x-translation, y-translation), where ``0`` denotes "no change"
            and ``0.5`` denotes "half of the axis size".
                * If ``None`` then equivalent to ``0.0`` unless `translate_px` has a value other than ``None``.
                * If a single number, then that value will be used for all images.
                * If a tuple ``(a, b)``, then a value will be uniformly sampled per image from the interval ``[a, b]``.
                  That sampled fraction value will be used identically for both x- and y-axis.
                * If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.
                  Each of these keys can have the same values as described above.
                  Using a dictionary allows to set different values for the two axis and sampling will then happen
                  *independently* per axis, resulting in samples that differ between the axes.
        translate_px (None, int, tuple of int or dict): Translation in pixels.
                * If ``None`` then equivalent to ``0`` unless `translate_percent` has a value other than ``None``.
                * If a single int, then that value will be used for all images.
                * If a tuple ``(a, b)``, then a value will be uniformly sampled per image from
                  the discrete interval ``[a..b]``. That number will be used identically for both x- and y-axis.
                * If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.
                  Each of these keys can have the same values as described above.
                  Using a dictionary allows to set different values for the two axis and sampling will then happen
                  *independently* per axis, resulting in samples that differ between the axes.
        rotate (number or tuple of number): Rotation in degrees (**NOT** radians), i.e. expected value range is
            around ``[-360, 360]``. Rotation happens around the *center* of the image,
            not the top left corner as in some other frameworks.
                * If a number, then that value will be used for all images.
                * If a tuple ``(a, b)``, then a value will be uniformly sampled per image from the interval ``[a, b]``
                  and used as the rotation value.
        shear (number, tuple of number or dict): Shear in degrees (**NOT** radians), i.e. expected value range is
            around ``[-360, 360]``, with reasonable values being in the range of ``[-45, 45]``.
                * If a number, then that value will be used for all images as
                  the shear on the x-axis (no shear on the y-axis will be done).
                * If a tuple ``(a, b)``, then two value will be uniformly sampled per image
                  from the interval ``[a, b]`` and be used as the x- and y-shear value.
                * If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.
                  Each of these keys can have the same values as described above.
                  Using a dictionary allows to set different values for the two axis and sampling will then happen
                  *independently* per axis, resulting in samples that differ between the axes.
        interpolation (int): OpenCV interpolation flag.
        mask_interpolation (int): OpenCV interpolation flag.
        fill (tuple[float, ...] | float): The constant value to use when filling in newly created pixels.
            (E.g. translating by 1px to the right will create a new 1px-wide column of pixels
            on the left of the image).
            The value is only used when `mode=constant`. The expected value range is ``[0, 255]`` for ``uint8`` images.
        fill_mask (tuple[float, ...] | float): Same as fill but only for masks.
        border_mode (int): OpenCV border flag.
        fit_output (bool): If True, the image plane size and position will be adjusted to tightly capture
            the whole image after affine transformation (`translate_percent` and `translate_px` are ignored).
            Otherwise (``False``),  parts of the transformed image may end up outside the image plane.
            Fitting the output shape can be useful to avoid corners of the image being outside the image plane
            after applying rotations. Default: False
        keep_ratio (bool): When True, the original aspect ratio will be kept when the random scale is applied.
            Default: False.
        rotate_method (Literal["largest_box", "ellipse"]): rotation method used for the bounding boxes.
            Should be one of "largest_box" or "ellipse"[1]. Default: "largest_box"
        balanced_scale (bool): When True, scaling factors are chosen to be either entirely below or above 1,
            ensuring balanced scaling. Default: False.

            This is important because without it, scaling tends to lean towards upscaling. For example, if we want
            the image to zoom in and out by 2x, we may pick an interval [0.5, 2]. Since the interval [0.5, 1] is
            three times smaller than [1, 2], values above 1 are picked three times more often if sampled directly
            from [0.5, 2]. With `balanced_scale`, the  function ensures that half the time, the scaling
            factor is picked from below 1 (zooming out), and the other half from above 1 (zooming in).
            This makes the zooming in and out process more balanced.
        p (float): probability of applying the transform. Default: 0.5.

    Targets:
        image, mask, keypoints, bboxes, volume, mask3d

    Image types:
        uint8, float32

    Reference:
        [1] https://arxiv.org/abs/2109.13488""",
            {
                "description": "Augmentation to apply affine transformations to images.\n\n    Affine transformations involve:\n\n        - Translation (\"move\" image on the x-/y-axis)\n        - Rotation\n        - Scaling (\"zoom\" in/out)\n        - Shear (move one side of the image, turning a square into a trapezoid)\n\n    All such transformations can create \"new\" pixels in the image without a defined content, e.g.\n    if the image is translated to the left, pixels are created on the right.\n    A method has to be defined to deal with these pixel values.\n    The parameters `fill` and `fill_mask` of this class deal with this.\n\n    Some transformations involve interpolations between several pixels\n    of the input image to generate output pixel values. The parameters `interpolation` and\n    `mask_interpolation` deals with the method of interpolation used for this.",
                "args": [
                    {"name": "scale", "type": "number, tuple of number or dict", "description": "Scaling factor to use, where ``1.0`` denotes \"no change\" and\n``0.5`` is zoomed out to ``50`` percent of the original size.\n* If a single number, then that value will be used for all images.\n* If a tuple ``(a, b)``, then a value will be uniformly sampled per image from the interval ``[a, b]``.\nThat the same range will be used for both x- and y-axis. To keep the aspect ratio, set\n``keep_ratio=True``, then the same value will be used for both x- and y-axis.\n* If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.\nEach of these keys can have the same values as described above.\nUsing a dictionary allows to set different values for the two axis and sampling will then happen\n*independently* per axis, resulting in samples that differ between the axes. Note that when\nthe ``keep_ratio=True``, the x- and y-axis ranges should be the same."},
                    {"name": "translate_percent", "type": "None, number, tuple of number or dict", "description": "Translation as a fraction of the image height/width\n(x-translation, y-translation), where ``0`` denotes \"no change\"\nand ``0.5`` denotes \"half of the axis size\".\n* If ``None`` then equivalent to ``0.0`` unless `translate_px` has a value other than ``None``.\n* If a single number, then that value will be used for all images.\n* If a tuple ``(a, b)``, then a value will be uniformly sampled per image from the interval ``[a, b]``.\nThat sampled fraction value will be used identically for both x- and y-axis.\n* If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.\nEach of these keys can have the same values as described above.\nUsing a dictionary allows to set different values for the two axis and sampling will then happen\n*independently* per axis, resulting in samples that differ between the axes."},
                    {"name": "translate_px", "type": "None, int, tuple of int or dict", "description": "Translation in pixels.\n* If ``None`` then equivalent to ``0`` unless `translate_percent` has a value other than ``None``.\n* If a single int, then that value will be used for all images.\n* If a tuple ``(a, b)``, then a value will be uniformly sampled per image from\nthe discrete interval ``[a..b]``. That number will be used identically for both x- and y-axis.\n* If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.\nEach of these keys can have the same values as described above.\nUsing a dictionary allows to set different values for the two axis and sampling will then happen\n*independently* per axis, resulting in samples that differ between the axes."},
                    {"name": "rotate", "type": "number or tuple of number", "description": "Rotation in degrees (**NOT** radians), i.e. expected value range is\naround ``[-360, 360]``. Rotation happens around the *center* of the image,\nnot the top left corner as in some other frameworks.\n* If a number, then that value will be used for all images.\n* If a tuple ``(a, b)``, then a value will be uniformly sampled per image from the interval ``[a, b]``\nand used as the rotation value."},
                    {"name": "shear", "type": "number, tuple of number or dict", "description": "Shear in degrees (**NOT** radians), i.e. expected value range is\naround ``[-360, 360]``, with reasonable values being in the range of ``[-45, 45]``.\n* If a number, then that value will be used for all images as\nthe shear on the x-axis (no shear on the y-axis will be done).\n* If a tuple ``(a, b)``, then two value will be uniformly sampled per image\nfrom the interval ``[a, b]`` and be used as the x- and y-shear value.\n* If a dictionary, then it is expected to have the keys ``x`` and/or ``y``.\nEach of these keys can have the same values as described above.\nUsing a dictionary allows to set different values for the two axis and sampling will then happen\n*independently* per axis, resulting in samples that differ between the axes."},
                    {"name": "interpolation", "type": "int", "description": "OpenCV interpolation flag."},
                    {"name": "mask_interpolation", "type": "int", "description": "OpenCV interpolation flag."},
                    {"name": "fill", "type": "tuple[float, ...] | float", "description": "The constant value to use when filling in newly created pixels.\n(E.g. translating by 1px to the right will create a new 1px-wide column of pixels\non the left of the image).\nThe value is only used when `mode=constant`. The expected value range is ``[0, 255]`` for ``uint8`` images."},
                    {"name": "fill_mask", "type": "tuple[float, ...] | float", "description": "Same as fill but only for masks."},
                    {"name": "border_mode", "type": "int", "description": "OpenCV border flag."},
                    {"name": "fit_output", "type": "bool", "description": "If True, the image plane size and position will be adjusted to tightly capture\nthe whole image after affine transformation (`translate_percent` and `translate_px` are ignored).\nOtherwise (``False``),  parts of the transformed image may end up outside the image plane.\nFitting the output shape can be useful to avoid corners of the image being outside the image plane\nafter applying rotations. Default: False"},
                    {"name": "keep_ratio", "type": "bool", "description": "When True, the original aspect ratio will be kept when the random scale is applied."},
                    {"name": "Default", "type": None, "description": "False."},
                    {"name": "rotate_method", "type": 'Literal["largest_box", "ellipse"]', "description": 'rotation method used for the bounding boxes.\nShould be one of "largest_box" or "ellipse"[1]. Default: "largest_box"'},
                    {"name": "balanced_scale", "type": "bool", "description": "When True, scaling factors are chosen to be either entirely below or above 1,\nensuring balanced scaling. Default: False.\nThis is important because without it, scaling tends to lean towards upscaling. For example, if we want\nthe image to zoom in and out by 2x, we may pick an interval [0.5, 2]. Since the interval [0.5, 1] is\nthree times smaller than [1, 2], values above 1 are picked three times more often if sampled directly\nfrom [0.5, 2]. With `balanced_scale`, the  function ensures that half the time, the scaling\nfactor is picked from below 1 (zooming out), and the other half from above 1 (zooming in).\nThis makes the zooming in and out process more balanced."},
                    {"name": "p", "type": "float", "description": "probability of applying the transform. Default: 0.5."},
                ],
                "targets": "image, mask, keypoints, bboxes, volume, mask3d\n\n    Image types:\n        uint8, float32",
                "reference": "[1] https://arxiv.org/abs/2109.13488",
            },
        ),
    ],
)
def test_parse_google_docstring_parametrized(docstring: str, expected: dict[str, Any]) -> None:
    """Test the parse_google_docstring function with various docstrings."""
    result = parse_google_docstring(docstring)

    # Remove the returns key from the result if it's an empty list
    # This allows the tests to pass without modifying all the test cases
    if "returns" in result and result["returns"] == []:
        del result["returns"]

    assert result == expected


@pytest.mark.parametrize(
    "args_text,expected",
    [
        # Test case 1: Simple args
        (
            """param1: Description of param1
            param2 (int): Description of param2""",
            [
                {"name": "param1", "type": None, "description": "Description of param1"},
                {"name": "param2", "type": "int", "description": "Description of param2"},
            ],
        ),

        # Test case 2: Args with multi-line descriptions
        (
            """param1: This is a description
                that spans multiple lines
            param2 (str): Another multi-line
                description""",
            [
                {"name": "param1", "type": None, "description": "This is a description\nthat spans multiple lines"},
                {"name": "param2", "type": "str", "description": "Another multi-line\ndescription"},
            ],
        ),

        # Test case 3: Complex types
        (
            """param1 (list[dict[str, Any]]): Complex type
            param2 (tuple[int, str, bool | None]): Another complex type""",
            [
                {"name": "param1", "type": "list[dict[str, Any]]", "description": "Complex type"},
                {"name": "param2", "type": "tuple[int, str, bool | None]", "description": "Another complex type"},
            ],
        ),
    ],
)
def test_parse_args_section(args_text: str, expected: list[dict[str, str | None]]) -> None:
    result = _parse_args_section(args_text)
    assert result == expected
