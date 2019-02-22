import os

import entwiner
from flask import g

from unweaver.app import create_app
from unweaver.graph import get_graph
from unweaver.parsers import parse_profiles
from unweaver.views import add_view


def run_app(path, host="localhost", port=8000, add_headers=None, debug=False):
    if add_headers is None:
        add_headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
            ("Access-Control-Allow-Methods", "GET"),
        ]

    profiles = parse_profiles(path)

    app = create_app()

    if debug:
        app.config["DEBUG"] = True

    # Share graph db connection
    @app.before_request
    def before_request():
        # Create a db connection
        try:
            # TODO: any issues with concurrent connections? Should we share one db
            # connection (DiGraphDB instance) vs. reconnecting?
            g.G = get_graph(path)
        except:
            # TODO: Catch a useful exception?
            pass

    @app.teardown_request
    def after_request(response):
        # TODO: add CORS info?
        g.G.graphdb.conn.close()
        g.G = None
        # FIXME: add headers to appropriate context manager in Flask 1.0
        # for header in add_headers:
        #     response.headers.add(*header)

    for profile in profiles:
        add_view(app, profile)

    app.run(host=host, port=port)
