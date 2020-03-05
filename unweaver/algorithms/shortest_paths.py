import copy
import itertools

import networkx as nx
from networkx.algorithms.shortest_paths import single_source_dijkstra
from shapely.geometry import mapping, shape

from ..augmented import AugmentedDiGraphDBView


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
    temp_edges = []
    if candidate.edge1 is not None:
        temp_edges.append(candidate.edge1)
    if candidate.edge2 is not None:
        temp_edges.append(candidate.edge2)

    if temp_edges:
        G_overlay = nx.DiGraph()
        G_overlay.add_edges_from(temp_edges)
        G = AugmentedDiGraphDBView(G=G, G_overlay=G_overlay)

    distances, paths = single_source_dijkstra(
        G, candidate.n, cutoff=max_cost, weight=cost_function
    )

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

    # Create nodes dictionary that contains both cost data and node attributes
    nodes = {}
    for node_id, distance in distances.items():
        nodes[node_id] = {**G.nodes[node_id], "cost": distance}

    return nodes, paths, edges
