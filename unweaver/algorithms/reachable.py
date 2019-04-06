import copy

from shapely.geometry import mapping, shape

from ..geo import cut
from .shortest_paths import shortest_paths


def reachable(G, candidate, cost_function, max_cost):
    """Generate all reachable places on graph, allowing extensions beyond existing
    nodes (e.g., assuming cost function is distance in meters and max_cost is 400, will
    extend to 400 meters from origin, creating new fake nodes at the ends.

    :param G: Network graph.
    :type G: NetworkX-like Graph or DiGraph.
    :param candidate: On-graph candidate metadata as created by candidates_dwithin.
    :type candidate: dict
    :param cost_function: NetworkX-compatible weight function.
    :type cost_function: callable
    :param max_cost: Maximum weight to reach in the tree.
    :type max_cost: float

    """
    # TODO: reuse these edges - lookup of edges from graph is often slowest
    distances, paths, edges = shortest_paths(G, candidate, cost_function, max_cost)

    # The shortest-path tree already contains all on-graph nodes within max_cost
    # distance. The only edges we need to add to make it the full, extended,
    # 'reachable' graph are:
    #   1) Partial edges at the fringe: these extend a relatively short way down a
    #      given edge and do not connect to any other partial edges.
    #   2) "Internal" edges that weren't counted originally because they don't fall on
    #      a shortest path, but are still reachable. These edges must connect nodes on
    #      the shortest-path tree - if one node wasn't on the shortest-path tree and we
    #      need to include the whole edge, that edge should've been on the
    #      shortest-path tree (proof to come).

    edges = list(edges)
    # return distances, list(edges)
    traveled_edges = set((e["_u"], e["_v"]) for e in edges)
    traveled_nodes = set([n for path in paths.values() for n in path])

    fringe_candidates = {}
    for u in traveled_nodes:
        for v in G.successors(u):
            # Ignore already-traveled edges
            if (u, v) in traveled_edges:
                continue
            traveled_edges.add((u, v))

            # Determine cost of traversal
            edge = dict(G[u][v])
            cost = cost_function(u, v, edge)

            # Exclude non-traversible edges
            if cost is None:
                continue

            # If the total cost is still less than max_cost, we will have traveled the
            # whole edge - there is no new "pseudo" node, only a new edge.
            if v in distances and distances[v] + cost < max_cost:
                interpolate_proportion = 1
            else:
                remaining = max_cost - distances[u]
                interpolate_proportion = remaining / cost

            edge["_u"] = u
            edge["_v"] = v

            fringe_candidates[(u, v)] = {
                "cost": cost,
                "edge": edge,
                "proportion": interpolate_proportion,
            }

    def make_partial_edge(edge, proportion):
        # Create edge and pseudonode
        # TODO: use real length
        geom = shape(edge["_geometry"])
        geom_length = geom.length
        interpolate_distance = proportion * geom_length

        # Create a new edge with pseudo-node
        fringe_edge = copy.deepcopy(edge)
        fringe_edge["_geometry"] = mapping(cut(geom, interpolate_distance)[0])
        fringe_point = geom.interpolate(interpolate_distance)
        fringe_node = "({}, {})".format(*list(fringe_point.coords)[0])
        fringe_edge["_v"] = fringe_node

        return fringe_edge, fringe_node

    fringe_edges = []
    seen = set()

    # Don't treat origin point edge as fringe-y: each start point in the shortest-path
    # tree was reachable from the initial half-edge.
    attempted = list(candidate.keys())
    started = list(set([path[0] for target, path in paths.items()]))

    if len(attempted) > 1:
        # Started on an edge
        edge_1 = (attempted[0], attempted[1])
        edge_2 = (attempted[1], attempted[0])
        if attempted[0] in started:
            # Treat as 'seen': we've already traversed a low-cost part of this edge
            seen.add((attempted[0], attempted[1]))
        if attempted[1] in started:
            # Treat as 'seen': we've already traversed a low-cost part of this edge
            seen.add((attempted[1], attempted[0]))

    # Adjust / remove fringe proportions based on context
    for edge_id, candidate in fringe_candidates.items():
        # Skip already-seen edges (e.g. reverse edges we looked ahead for).
        if edge_id in seen:
            continue

        edge = candidate["edge"]
        proportion = candidate["proportion"]
        cost = candidate["cost"]

        # Can traverse whole edge - keep it
        if proportion == 1:
            fringe_edges.append(edge)
            continue

        rev_edge_id = (edge_id[1], edge_id[0])
        reverse_intersected = False
        has_reverse = rev_edge_id in fringe_candidates
        if has_reverse:
            # This edge is "internal": it's being traversed from both sides
            rev_proportion = fringe_candidates[rev_edge_id]["proportion"]
            if proportion + rev_proportion > 1:
                # They intersect. Find the lowest-cost meeting point: the average of
                # their end points.
                reverse_intersected = True
                proportion = (proportion + (1 - rev_proportion)) / 2
                rev_proportion = 1 - proportion
            else:
                # They do not intersect. Keep the original proportions
                pass

        # Create primary partial edge and node
        fringe_edge, fringe_node = make_partial_edge(edge, proportion)

        if has_reverse:
            # Create reverse partial edge
            rev_edge = fringe_candidates[rev_edge_id]["edge"]
            rev_fringe_edge, rev_fringe_node = make_partial_edge(
                rev_edge, rev_proportion
            )
            rev_fringe_edge["_u"] = rev_edge_id[0]
            rev_fringe_edge["_v"] = rev_fringe_node

            rev_cost = (
                distances[rev_edge_id[0]] + fringe_candidates[rev_edge_id]["cost"]
            )

            if reverse_intersected:
                # Only make one node and keep it consistent between the two edges
                rev_fringe_edge["_v"] = fringe_node
                mean_cost = (cost + rev_cost) / 2
                distances[fringe_node] = mean_cost
            else:
                distances[rev_fringe_node] = rev_cost

            fringe_edges.append(rev_fringe_edge)
            seen.add(rev_edge_id)

        fringe_edges.append(fringe_edge)
        distances[fringe_node] = max_cost

        seen.add(edge_id)

    edges = edges + fringe_edges

    return distances, edges
