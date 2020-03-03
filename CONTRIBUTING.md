# Contributing to `unweaver`

Entwiner is developed using [`poetry`](https://python-poetry.org/docs/pyproject/). Most
of the development setup can be obtained by cloning this repository and running `poetry
install`.

## Pre-commit hooks

Style and `setup.py` file generation are handled using `pre-commit` hooks.

To enable the hooks registered in this repository, run
`poetry run pre-commit install`.

### Code style

The `unweaver` package is developed using the [`black`](https://github.com/psf/black)
autoformatter. `black` is automaticaly installed with `poetry install`.

### Generating a setup.py file

`unweaver` includes a `setup.py` file for legacy build support. As of writing,
`poetry` does not yet have a native way to directly manage a `setup.py` file, so

### Generating requirements.txt files

For legacy purposes, requirements.txt and requirements-dev.txt files are automatically
generated using `poetry`. No setup is required if you installed your environment using
`poetry install`.
