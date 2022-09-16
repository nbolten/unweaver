"""unweaver CLI."""
import os
from typing import List

import click
import fiona  # type: ignore

from unweaver.constants import DB_PATH
from unweaver.build.build_graph import build_graph
from unweaver.build.get_layers_paths import get_layers_paths
from unweaver.graphs import DiGraphGPKG
from unweaver.parsers import parse_profiles
from unweaver.server import run_app
from unweaver.weight import precalculate_weight


@click.group()
def unweaver() -> None:
    pass


@unweaver.command()
@click.argument("project_directory", type=click.Path())
@click.option(
    "--precision",
    default=7,
    help="Latitude-longitude coordinate rounding precision for whether dataset polylines are connected.",
)
@click.option(
    "--changes-sign",
    multiple=True,
    help="A property whose sign should be flipped when reversing an edge. "
    "Example: a positive steepness/incline field value should be made negative for the reverse edge.",
)
def build(
    project_directory: str, precision: int, changes_sign: List[str]
) -> None:
    """Build a routable GeoPackage (graph.gpkg in the project directory) from
    the data in the `{project}/layers` directory.
    """
    click.echo("Estimating feature count...")
    # TODO: catch errors in starting server
    # TODO: spawn process?

    layers_paths = get_layers_paths(project_directory)

    n = 0
    for path in layers_paths:
        with fiona.open(path) as c:
            n += len(c)
            click.echo(f"    counted features in {path}")
    # Two edges per feature - forward and reverse
    n *= 2

    click.echo(f"Creating {n} edges from {n // 2} features")

    with click.progressbar(length=n, label="Importing features") as bar:
        build_graph(
            project_directory,
            precision=precision,
            changes_sign=changes_sign,
            counter=bar,
        )

    click.echo("Done.")


@unweaver.command()
@click.argument("project_directory", type=click.Path())
def weight(project_directory: str) -> None:
    """Precalculate all static weights for all profiles in a project."""
    # TODO: catch errors in starting server
    # TODO: spawn process?
    click.echo("Collecting data for static weighting...")
    profiles = parse_profiles(project_directory)
    G = DiGraphGPKG(path=os.path.join(project_directory, DB_PATH))
    n_profiles = len([p for p in profiles if p.get("precalculate", False)])
    n = G.size() * n_profiles
    with click.progressbar(length=n, label="Computing static weights") as bar:
        for profile in profiles:
            if profile["precalculate"]:
                weight_column = f"_weight_{profile['id']}"
                precalculate_weight(
                    G, weight_column, profile["cost_function"], counter=bar
                )


@unweaver.command()
@click.argument("project_directory", type=click.Path())
@click.option(
    "--host",
    "-h",
    default="localhost",
    help="Host on which to run the server.",
)
@click.option(
    "--port", "-p", default=8000, help="Port on which to run the server."
)
@click.option(
    "--debug",
    is_flag=True,
    help="Whether to run the server with in-browser error tracebacks.",
)
def serve(
    project_directory: str, host: str, port: str, debug: bool = False
) -> None:
    """Run a web server with auto-generated web API endpoints that return
    JSON for shortest-path routes, shortest-path trees, and reachable trees
    for every profile in a project.
    """
    click.echo(f"Starting server in {project_directory}...")
    # TODO: catch errors in starting server
    # TODO: spawn process?
    run_app(project_directory, host=host, port=port, debug=debug)
