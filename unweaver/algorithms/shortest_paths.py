from networkx.algorithms.shortest_paths import single_source_dijkstra


def shortest_paths(
    G,
    start_node,
    cost_function,
    max_cost=None,
    precalculated_cost_function=None,
):
    """Find the shortest paths to on-graph nodes starting at a given edge/node,
    subject to a maximum total "distance"/cost constraint.

    :param G: Network graph.
    :type G: NetworkX-like Graph or DiGraph.
    :param start_node: Start node (on graph) at which to begin search.
    :type start_node: str
    :param cost_function: NetworkX-compatible weight function.
    :type cost_function: callable
    :param max_cost: Maximum weight to reach in the tree.
    :type max_cost: float
    :param precalculated_cost_function: NetworkX-compatible weight function
                                        that represents precalculated weights.
    :type precalculated_cost_function: callable

    """
    if precalculated_cost_function is not None:
        cost_function = precalculated_cost_function

    distances, paths = single_source_dijkstra(
        G, start_node, cutoff=max_cost, weight=cost_function
    )

    # Extract unique edges
    edge_ids = list(
        set([(u, v) for p in paths.values() for u, v in zip(p, p[1:])])
    )

    # FIXME: entwiner should leverage a 'get an nbunch' method so that this
    # requires only one SQL query.
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
