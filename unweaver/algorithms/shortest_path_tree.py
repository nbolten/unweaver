import copy
import itertools

from networkx.algorithms.shortest_paths import multi_source_dijkstra
from shapely.geometry import mapping, shape

from ..geo import cut


def shortest_path_tree(
    G, candidate, cost_function, maxCost=None, interpolate_fringe=True
):
    """Find the shortest path tree starting at a given edge/node.

    :param G: Network graph.
    :type G: NetworkX-like Graph or DiGraph.
    :param candidate: On-graph candidate metadata as created by candidates_dwithin.
    :type candidate: dict
    :param cost_function: NetworkX-compatible weight function.
    :type cost_function: callable
    :param maxCost: Maximum weight to reach in the tree.
    :type maxCost: float
    :param interpolate_fringe: Interpolate at the "fringe" to reach maxCost (so long as
                               the fringe edge doesn't have infinite cost). Works best
                               when the cost function represents something like time or
                               distance.
    :type interpolate_fringe: bool

    """
    sources = candidate.keys()
    distances, paths = multi_source_dijkstra(
        G, sources, cutoff=maxCost, weight=cost_function
    )

    # Create costs and unique edges (tree edges) data structure
    costs = distances

    # Unique edges
    edge_ids = list(
        set([(u, v) for path in paths.values() for u, v in zip(path, path[1:])])
    )
    # FIXME: entwiner should leverage a 'get an nbunch' method so that this requires
    # only one SQL query.
    edges = (dict(G[u][v]) for u, v in edge_ids)

    if len(sources) > 1:
        # Multiple start points because origin was an edge - add any initial costs to
        # final points
        for graph_node, c in candidate.items():
            pseudo_node = "({}, {})".format(*c["edge"]["_geometry"]["coordinates"][0])
            c["pseudo_node"] = pseudo_node

        for target, path in paths.items():
            origin = path[0]
            # Add initial costs associated with the "half edges" at the starting point.
            distances[target] += candidate[origin]["seed_cost"]
            # Add initial "half edges" to paths
            path = [candidate[path[0]]["pseudo_node"]] + path

        # Add initial half edges
        edges = itertools.chain(
            [c["edge"] for graph_node, c in candidate.items()], edges
        )

    # Interpolate at the fringe - estimate the actual reachable positions just past the
    # default shortest-path fringe to reach the actual "maxCost".
    if interpolate_fringe:
        edges = itertools.chain(
            edges, fringe(G, paths, distances, cost_function, maxCost)
        )

    return costs, paths, edges


def fringe(G, paths, distances, cost_function, maxCost):
    # Find outgoing fringe edges (fringe = non-internal)
    path_nodes = list(set([n for path in paths.values() for n in path]))
    for node in path_nodes:
        for target in G.successors(node):
            # Ignore already-traveled nodes
            if target in path_nodes:
                continue

            edge = dict(G[node][target])
            cost = cost_function(node, target, edge)

            # Throw out any fringe edges that have 'None' (infinite) cost
            if cost is None:
                continue

            # Given how much more 'cost' is needed to reach maxCost vs the cost of the
            # real edge, interpolate down the geometry by that fraction.
            remaining = maxCost - distances[node]
            interpolate_fraction = remaining / cost
            # TODO: use real length
            geom = shape(edge["_geometry"])
            geom_length = geom.length
            interpolate_distance = interpolate_fraction * geom_length

            # Create a new edge with pseudo-node
            fringe_edge = copy.deepcopy(edge)
            fringe_edge["_geometry"] = mapping(cut(geom, interpolate_distance)[0])
            fringe_point = geom.interpolate(interpolate_distance)
            fringe_node = "({}, {})".format(*list(fringe_point.coords)[0])
            fringe_edge["_v"] = fringe_node

            # Update paths and edges
            paths[fringe_node] = paths[node] + [fringe_node]
            distances[fringe_node] = maxCost
            yield (fringe_edge)
