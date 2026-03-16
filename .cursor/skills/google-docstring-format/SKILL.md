---
name: google-docstring-format
description: Write and fix Google-style docstrings that pass the project's check-docstrings pre-commit hook. Use when writing docstrings, fixing check-docstrings failures, ReferenceFormatError, InvalidTypeAnnotationError, or when docstring validation fails.
---

# Google Docstring Format (Project)

## Config (pyproject.toml)

```toml
[tool.docstring_checker]
paths = ["google_docstring_parser", "tools"]
require_param_types = true
check_references = true
check_type_consistency = true
exclude_files = ["test_malformed_docstrings.py"]
```

## Rules

### Args
- Every parameter **must** have a type: `param_name (type): description`
- Use `list[str]` not `list`; `dict[str, Any]` not `dict`. Bare collections fail validation.
- Types must match function annotations when `check_type_consistency` is true.

### Returns
- Use `Returns:` (plural), not `Return:` or `return:` or `returns:`
- Must have type: `Returns:\n    dict[str, Any]: Description`
- Or just `None` if no return value.

### References
- **Single reference**: no leading dash
  ```
  Reference:
      Paper title: https://example.com/paper
  ```
- **Multiple references**: all must start with `-`
  ```
  References:
      - First paper: https://example.com/paper1
      - Second paper: https://example.com/paper2
  ```
- Each reference needs non-empty `description` and `source` (colon-separated).

### Type validation
- `dict`, `list`, `set`, `tuple`, etc. require brackets: `list[str]`, `dict[str, int]`
- No unclosed parentheses in param types
- Brackets must be balanced and matched

## Fixing errors

| Error | Fix |
|-------|-----|
| `Parameter 'x' is missing a type` | Add `(type)` after param name |
| `Collection 'list' must include element types` | Use `list[str]` not `list` |
| `missing_dash` / `dash_in_single` | Single ref: no dash. Multiple refs: all start with `-` |
| `Invalid section name 'return:'` | Use `Returns:` |
| `Returns section is missing type annotation` | Add type before colon in Returns |

## Verify

```bash
pre-commit run check-docstrings --all-files
```
