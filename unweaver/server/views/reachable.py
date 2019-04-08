from flask import g, jsonify

from ...network_queries import candidates_dwithin
from ...algorithms.shortest_path import _choose_candidate
from ...algorithms.reachable import reachable


def reachable_view(view_args, cost_function, reachable_function):
    lon = view_args["lon"]
    lat = view_args["lat"]
    max_cost = view_args["max_cost"]

    candidates = candidates_dwithin(
        g.G, lon, lat, 4, is_destination=False, dwithin=5e-4
    )

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

    costs, edges = reachable(g.G, candidate, cost_function, max_cost)

    reachable_data = reachable_function(costs, edges)

    return jsonify(reachable_data)