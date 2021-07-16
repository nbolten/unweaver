from typing import List, Optional, Tuple, Union

import flask
from flask import g

from unweaver.server.app import create_app
from unweaver.graph import get_graph
from unweaver.parsers import parse_profiles
from .views import add_views


Header = Tuple[str, str]


def run_app(
    path: str,
    host: str = "localhost",
    port: Union[str, int] = 8000,
    add_headers: List[Header] = None,
    debug: bool = False,
) -> None:
    app = setup_app(path, add_headers, debug)
    app.run(host=host, port=port)


def setup_app(
    path: str, add_headers: Optional[List[Header]] = None, debug: bool = False
) -> flask.Flask:
    if add_headers is None:
        # Using new variable name to make mypy happy
        headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
            ("Access-Control-Allow-Methods", "GET"),
        ]
    else:
        headers = add_headers

    profiles = parse_profiles(path)

    app = create_app()

    # TODO: handle 404, 400

    # Share graph db connection
    @app.before_request
    def before_request() -> None:
        # Create a db connection
        try:
            # TODO: any issues with concurrent connections? Should we share
            # one db connection (DiGraphDB instance) vs. reconnecting?
            if "G" not in g:
                g.G = get_graph(path)
        except Exception as e:
            # TODO: Check this during startup as well to detect graph issues
            print(e)
            g.failed_graph = True

    @app.after_request
    def after_request(
        response: flask.wrappers.Response,
    ) -> flask.wrappers.Response:
        for header, value in headers:
            response.headers[header] = value
        return response

    @app.teardown_request
    def teardown_request(exception: Exception = None) -> None:
        # TODO: add CORS info?
        g.G = None

    for profile in profiles:
        add_views(app, profile)

    return app
