# super-dl

Scaffold for a Python project using Poetry.

Quick start

- Install Poetry: https://python-poetry.org/docs/
- Create a venv and install dependencies:

  poetry install

- Run tests:

  poetry run pytest

- Run CLI entrypoint:

  poetry run super-dl --help

Example: download from influencersgonewild

```bash
# Download a page and extract the mp4, saving to default filename
poetry run super-dl --site influencersgonewild "https://influencersgonewild.com/some-post"

# Download and save to a specific file
poetry run super-dl --site influencersgonewild "https://influencersgonewild.com/some-post" -o output.mp4
```

Install with pip (editable / development)


```bash
# install with pip (uses setup.cfg/setup.py)
pip install -e .

# then run from anywhere
super-dl --site influencersgonewild "https://influencersgonewild.com/some-post" -o output.mp4
```

Build wheel and install

```bash
python -m build  # requires 'build' package
pip install dist/*.whl
```
