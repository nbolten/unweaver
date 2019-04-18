from flask import g, jsonify

from ...network_queries import candidates_dwithin
from ...algorithms.shortest_path import _choose_candidate
from ...algorithms.shortest_paths import shortest_paths


def shortest_paths_view(view_args, cost_function, shortest_paths_function):
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

    costs, paths, edges = shortest_paths(g.G, candidate, cost_function, max_cost)

    if len(candidate) > 1:
        # Was an edge - extract the pseudonode
        # FIXME: pseudo_node attr has tuple braces (), is not identical to other IDs
        origin_id = next(iter(candidate.values()))["pseudo_node"][1:-1]
    else:
        origin_id = next(iter(candidate.keys()))["node"]

    origin_coords = [float(n) for n in origin_id.split(", ")]
    origin = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": origin_coords},
        "properties": {},
    }

    processed_result = shortest_paths_function(origin, costs, paths, edges)

    return jsonify(processed_result)
