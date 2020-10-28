from flask import g, jsonify

from .app import create_app
from ..graph import get_graph
from ..parsers import parse_profiles
from .views import add_views


def run_app(path, host="localhost", port=8000, add_headers=None, debug=False):
    app = setup_app(path, add_headers, debug)
    app.run(host=host, port=port)


def setup_app(path, add_headers=None, debug=False):
    if add_headers is None:
        add_headers = [
            ("Access-Control-Allow-Origin", "*"),
            ("Access-Control-Allow-Headers", "Content-Type,Authorization"),
            ("Access-Control-Allow-Methods", "GET"),
        ]

    profiles = parse_profiles(path)

    app = create_app()

    # FIXME: Redundant!
    # Return validation errors as JSON
    @app.errorhandler(422)
    @app.errorhandler(400)
    def handle_error(err):
        headers = err.data.get("headers", None)
        messages = err.data.get("messages", ["Invalid request."])
        if headers:
            return jsonify({"errors": messages}), err.code, headers
        else:
            return jsonify({"errors": messages}), err.code

    if debug:
        app.config["DEBUG"] = True

    # Share graph db connection
    @app.before_request
    def before_request():
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
    def after_request(response):
        for header, value in add_headers:
            response.headers[header] = value
        return response

    @app.teardown_request
    def teardown_request(exception):
        # TODO: add CORS info?
        # g.G.sqlitegraph.conn.close()
        g.G = None

    for profile in profiles:
        add_views(app, profile)

    return app
