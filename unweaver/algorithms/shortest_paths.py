import copy
import itertools

from networkx.algorithms.shortest_paths import multi_source_dijkstra
from shapely.geometry import mapping, shape

from ..geo import cut


def shortest_paths(G, candidate, cost_function, max_cost=None):
    """Find the shortest paths to on-graph nodes starting at a given edge/node, subject
    to a maximum total "distance"/cost constraint.

    :param G: Network graph.
    :type G: NetworkX-like Graph or DiGraph.
    :param candidate: On-graph candidate metadata as created by candidates_dwithin.
    :type candidate: dict
    :param cost_function: NetworkX-compatible weight function.
    :type cost_function: callable
    :param max_cost: Maximum weight to reach in the tree.
    :type max_cost: float
    """
    # TODO:
    # 1) Create separate walkshed function, have it fill in internal gaps, dedupe and
    # account for 'overlaps' during extension: if you can reach 60% down a sidewalk on
    # each direction, should just include one whole one.
    # 2) Tree should not dedupe: it's really showing all the paths. Create a new data
    # structure (e.g. one FeatureCollection per path?) that represents each path.
    sources = candidate.keys()
    distances, paths = multi_source_dijkstra(
        G, sources, cutoff=max_cost, weight=cost_function
    )

    # Create costs and unique edges (tree edges) data structure
    costs = distances

    # Unique edges
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
        # Multiple start points because origin was an edge - add any initial costs to
        # final points
        for graph_node, c in candidate.items():
            pseudo_node = "({}, {})".format(*c["edge"]["_geometry"]["coordinates"][0])
            c["pseudo_node"] = pseudo_node

        for target, path in paths.items():
            origin = path[0]
            # Add initial costs associated with the "half edges" at the starting point.
            new_path_cost = distances[target] + candidate[origin]["seed_cost"]
            if new_path_cost > max_cost:
                # Shortest-path search went too far, since it didn't know about
                # initial costs.
                continue
            distances[target] = new_path_cost
            # Add initial "half edges" to paths
            path = [candidate[path[0]]["pseudo_node"]] + path

        # Add initial half edges
        edges = itertools.chain(
            [c["edge"] for graph_node, c in candidate.items()], edges
        )

    return costs, paths, edges
