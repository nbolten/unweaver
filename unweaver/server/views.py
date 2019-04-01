from flask import g, jsonify
from marshmallow import fields
import networkx as nx
from webargs.flaskparser import use_args

from ..network_queries import candidates_dwithin
from ..algorithms.shortest_path import (
    route_legs,
    waypoint_legs,
    _choose_candidate,
    NoPathError,
)
from ..algorithms.shortest_path_tree import shortest_path_tree


def add_directions_view(app, profile):
    # TODO: validate profile name - must be url path-compatible
    url = "/directions/{}.json".format(profile.name)
    # TODO: do any kind of input validation (at least handle errors)
    arg_schema = {arg["name"]: arg["type"] for arg in profile.args}
    arg_schema["lon1"] = fields.Float()
    arg_schema["lat1"] = fields.Float()
    arg_schema["lon2"] = fields.Float()
    arg_schema["lat2"] = fields.Float()

    @use_args(arg_schema)
    def directions(args):
        if g.get("failed_graph", False):
            return jsonify(
                {"status": "NoGraph", "message": "Internal graph read error."}
            )

        try:
            lon1 = args.pop("lon1")
            lat1 = args.pop("lat1")
            lon2 = args.pop("lon2")
            lat2 = args.pop("lat2")
        except KeyError:
            # FIXME: should produce specific exceptions / status to pass to directions
            # function for consistent response messages.
            return (
                jsonify({"status": "MissingInput", "msg": "Missing location inputs"}),
                400,
            )

        if hasattr(profile, "cost_function_generator"):
            cost_function_generator = profile.cost_function_generator
        else:
            cost_function_generator = default_cost_function_generator

        cost_function = cost_function_generator(**args)

        if hasattr(profile, "directions_function"):
            directions_function = profile.directions
        else:
            directions_function = default_directions_function

        trip = get_trip(g.G, lon1, lat1, lon2, lat2, cost_function, directions_function)

        return jsonify(trip)

    app.add_url_rule(url, "directions-{}".format(profile.name), directions)


def add_tree_view(app, profile):
    url = "/tree/{}.json".format(profile.name)

    arg_schema = {arg["name"]: arg["type"] for arg in profile.args}
    arg_schema["lon"] = fields.Float()
    arg_schema["lat"] = fields.Float()
    arg_schema["maxCost"] = fields.Float()

    @use_args(arg_schema)
    def tree(args):
        if g.get("failed_graph", False):
            return jsonify(
                {"status": "NoGraph", "message": "Internal graph read error."}
            )
        # TODO: partial traversal rule(s) - when maxCost is reached, should the tree
        # extend a little farther? Easy when cost is distance, ambiguous otherwise.
        # Expose enough data so that user can do that?
        try:
            lon = args.pop("lon")
            lat = args.pop("lat")
        except KeyError:
            return (
                jsonify({"status": "MissingInput", "msg": "Missing location inputs"}),
                400,
            )

        try:
            maxCost = args.pop("maxCost")
        except KeyError:
            return (
                jsonify(
                    {"status": "MissingInput", "msg": "Missing maximum cost input"}
                ),
                400,
            )

        if hasattr(profile, "cost_function_generator"):
            cost_function_generator = profile.cost_function_generator
        else:
            cost_function_generator = default_cost_function_generator

        cost_function = cost_function_generator(**args)

        if hasattr(profile, "tree"):
            tree_function = profile.tree
        else:
            tree_function = default_tree_function

        tree = get_tree(g.G, lon, lat, cost_function, tree_function, maxCost)

        return jsonify(tree)

    app.add_url_rule(url, "tree-{}".format(profile.name), tree)


def add_views(app, profile):
    add_directions_view(app, profile)
    add_tree_view(app, profile)


def get_trip(G, lon1, lat1, lon2, lat2, cost_function, directions_function):
    legs = waypoint_legs(G, [[lon1, lat1], [lon2, lat2]], cost_function)
    for i, (wp1, wp2) in enumerate(legs):
        if wp1 is None:
            return {
                "status": "InvalidWaypoint",
                "msg": "Cannot route from waypoint {}".format(i + 1),
                "status_data": {"index": i},
            }
        if wp2 is None:
            return {
                "status": "InvalidWaypoint",
                "msg": "Cannot route to waypoint {}".format(i + 2),
                "status_data": {"index": i + 1},
            }

    try:
        cost, path, edges = route_legs(G, legs, cost_function)
    except NoPathError:
        return {"status": "NoPath", "msg": "No path found."}

    origin = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon1, lat1]},
        "properties": {},
    }
    destination = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon2, lat2]},
        "properties": {},
    }

    directions = directions_function(origin, destination, cost, path, edges)

    return directions


def get_tree(G, lon, lat, cost_function, tree_function, maxCost):
    """Calculate shortest-path tree using Dijkstra's method, up to some maximum weight.
    The results can be used to create things like isochrones and walksheds.

    """
    candidates = candidates_dwithin(G, lon, lat, 4, is_destination=False, dwithin=5e-4)

    if candidates is None:
        return {
            "status": "InvalidWaypoint",
            "msg": "No on-graph start point from given location.",
            "status_data": {"index": -1},
        }

    candidate = _choose_candidate(candidates, cost_function)

    # TODO: unique message for this case?
    if candidate is None:
        return {
            "status": "InvalidWaypoint",
            "msg": "No on-graph start point from given location.",
            "status_data": {"index": -1},
        }

    costs, paths, edges = shortest_path_tree(G, candidate, cost_function, maxCost)

    tree = tree_function(costs, paths, edges)

    return tree


def default_cost_function_generator():
    def cost_function(u, v, d):
        return d["_length"]

    return cost_function


def default_directions_function(origin, destination, cost, nodes, edges):
    return {
        "origin": origin,
        "destination": destination,
        "total_cost": cost,
        "edges": edges,
    }


def default_tree_function(costs, paths, edges):
    """Return the minimum costs to nodes in the graph.
    """
    # FIXME: coordinates are derived from node string, should be derived from
    # node metadata (add node coordinates upstream in entwiner).
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(n) for n in node.split(",")],
                },
                "properties": {"cost": cost},
            }
            for node, cost in costs.items()
        ],
    }
