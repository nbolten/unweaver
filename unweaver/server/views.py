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
from ..algorithms.shortest_paths import shortest_paths
from ..algorithms.reachable import reachable


def add_directions_view(app, profile):
    # TODO: validate profile name - must be url path-compatible
    url = "/directions/{}.json".format(profile.name)
    # TODO: do any kind of input validation (at least handle errors)
    arg_schema = {}
    if hasattr(profile, "args"):
        for arg in profile.args:
            arg_schema[arg["name"]] = arg["type"]
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

        trip = get_directions(
            g.G, lon1, lat1, lon2, lat2, cost_function, directions_function
        )

        return jsonify(trip)

    app.add_url_rule(url, "directions-{}".format(profile.name), directions)


def add_shortest_paths_view(app, profile):
    url = "/shortest_paths/{}.json".format(profile.name)

    arg_schema = {}
    if hasattr(profile, "args"):
        for arg in profile.args:
            arg_schema[arg["name"]] = arg["type"]
    arg_schema["lon"] = fields.Float()
    arg_schema["lat"] = fields.Float()
    arg_schema["maxCost"] = fields.Float()

    @use_args(arg_schema)
    def handle_shortest_paths(args):
        if g.get("failed_graph", False):
            return jsonify(
                {"status": "NoGraph", "message": "Internal graph read error."}
            )
        # TODO: partial traversal rule(s) - when maxCost is reached, should the shortest_paths
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

        if hasattr(profile, "shortest_paths"):
            shortest_paths_function = profile.shortest_paths
        else:
            shortest_paths_function = default_shortest_paths_function

        shortest_paths = get_shortest_paths(
            g.G, lon, lat, cost_function, shortest_paths_function, maxCost
        )

        return jsonify(shortest_paths)

    app.add_url_rule(
        url, "shortest_paths-{}".format(profile.name), handle_shortest_paths
    )


def add_reachable_view(app, profile):
    url = "/reachable/{}.json".format(profile.name)

    arg_schema = {}
    if hasattr(profile, "args"):
        for arg in profile.args:
            arg_schema[arg["name"]] = arg["type"]
    arg_schema["lon"] = fields.Float()
    arg_schema["lat"] = fields.Float()
    arg_schema["maxCost"] = fields.Float()

    @use_args(arg_schema)
    def handle_reachable(args):
        if g.get("failed_graph", False):
            return jsonify(
                {"status": "NoGraph", "message": "Internal graph read error."}
            )
        # TODO: partial traversal rule(s) - when maxCost is reached, should the reachable
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

        if hasattr(profile, "reachable"):
            reachable_function = profile.reachable
        else:
            reachable_function = default_reachable_function

        reachable = get_reachable(
            g.G, lon, lat, cost_function, reachable_function, maxCost
        )

        return jsonify(reachable)

    app.add_url_rule(url, "reachable-{}".format(profile.name), handle_reachable)


def add_views(app, profile):
    add_directions_view(app, profile)
    add_shortest_paths_view(app, profile)
    add_reachable_view(app, profile)


def get_directions(G, lon1, lat1, lon2, lat2, cost_function, directions_function):
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


def get_shortest_paths(G, lon, lat, cost_function, shortest_paths_function, max_cost):
    """Calculate shortest-path shortest_paths using Dijkstra's method, up to some maximum weight.
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

    costs, paths, edges = shortest_path_shortest_paths(
        G, candidate, cost_function, max_cost
    )

    shortest_paths = shortest_paths_function(costs, paths, edges)

    return shortest_paths


def get_reachable(G, lon, lat, cost_function, reachable_function, max_cost):
    """Calculate shortest-path shortest_paths using Dijkstra's method, up to some maximum weight.
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

    costs, edges = reachable(G, candidate, cost_function, max_cost)

    reachable_data = reachable_function(costs, edges)

    return reachable_data


def default_cost_function_generator():
    def cost_function(u, v, d):
        # FIXME: "length" is not guaranteed to exist? Update `entwiner` to calculate
        # a _length attribute for all edges?
        return d.get("length", None)

    return cost_function


def default_directions_function(origin, destination, cost, nodes, edges):
    return {
        "origin": origin,
        "destination": destination,
        "total_cost": cost,
        "edges": edges,
    }


def default_shortest_paths_function(costs, paths, edges):
    """Return the minimum costs to nodes in the graph."""
    # FIXME: coordinates are derived from node string, should be derived from
    # node metadata (add node coordinates upstream in entwiner).
    return {
        "paths": list(paths),
        "edges": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": edge.pop("_geometry"),
                    "properties": edge,
                }
                for edge in edges
            ],
        },
        "node_costs": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(n.strip("(").strip(")")) for n in node.split(",")
                        ],
                    },
                    "properties": {"cost": cost},
                }
                for node, cost in costs.items()
            ],
        },
    }


def default_reachable_function(costs, edges):
    """Return the total extent of reachable edges."""
    # FIXME: coordinates are derived from node string, should be derived from
    # node metadata (add node coordinates upstream in entwiner).
    unique_edges = []
    seen = set()
    for edge in edges:
        edge_id = (edge["_u"], edge["_v"])

        if edge_id in seen:
            # Skip if we've seen this edge before
            continue
        if (edge_id[1], edge_id[0]) in seen:
            # Skip if we've seen the reverse of this edge before
            continue

        unique_edges.append(edge)
        seen.add(edge_id)

    return {
        "edges": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": edge.pop("_geometry"),
                    "properties": edge,
                }
                for edge in unique_edges
            ],
        },
        "node_costs": {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(n.strip("(").strip(")")) for n in node.split(",")
                        ],
                    },
                    "properties": {"cost": cost},
                }
                for node, cost in costs.items()
            ],
        },
    }
