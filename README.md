# Unweaver

![Unweaver logo](docs/assets/logo.svg)

Unweaver is a routing engine focused on flexibility. It can read many data formats
(including OpenStreetMap), find shortest-path routes via a web API, and allows
completely customizable combinations of cost functions and directions specifications,
summarized in "profiles". Unweaver's costing strategy includes dynamics (as opposed
to precalculated) edge costs for when profiles need to be heavily parameterized on a
per-user basis.

If you want to use `unweaver` as a command line application or library, see
the [installation](#installation) section. If you want to contribute to the
development of `unweaver` itself, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Installation

`unweaver` can be used as a command line application or a library that can be
used to develop new applications or analyze geospatial networks in a Jupyter
notebook.

Regardless of the way you install and use `unweaver`, it has a set of
non-Python dependencies that will need to be installed on your system first.

- [Go here](#install-non-python-dependencies) to get instructions on installing
the non-Python dependencies required by `unweaver`.

- [Go here](#install-`unweaver`-as-a-command-line-application ) to get
instructions on installing `unweaver` as a command line application.

- [Go here](#install-`unweaver`-as-a-library) to get instructions on installing
`unweaver` as a library.

### Install and configure non-python dependencies

Unweaver depends on the following software packages in order to run:

- SQLite: A file-based SQL database and the format of the routable GeoPackage
created by `unweaver`.
- SpatiaLite: An extension for SQLite that adds geospatial support.
- GDAL: A common geospatial library for reading/writing geodata formats.
- proj4: A common geospatial library for managing map (re)projections.

#### Platform-specific installation instructions

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

### Install `unweaver` as a command line application

Unweaver is build with the `poetry` toolkit. When Unweaver is properly released on
PyPI, installing the module will be as simple as running `poetry add unweaver`. For
now, it must be installed from this repository. This can be done using either with
`poetry` (ideal) or `pip` (for backwards compatibility).

#### With `pip`:

This can be done with a one-liner:

    pip install git+https://github.com/nbolten/unweaver.git@f9f4bed#egg=unweaver

Where the `@` entry is the commit. This can also be set to a branch name.

### Install `unweaver` as a library

#### With `poetry`:

Edit your `pyproject.toml` to include a line like this under
[tool.poetry.dependencies]:

    unweaver = {git = "https://github.com/nbolten/unweaver.git", rev = "f9f4bed"}

You can choose `rev` to be whatever git commit hash you want to use.

#### With `pip`:

This can be done with a one-liner:

    pip install git+https://github.com/nbolten/unweaver.git@f9f4bed#egg=unweaver

Where the `@` entry is the commit. This can also be set to a branch name.

## Data format flexibility

Unweaver can ingest any linear (LineString) format processable by GDAL,
including GeoJSON and Shapefiles. The primary graph data structure created from
these data is a portable, routable [GeoPackage](https://www.geopackage.org/).

This GeoPackage stores network information in an edge list format using two
feature tables: `nodes` and `edges`.

`nodes` has a primary key (`fid`), a unique node id (`_n`), and a Point
geometry column (`geom` by default). The `nodes` table can be extended to
include any number of other columns, but `unweaver` does not automatically do
so during the build step at this time.

`edges` has a primary key (`fid`) a unique pair of node ids that describe the
edge (`_u` and `_v`), and a LineString geometry column. The `edges` table is
automatically extended during the build process, transforming input linear data
properties into column names and values. For example, a "length" numeric
property in the input data will result in the creation of a numeric "length"
column populated with the associated values. The use of `_u` and `_v` to
uniquely identify an edge means that `unweaver` describes a digraph and not
a multidigraph. Multidigraph support is planned for the near future, as
real-world networks frequently have multiple paths starting and ending at the
same location.

## Running the example

### Get the data

The example expects there to be a GeoJSON file representing a sidewalk network
in the `example/layers` directory. You may need to create the `layers`
directory. Unfortunately, we don't have a consistent place to put this example
data yet, so to get it please request it from someone at the Taskar Center or
from the repo author.

### Build the graph

Run `unweaver build ./example` in the main repo. If you are running Unweaver
as a developer using `poetry`, run `poetry run python -m unweaver build
./example`.

This will create `example/graph.gpkg`, a GeoPackage that Unweaver can use for
network queries, including routing.

### Weight the graph

Run `unweaver weight ./example` in the main repo. If you are running Unweaver
as a developer using `poetry`, run `poetry run python -m unweaver weight
./example`.

This will update `example/graph.gpkg` with a precalculated weight value for a
(necessarily non-representative) stereotyped manual wheelchair user.

### Run the web server

Run `unweaver serve ./example` in the main repo. If you are running Unweaver
as a developer using `poetry`, run `poetry run python -m unweaver server
./example`.

This will run a Flask web server to which requests to the
`/shortest_path/<profile>.json`, `/shortest_path_tree/<profile>.json`, and
`/reachable_tree/<profile>.json` endpoints may be sent.

## Troubleshooting

### Can't load extensions on a Mac

Unweaver needs to load the SpatiaLite extension for SQLite3, but the version of
SQLite3 that comes with Macs cannot load extensions by default. You will need
to:

1. Install sqlite3 from a third party, such as homebrew: `brew install sqlite3`
2. After installing (or after running `brew link sqlite3`), follow the
instructions to set up your PATH and library flag locations to be the homebrew
ones. This will involve editing your shell's config, usually `.bashrc` or
`.zshrc`.
3. Ensure that your environment is set up correctly by opening a new terminal
and running `which sqlite3`. If the path is `/usr/bin/sqlite3` and not a path
with the word `Cellar` in it, your environment is not correct and you need to
(1) run `source .bashrc` (or `.zshrc`) to enable it in your current
environment, then test again, and (2) troubleshoot your environment until it
automatically loads your shell config automatically (sometimes a restart is
required).
4. Install Python such that it links to this sqlite3 or builds its own with
extension support. `pyenv` can be configured to do so with some flags. Example
[here](https://github.com/pyenv/pyenv/issues/1702).
5. Use this version of Python to set up your `poetry` environment below using
`poetry env <path/to/your/pyenv/bin/python` or
`<path/to/your/pyenv/bin/python> -m venv venv` to create a non-poetry custom
virtual environment.
