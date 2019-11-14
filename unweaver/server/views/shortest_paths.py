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

    costs, paths, edges = shortest_paths(g.G, candidate, cost_function, max_cost)

    nodes = {}
    for node_id, cost in costs.items():
        nodes[node_id] = {**g.G.nodes[node_id], "cost": cost}

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

    processed_result = shortest_paths_function(origin, nodes, paths, edges)

    return jsonify(processed_result)
