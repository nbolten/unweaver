# Contributing to `unweaver`

`unweaver` is developed using
[`poetry`](https://python-poetry.org/docs/pyproject/). Most of the development
setup can be obtained by cloning this repository and running `poetry install`.

## Pre-commit hooks

Style and `setup.py` file generation are handled using `pre-commit` hooks.

To enable the hooks registered in this repository, run
`poetry run pre-commit install`. Note that `poetry run` must also be prepended
to `git commit` (or the environment shell must be enabled with `poetry shell`).
Otherwise, you will get "command not found" errors.

### Dealing with pre-commit hook failures

Pre-commit hooks attempt to run certain checks before certain git actions,
usually a commit. If they run their action and modify a file, a 'FAIL' message
will flash during the `git commit` process. This is often a good thing,
indicating that you need to add the modified files and reattempt committing.

However, if the `mypy` or `pytest` hooks fail, this means you will need to fix
the problems identified before attempting another commit.


### Type hinting

Type hinting is enforced on commit with a `mypy` pre-commit hook. The settings
for type hinting can be found in `pyproject.toml`.

### `pytest`

`pytest` is run as a pre-commit hook on the `tests` directory. This decreases
the chance that your changes will break existing functionality.

### Code style

The `unweaver` package is developed using the
[`black`](https://github.com/psf/black) autoformatter. `black` is automaticaly
installed with `poetry install`.

### Generating a setup.py file

`unweaver` includes a `setup.py` file for legacy build support. It is
(re)generated whenever the `pyproject.toml` or `poetry.lock` files are changed
via a pre-commit hook.

### Generating requirements.txt files

For legacy purposes, `requirements.txt` and `requirements-dev.txt` files are
automatically generated via a pre-commit hook whenever the `pyproject.toml` or
`poetry.lock` files are changed.
