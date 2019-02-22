from flask import g, jsonify
from marshmallow import fields
import networkx as nx
from webargs.flaskparser import use_args

from .shortest_path import shortest_path, NoPathError


def add_view(app, profile):
    # TODO: validate profile name - must be url path-compatible
    url = "/directions/{}.json".format(profile.name)

    # TODO: do any kind of input validation (at least handle errors)
    args = {arg["name"]: arg["type"] for arg in profile.args}
    args["lon1"] = fields.Float()
    args["lat1"] = fields.Float()
    args["lon2"] = fields.Float()
    args["lat2"] = fields.Float()

    @use_args(args)
    def route(args):
        try:
            lon1 = args.pop("lon1")
            lat1 = args.pop("lat1")
            lon2 = args.pop("lon2")
            lat2 = args.pop("lat2")
        except KeyError:
            return jsonify({"status": "Failed", "msg": "Missing location inputs"}), 400
        # lon1 = -122.351252
        # lat1 = 47.649860
        # lon2 = -122.354380
        # lat2 = 47.652136
        cost_function = profile.cost_function_generator(**args)

        try:
            cost, path, edges = shortest_path(
                g.G, lon1, lat1, lon2, lat2, cost_function
            )
        except NoPathError:
            return jsonify({"status": "Failed", "msg": "No path"})

        directions = profile.directions(cost, path, edges)

        return jsonify(directions)

    app.add_url_rule(url, "directions-{}".format(profile.name), route)
