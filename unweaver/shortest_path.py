"""Find the on-graph shortest path between two geolocated points."""
import networkx as nx
from networkx.algorithms.shortest_paths import single_source_dijkstra


from .graph import prepare_search


class NoPathError(Exception):
    pass


def shortest_path(G, lon1, lat1, lon2, lat2, cost_function, invert=None, flip=None):
    """Find the on-graph shortest path between two geolocated points.

    :param G: The routing graph.
    :type G: entwiner.graphs.digraphdb.DiGraphDB
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

    """
    # TODO: Extract invertible/flippable edge attributes into the profile.
    origin_context = prepare_search(G, lon1, lat1, invert=invert, flip=flip)
    destination_context = prepare_search(G, lon2, lat2, invert=invert, flip=flip)

    # If closest points on the graph are on edges, multiple shortest path searches
    # will be done (this is a good point for optimization in future releases) and the
    # cheapest one will be kept.
    waypoints = {"origin": [], "destination": []}
    for name, context in zip(
        ["origin", "destination"], [origin_context, destination_context]
    ):
        if context["type"] == "node":
            waypoints[name].append(
                {"cost": 0, "node": context["node_id"], "pseudo": False}
            )
        else:
            for edge, node in zip(context["edges"], context["node_ids"]):
                # TODO: fake numbers of -1 and -2 mean nothing - use them consistently
                # for downstream user-defined cost functions
                cost = cost_function(-1, -2, edge)
                waypoints[name].append({"cost": cost, "node": node, "edge": edge})

    attempts = []
    for origin in waypoints["origin"]:
        for destination in waypoints["destination"]:
            cost, path = single_source_dijkstra(
                G,
                source=origin["node"],
                target=destination["node"],
                weight=cost_function,
            )
            if cost is None:
                continue
            cost += origin["cost"]
            cost += destination["cost"]

            edges = [G[u][v] for u, v in zip(path, path[1:])]

            if "edge" in origin:
                path = [-1] + path
                edges = [origin["edge"]] + edges
            if "edge" in destination:
                path += [-2]
                edges = edges + [destination["edge"]]
            attempts.append((cost, path, edges))

    if not attempts:
        raise NoPathError("No viable path found.")

    best_cost, best_path, best_edges = sorted(attempts, key=lambda x: x[0])[0]

    return best_cost, best_path, best_edges
