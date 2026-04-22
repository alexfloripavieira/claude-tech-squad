## Stack Notes

- Prefer the test runner declared in `pyproject.toml`, `tox.ini`, or existing docs.
- Keep virtual environment and dependency lockfile changes explicit.
- Do not introduce broad dependency upgrades during feature work unless required.

## Default Commands

```bash
python -m pytest
python -m pytest
python -m ruff check .
python -m build
```
