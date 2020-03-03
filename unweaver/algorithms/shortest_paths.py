import copy
import itertools

from networkx.algorithms.shortest_paths import single_source_dijkstra
from shapely.geometry import mapping, shape


def shortest_paths(G, candidate, cost_function, max_cost=None):
    """Find the shortest paths to on-graph nodes starting at a given edge/node, subject
    to a maximum total "distance"/cost constraint.

    :param G: Network graph.
    :type G: NetworkX-like Graph or DiGraph.
    :param candidate: On-graph candidate metadata as created by waypoint_candidates.
    :type candidate: dict
    :param cost_function: NetworkX-compatible weight function.
    :type cost_function: callable
    :param max_cost: Maximum weight to reach in the tree.
    :type max_cost: float
    """
    sources = candidate.keys()

    distances = {}
    paths = {}
    for node, c in candidate.items():
        # Get shortest path distances (and associated paths) up to maximum cost
        _distances, _paths = single_source_dijkstra(
            G, node, cutoff=max_cost, weight=cost_function
        )

        # Add 'seed' costs, if applicable, and throw away any false positives that
        # appeared due to not originally accounting for the off-graph start point cost
        for reached_node, cost in _distances.items():
            if "seed_cost" in c:
                cost = cost + c["seed_cost"]

            if cost > max_cost:
                continue

            if reached_node not in distances or distances[reached_node] > cost:
                distances[reached_node] = cost
                paths[reached_node] = _paths[reached_node]

    # Extract unique edges
    edge_ids = list(
        set([(u, v) for path in paths.values() for u, v in zip(path, path[1:])])
    )

    # FIXME: entwiner should leverage a 'get an nbunch' method so that this requires
    # only one SQL query.
    def edge_generator(G, edge_ids):
        for u, v in edge_ids:
            edge = dict(G[u][v])
            edge["_u"] = u
            edge["_v"] = v
            yield edge

    edges = edge_generator(G, edge_ids)

    if len(sources) > 1:
        # Start point was an edge - add pseudonode to candidates
        first_candidate = candidate[next(iter(candidate.keys()))]
        pseudo_node = "{}, {}".format(
            *first_candidate["edge"]["_geometry"]["coordinates"][0]
        )

        for target, path in paths.items():
            paths[target] = [pseudo_node] + path

        # Add initial half edges
        half_edges = []
        for node, c in candidate.items():
            if node in paths:
                path = paths[node]
                if path[1] == node:
                    half_edges.append(c["edge"])

        edges = itertools.chain(half_edges, edges)

    # Create nodes dictionary that contains both cost data and node attributes
    nodes = {}
    for node_id, distance in distances.items():
        nodes[node_id] = {**G.nodes[node_id], "cost": distance}

    return nodes, paths, edges
