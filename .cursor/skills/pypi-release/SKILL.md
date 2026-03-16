---
name: pypi-release
description: Cut a PyPI release - bump version, build, upload. Use when releasing, publishing to PyPI, bumping version, or creating a new release.
---

# PyPI Release (Project)

## Workflow

1. **Bump version** in `pyproject.toml`:
   ```toml
   version = "0.0.10"  # was 0.0.9
   ```

2. **Commit and push**, create GitHub release (tag + publish)

3. **CI runs** `upload_to_pypi.yml` on `release: published`:
   - Builds with `python -m build`
   - Uploads with `twine upload dist/*`
   - Uses `PYPI_API_TOKEN` secret

## Manual build/upload (if needed)

```bash
pip install build twine
python -m build
twine upload dist/*
```

Requires `TWINE_USERNAME=__token__` and `TWINE_PASSWORD` (PyPI token).

## CI job (upload_to_pypi.yml)

- Trigger: `release: types: [published]`
- Removes `tests` and `benchmark` before build
- Uses `secrets.PYPI_API_TOKEN`
