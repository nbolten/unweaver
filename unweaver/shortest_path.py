"""Find the on-graph shortest path between two geolocated points."""
import networkx as nx
from networkx.algorithms.shortest_paths import multi_source_dijkstra


from .graph import prepare_search
from .exceptions import InvalidWaypoint


class NoPathError(Exception):
    pass


# TODO: use origin/destination terminology and params, make them 2-tuples
def shortest_path(
    G, lon1, lat1, lon2, lat2, cost_function, invert=None, flip=None, edge_filter=None
):
    """Find the on-graph shortest path between two geolocated points.

    :param G: The routing graph.
    :type G: entwiner.DiGraphDB
    :param lon1: Longitude of origin point.
    :type lon1: float
    :param lat1: Latitude of origin point.
    :type lat1: float
    :param lon2: Longitude of destination point.
    :type lon2: float
    :param lat2: Latitude of destination point.
    :type lat2: float
    :param cost_function: A networkx-compatible cost function. Takes u, v, ddict as
                     parameters and returns a single number.
    :type cost_function: callable
    :param invert: A list of keys to "invert", i.e. multiply by 1, for any temporary
                   reversed edges - i.e. when finding routes half way along an edge.
    :type invert: list of str
    :param flip: A list of keys fo "flip", i.e. swap truthiness, for the same
                 "reversed" scenario for the `invert` parameter. 0s become 1s and Trues
                 become Falses.
    :type flip: list of str
    :param edge_filter: Function that filters origin/destination edges: if the edge is
                        "good", the filter returns True, otherwise it returns False.
    :type edge_filter: callable

    """
    # TODO: Extract invertible/flippable edge attributes into the profile.
    # NOTE: Written this way to anticipate multi-waypoint routing
    waypoints = [(lon1, lat1), (lon2, lat2)]
    pairs = zip(waypoints, waypoints[1:])
    legs = []
    for wp1, wp2 in pairs:
        wp1_candidates = prepare_search(
            G, wp1[0], wp1[1], n=4, invert=invert, flip=flip
        )
        wp2_candidates = prepare_search(
            G, wp2[0], wp2[1], n=4, invert=invert, flip=flip, is_destination=True
        )

        # If closest points on the graph are on edges, multiple shortest path searches
        # will be done (this is a good point for optimization in future releases) and the
        # cheapest one will be kept.
        # TODO: generalize to multi-waypoints.
        seed_cluster_1 = _waypoint_seeds(wp1_candidates, cost_function)
        seed_cluster_2 = _waypoint_seeds(wp2_candidates, cost_function)
        for cluster in (seed_cluster_1, seed_cluster_2):
            if cluster is None:
                # FIXME: Should produce more specific feedback - which waypoint?
                raise InvalidWaypoint(
                    "One or more waypoint had no valid on-graph start points"
                )
        routes = []
        for to_node, to_seed in seed_cluster_2.items():
            # FIXME: use multi_source_dijkstra
            try:
                cost, path = multi_source_dijkstra(
                    G,
                    sources=[k for k, v in seed_cluster_1.items()],
                    target=to_node,
                    weight=cost_function,
                )
            except nx.exception.NetworkXNoPath:
                continue

            if cost is None:
                continue

            from_node = path[0]
            from_seed = seed_cluster_1[from_node]
            cost += from_seed["seed_cost"]
            cost += to_seed["seed_cost"]

            edges = [dict(G[u][v]) for u, v in zip(path, path[1:])]

            if from_seed["type"] == "edge":
                path = [-1] + path
                edges = [from_seed["edge"]] + edges
            if to_seed["type"] == "edge":
                path += [-2]
                edges = edges + [to_seed["edge"]]
            routes.append((cost, path, edges))

        # NOTE: Might want to try a new seed for waypoints instead of skipping.
        if not routes:
            raise NoPathError("No viable path found.")

        best_cost, best_path, best_edges = sorted(routes, key=lambda x: x[0])[0]
        legs.append((best_cost, best_path, best_edges))

    # TODO: Return multiple legs once multiple waypoints supported
    return legs[0]


def _waypoint_seeds(candidates, cost_function, edge_filter=None):
    if edge_filter is None:
        edge_filter = lambda x: True

    for candidate in candidates:
        if candidate["type"] == "node":
            # There's no way to filter nodes right now anyways - just keep the
            # first one.
            return {
                candidate["node"]: {"type": "node", "seed_cost": 0, "pseudo": False}
            }
        else:
            if not edge_filter(candidate):
                continue

            result = {}
            for seed in candidate["edges"]:
                cost = cost_function(-1, -2, seed["half_edge"])
                if cost is None:
                    continue
                result[seed["node"]] = {
                    "type": "edge",
                    "edge": seed["half_edge"],
                    "seed_cost": cost,
                    "pseudo": True,
                }

            if not result:
                # Both pseudo-edges were infinite cost. Try the next candidate!
                continue

            return result

    return None
