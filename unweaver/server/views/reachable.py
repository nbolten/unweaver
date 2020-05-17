from flask import g, jsonify
from shapely.geometry import mapping

from ...augmented import prepare_augmented
from ...graph import waypoint_candidates
from ...algorithms.shortest_path import _choose_candidate
from ...algorithms.reachable import reachable


def reachable_view(view_args, cost_function, reachable_function):
    lon = view_args["lon"]
    lat = view_args["lat"]
    max_cost = view_args["max_cost"]

    candidates = waypoint_candidates(
        g.G, lon, lat, 4, is_destination=False, dwithin=5e-4
    )

    if candidates is None:
        return jsonify(
            {
                "status": "InvalidWaypoint",
                "msg": "No on-graph start point from given location.",
                "status_data": {"index": -1},
            }
        )

    candidate = _choose_candidate(candidates, cost_function)

    # TODO: unique message for this case?
    if candidate is None:
        return jsonify(
            {
                "status": "InvalidWaypoint",
                "msg": "No on-graph start point from given location.",
                "status_data": {"index": -1},
            }
        )

    G_aug = prepare_augmented(g.G, candidate)

    nodes, edges = reachable(G_aug, candidate, cost_function, max_cost)
    origin = mapping(candidate.geometry)
    reachable_data = reachable_function(origin, nodes, edges)

    return jsonify(reachable_data)
