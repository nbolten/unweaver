from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    # TODO: handle 400 and 422

    return app
