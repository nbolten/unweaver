from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    TypedDict,
)

from shapely.geometry import mapping, shape

from unweaver.geo import cut_off
from unweaver.geojson import LineString
from unweaver.graph import ProjectedNode, makeNodeID
from unweaver.graph_types import EdgeData, CostFunction
from unweaver.graphs import DiGraphGPKGView
from unweaver.utils import haversine
from .shortest_paths import (
    shortest_paths,
    BaseNode,
    ReachedNode,
)


class FringeCandidate(TypedDict):
    cost: float
    edge_data: EdgeData
    proportion: float


def reachable(
    G: DiGraphGPKGView,
    candidate: ProjectedNode,
    cost_function: CostFunction,
    max_cost: float,
    precalculated_cost_function: Optional[CostFunction] = None,
) -> Tuple[Dict[str, ReachedNode], List[EdgeData]]:
    """Generate all reachable places on graph, allowing extensions beyond
    existing nodes (e.g., assuming cost function is distance in meters and
    max_cost is 400, will extend to 400 meters from origin, creating new fake
    nodes at the ends.

    :param G: Network graph.
    :type G: NetworkX-like Graph or DiGraph.
    :param candidate: On-graph candidate metadata as created by
                      waypoint_candidates.
    :type candidate: dict
    :param cost_function: NetworkX-compatible weight function.
    :type cost_function: callable
    :param max_cost: Maximum weight to reach in the tree.
    :type max_cost: float
    :param precalculated_cost_function: NetworkX-compatible weight function
                                        that represents precalculated weights.
    :type precalculated_cost_function: callable

    """
    # TODO: reuse these edges - lookup of edges from graph is often slowest
    if precalculated_cost_function is None:
        nodes, paths, edges = shortest_paths(
            G, candidate.n, cost_function, max_cost
        )
    else:
        nodes, paths, edges = shortest_paths(
            G, candidate.n, precalculated_cost_function, max_cost
        )

    # The shortest-path tree already contains all on-graph nodes within
    # max_cost distance. The only edges we need to add to make it the full,
    # extended, 'reachable' graph are:
    #   1) Partial edges at the fringe: these extend a relatively short way
    #      down a given edge and do not connect to any other partial edges.
    #   2) "Internal" edges that weren't counted originally because they don't
    #      fall on a shortest path, but are still reachable. These edges must
    #      connect nodes on the shortest-path tree - if one node wasn't on the
    #      shortest-path tree and we need to include the whole edge, that edge
    #      should've been on the shortest-path tree (proof to come).

    edges = list(edges)
    traveled_edges = set((e["_u"], e["_v"]) for e in edges)
    traveled_nodes = set([n for path in paths.values() for n in path])

    if G.is_directed():
        neighbor_func = G.successors
    else:
        neighbor_func = G.neighbors

    fringe_candidates = {}
    for u in traveled_nodes:
        if u not in G:
            # For some reason, this only happens to the in-memory graph: the
            # "pseudo" node created in paths that start along an edge remains
            # and of course does not exist in the true graph.
            # Investigate: FIXME!
            continue
        for v in neighbor_func(u):
            # Ignore already-traveled edges
            if (u, v) in traveled_edges:
                continue
            traveled_edges.add((u, v))

            # Determine cost of traversal
            edge_data = G[u][v]
            edge_data = dict(edge_data)
            # FIXME:  this value is incorrect for precalculated weights. Need
            # to maintain precalculated and non-precalculated versions of the
            # cost function and apply the non-precalculated for these
            # situations.
            cost = cost_function(u, v, edge_data)

            # Exclude non-traversible edges
            if cost is None:
                continue

            # If the total cost is still less than max_cost, we will have
            # traveled the whole edge - there is no new "pseudo" node, only a
            # new edge.
            if v in nodes and nodes[v].cost + cost < max_cost:
                interpolate_proportion = 1.0
            else:
                remaining = max_cost - nodes[u].cost
                interpolate_proportion = remaining / cost

            # TODO: Use consistent data classes for passing around edge data,
            # leave (de)serialization concerns up to near-db interfaces
            edge_data["_u"] = u
            edge_data["_v"] = v

            fringe_candidate: FringeCandidate = {
                "cost": cost,
                "edge_data": edge_data,
                "proportion": interpolate_proportion,
            }

            fringe_candidates[(u, v)] = fringe_candidate

    fringe_edges = []
    seen = set()

    # Don't treat origin point edge as fringe-y: each start point in the
    # shortest-path tree was reachable from the initial half-edge.
    # started = list(set([path[0] for target, path in paths.items()]))

    # Adjust / remove fringe proportions based on context
    for edge_id, fringe_candidate in fringe_candidates.items():
        # Skip already-seen edges (e.g. reverse edges we looked ahead for).
        if edge_id in seen:
            continue

        edge_data = fringe_candidate["edge_data"]
        proportion = fringe_candidate["proportion"]
        cost = fringe_candidate["cost"]

        # Can traverse whole edge - keep it
        if proportion == 1:
            fringe_edges.append(edge_data)
            continue

        rev_edge_id = (edge_id[1], edge_id[0])
        # reverse_intersected = False
        has_reverse = rev_edge_id in fringe_candidates
        if has_reverse:
            # This edge is "internal": it's being traversed from both sides
            rev_proportion = fringe_candidates[rev_edge_id]["proportion"]
            if proportion + rev_proportion > 1:
                # They intersect - the entire edge can be traversed.
                fringe_edges.append(edge_data)
                continue
            else:
                # They do not intersect. Keep the original proportions
                pass

        # If this point has been reached, this is:
        # (1) A partial extension down an edge
        # (2) It doesn't overlap with any other partial edges

        # Create primary partial edge and node and append to the saved data
        fringe_edge, fringe_node = _make_partial_edge(G, edge_data, proportion)

        fringe_edges.append(fringe_edge)
        fringe_node_id = fringe_node.key

        nodes[fringe_node_id] = ReachedNode(
            key=fringe_node.key, geom=fringe_node.geom, cost=max_cost
        )

        seen.add(edge_id)

    edges = edges + fringe_edges

    return nodes, edges


def _make_partial_edge(
    G: DiGraphGPKGView, edge: EdgeData, proportion: float
) -> Tuple[EdgeData, BaseNode]:
    # Create edge and pseudonode
    # TODO: use real length
    # FIXME: Create an Edge class that knows the geometry column name.
    geom_key = G.network.edges.geom_column
    geom = shape(edge[geom_key])
    geom_length = geom.length
    interpolate_distance = proportion * geom_length

    # Create a new edge with pseudo-node
    fringe_edge = {**edge}
    cut_geom = cut_off(geom, interpolate_distance)

    fringe_edge[geom_key] = LineString(cut_geom)
    fringe_point = geom.interpolate(interpolate_distance)
    fringe_node_id = makeNodeID(*fringe_point.coords[0])

    fringe_node = BaseNode(key=fringe_node_id, geom=mapping(fringe_point))

    fringe_edge["_v"] = fringe_node_id

    fringe_edge["length"] = haversine(fringe_edge[geom_key].coordinates)

    return fringe_edge, fringe_node
