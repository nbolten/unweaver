"""unweaver CLI."""
import os
from typing import List

import click
import fiona

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
@click.argument("directory", type=click.Path())
@click.option("--precision", default=7)
@click.option("--changes-sign", multiple=True)
def build(directory: str, precision: int, changes_sign: List[str]) -> None:
    click.echo("Estimating feature count...")
    # TODO: catch errors in starting server
    # TODO: spawn process?

    layers_paths = get_layers_paths(directory)

    n = 0
    for path in layers_paths:
        with fiona.open(path) as c:
            n += len(c)
    # Two edges per feature - forward and reverse
    n *= 2

    with click.progressbar(length=n, label="Importing features") as bar:
        build_graph(
            directory,
            precision=precision,
            changes_sign=changes_sign,
            counter=bar,
        )

    click.echo("Done.")


@unweaver.command()
@click.argument("directory", type=click.Path())
def weight(directory: str) -> None:
    # TODO: catch errors in starting server
    # TODO: spawn process?
    profiles = parse_profiles(directory)
    G = DiGraphGPKG(path=os.path.join(directory, DB_PATH))
    n_profiles = len([p for p in profiles if p["precalculate"]])
    n = G.size() * n_profiles
    with click.progressbar(length=n, label="Computing static weights") as bar:
        for profile in profiles:
            if profile["precalculate"]:
                weight_column = f"_weight_{profile['id']}"
                precalculate_weight(
                    G, weight_column, profile["cost_function"], counter=bar
                )


@unweaver.command()
@click.argument("directory", type=click.Path())
@click.option("--host", "-h", default="localhost")
@click.option("--port", "-p", default=8000)
@click.option("--debug", is_flag=True)
def serve(directory: str, host: str, port: str, debug: bool = False) -> None:
    click.echo(f"Starting server in {directory}...")
    # TODO: catch errors in starting server
    # TODO: spawn process?
    run_app(directory, host=host, port=port, debug=debug)
