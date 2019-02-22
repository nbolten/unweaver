"""unweaver CLI."""
import click

from unweaver.run import run_app
from unweaver.build import build_graph


@click.group()
def unweaver():
    pass


@unweaver.command()
@click.argument("directory", type=click.Path("r"))
def build(directory):
    click.echo("Building graph...")
    # TODO: catch errors in starting server
    # TODO: spawn process?
    build_graph(directory)
    click.echo("Done.")


@unweaver.command()
@click.argument("directory", type=click.Path("r"))
@click.option("--host", "-h")
@click.option("--port", "-p")
@click.option("--debug", is_flag=True)
def run(directory, host="localhost", port=8000, debug=False):
    click.echo("Starting server in {}...".format(directory))
    # TODO: catch errors in starting server
    # TODO: spawn process?
    run_app(directory, host=host, port=port, debug=debug)
