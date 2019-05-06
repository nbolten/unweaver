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

    costs, edges = reachable(g.G, candidate, cost_function, max_cost)

    if len(candidate) > 1:
        first_edge = next(iter(candidate.values()))["edge"]
        origin_coords = first_edge["_geometry"]["coordinates"][0]
    else:
        origin_node = next(iter(candidate.keys()))
        origin_coords = [float(n) for n in origin_node.split(", ")]

    origin = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": origin_coords},
        "properties": {},
    }

    reachable_data = reachable_function(origin, costs, edges)

    return jsonify(reachable_data)
