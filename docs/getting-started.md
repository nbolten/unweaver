# Installation

## With Docker

    docker build -t unweaver https://github.com/nbolten/unweaver.git#main

## With pip or poetry

### Non-Python prerequisites

Unweaver depends on the following software packages in order to run:

- SQLite: A file-based SQL database and the format of the routable GeoPackage
created by `unweaver`.
- SpatiaLite: An extension for SQLite that adds geospatial support.
- GDAL: A common geospatial library for reading/writing geodata formats.
- proj4: A common geospatial library for managing map (re)projections.

#### Platform-specific prerequisites installation

*On a Mac using Homebrew:*

    brew install sqlite libspatialite gdal proj

(See [this troubleshooting on Mac](#can't-load-extensions-on-a-mac) section if
you still can't load SQLite extensions with `unweaver`)

*On a debian-based distribution:*

    apt install libsqlite3 libspatialite libgdal libproj

#### Enable SQLite extension support in Python

Python may be distributed with or without SQLite and extensions support. For
example, if you are using [pyenv](https://github.com/pyenv/pyenv) to manage
your Python installation, you will need to ensure it is
[built with flags](https://github.com/pyenv/pyenv/issues/1702) enable SQLite
support.

Unweaver is build with the `poetry` toolkit. When Unweaver is properly released on
PyPI, installing the module will be as simple as running `poetry add unweaver`. For
now, it must be installed from this repository. This can be done using either with
`poetry` (ideal) or `pip` (for backwards compatibility).

### With `pip`:

This can be done with a one-liner:

    pip install git+https://github.com/nbolten/unweaver.git@f9f4bed#egg=unweaver

Where the `@` entry is the commit. This can also be set to a branch name.

### With `poetry`:

Edit your `pyproject.toml` to include a line like this under
[tool.poetry.dependencies]:

    unweaver = {git = "https://github.com/nbolten/unweaver.git", rev = "f9f4bed"}

You can choose `rev` to be whatever git commit hash you want to use.
