"""unweaver CLI."""
import os

import click
import fiona

import entwiner
from unweaver.constants import DB_PATH
from unweaver.build import build_graph, get_layers_paths
from unweaver.parsers import parse_profiles
from unweaver.server import run_app
from unweaver.weight import precalculate_weight


@click.group()
def unweaver():
    pass


@unweaver.command()
@click.argument("directory", type=click.Path("r"))
@click.option("--precision", default=7)
@click.option("--changes-sign", multiple=True)
def build(directory, precision, changes_sign):
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
@click.argument("directory", type=click.Path("r"))
def weight(directory):
    # TODO: catch errors in starting server
    # TODO: spawn process?
    profiles = parse_profiles(directory)
    G = entwiner.DiGraphDB(path=os.path.join(directory, DB_PATH))
    n_profiles = len([p for p in profiles if p["precalculate"]])
    n = G.size() * n_profiles
    with click.progressbar(length=n, label="Computing static weights") as bar:
        for profile in profiles:
            if profile["precalculate"]:
                weight_column = "_weight_{}".format(profile["id"])
                precalculate_weight(
                    G, weight_column, profile["cost_function"], counter=bar
                )


@unweaver.command()
@click.argument("directory", type=click.Path("r"))
@click.option("--host", "-h", default="localhost")
@click.option("--port", "-p", default=8000)
@click.option("--debug", is_flag=True)
def serve(directory, host, port, debug=False):
    click.echo("Starting server in {}...".format(directory))
    # TODO: catch errors in starting server
    # TODO: spawn process?
    run_app(directory, host=host, port=port, debug=debug)
