from flask import g, jsonify
from marshmallow import fields
import networkx as nx
from webargs.flaskparser import use_args

from .trip import get_trip


def add_view(app, profile):
    # TODO: validate profile name - must be url path-compatible
    url = "/directions/{}.json".format(profile.name)

    # TODO: do any kind of input validation (at least handle errors)
    arg_schema = {arg["name"]: arg["type"] for arg in profile.args}
    arg_schema["lon1"] = fields.Float()
    arg_schema["lat1"] = fields.Float()
    arg_schema["lon2"] = fields.Float()
    arg_schema["lat2"] = fields.Float()

    @use_args(arg_schema)
    def route(args):
        trip = get_trip(g.G, profile, args)

        return jsonify(trip)

    app.add_url_rule(url, "directions-{}".format(profile.name), route)
