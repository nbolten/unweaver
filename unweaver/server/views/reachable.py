from flask import g, jsonify

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

    nodes, edges = reachable(g.G, candidate, cost_function, max_cost)

    if len(candidate) > 1:
        first_edge = next(iter(candidate.values()))["edge"]
        origin_coords = first_edge["_geometry"]["coordinates"][0]
    else:
        origin_node = next(iter(candidate.keys()))
        origin_coords = g.G.nodes[origin_node]["_geometry"]["coordinates"]

    origin = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": origin_coords},
        "properties": {},
    }

    reachable_data = reachable_function(origin, nodes, edges)

    return jsonify(reachable_data)
