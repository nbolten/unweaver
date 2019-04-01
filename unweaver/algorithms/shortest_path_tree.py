from networkx.algorithms.shortest_paths import multi_source_dijkstra


def shortest_path_tree(G, candidate, cost_function, maxCost=None):
    """Find the shortest path tree starting at a given edge/node.

    """
    sources = candidate.keys()
    distances, paths = multi_source_dijkstra(
        G, sources, cutoff=maxCost, weight=cost_function
    )

    if len(sources) > 1:
        # Multiple start points because origin was an edge - add any initial costs to
        # final points
        for target, path in paths.items():
            origin = path[0]
            distances[target] += candidate[origin]["seed_cost"]

    # Create costs and unique edges (tree edges) data structure
    costs = distances

    # Unique edges
    edges = (
        dict(G[u][v])
        for u, v in set(
            [(u, v) for path in paths.values() for u, v in zip(path, path[1:])]
        )
    )

    return costs, paths, edges
