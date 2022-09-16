# Welcome to Unweaver

<img src="assets/logo.svg" alt="Unweaver logo" alignt="left" style="width:100px;margin-right:16px"/>
Unweaver is a flexible routing engine intended for research and production
routing and network analysis applications. Why use Unweaver?

* Unweaver stitches together a routable network from geospatial data and stores
it as a routable GeoPackage, a portable SQLite database and OGC standard. You
can save, share, and query your networks using any open source tooling that
understands SQLite or GeoPackages.

* Unweaver leverages user-defined Python cost functions that are evaluated
at runtime, so you can define and rapidly iterate on your shortest-path graph
traversal using any amount of custom logic.

* Unweaver provides a [`networkx`](https://networkx.github.io/)-compatible view into
your routable GeoPackage so that you can traverse and query it like an
in-memory graph*.

* Unweaver provides a web server that creates JSON-returning web endpoints
using simple JSON configuration files (routing profiles).

* Unweaver can be used as a command line tool or as a library in production
applications or Jupyter notebooks.

\* Not all `networkx` algorithms have been tested with Unweaver yet.

## Commands

* `unweaver build` - Build a project directory into a routable GeoPackage.
* `unweaver weight` - Calculate static weights for edges in the routable
GeoPackage.
* `unweaver serve` - Start the web API server (shortest-path, shortest-path
tree, and reachable tree JSON endpoints).
* `mkdocs --help` - Print help message and exit.

## Project layout

    mkdocs.yml      # The configuration file.
    poetry.lock     # Python dependencies lockfile.
    pyproject.toml  # Primary package definition config.
    CONTRIBUTING.md # Documentation for contributing to unweaver.
    Dockerfile      # For reproducible builds and deployments with `docker`.
    LICENSE         # The license for unweaver (Apache-2.0).
    README.md       # README for the unweaver.
    TODO.md         # Project planning (for lack of a Kanban...).
    docs/
        index.md    # The documentation homepage.
        ...         # Other markdown pages, images and other files.
    example/
        ...         # Example unweaver project directory contents
    tests/          # Project tests (for development)
    unweaver/       # The unweaver library
