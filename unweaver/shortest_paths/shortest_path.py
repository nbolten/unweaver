"""Find the on-graph shortest path between two geolocated points."""
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import networkx as nx  # type: ignore
from networkx.algorithms.shortest_paths import (  # type: ignore
    multi_source_dijkstra,
)

from unweaver.geojson import Feature, Point
from unweaver.graphs import (
    AugmentedDiGraphGPKGView,
    DiGraphGPKG,
    DiGraphGPKGView,
)
from unweaver.graph import ProjectedNode
from unweaver.graph_types import CostFunction, EdgeData
from unweaver.constants import DWITHIN
from unweaver.candidates import choose_candidate, waypoint_candidates
from unweaver.exceptions import NoPathError


Waypoints = Sequence[Feature[Point]]


def waypoint_nodes(
    G: DiGraphGPKG,
    waypoints: Waypoints,
    cost_function: CostFunction,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
    dwithin: float = DWITHIN,
) -> List[Optional[ProjectedNode]]:
    nodes = []
    for i, wp in enumerate(waypoints):
        node_id = f"-{i + 1}"
        lon, lat = wp.geometry.coordinates
        # FIXME: don't invert any properties on the fly, make use of symmetry
        # of half-edges: e.g., for edge (u, v), edge (v, u) already has the
        # flipped/inverted properties.
        # FIXME: handle case where starting point is on the same edge: need to
        # change the new edges being  inserted to reference one another, e.g.
        # connect -1 to -2 and vice versa.
        wp_candidates = waypoint_candidates(
            G,
            lon,
            lat,
            n=4,
            dwithin=dwithin,
            invert=invert,
            flip=flip,
            node_id=node_id,
        )

        # If closest points on the graph are on edges, multiple shortest path
        # searches will be done (this is a good point for optimization in
        # future releases) and the cheapest one will be kept.
        # TODO: generalize to multi-waypoints.
        context: Literal["origin", "destination", "both"]
        if i == 0:
            context = "origin"
        elif i == len(waypoints) - 1:
            context = "both"
        else:
            context = "destination"
        graph_wp = choose_candidate(G, wp_candidates, context, cost_function)

        nodes.append(graph_wp)

    return nodes


def shortest_path_multi(
    G: DiGraphGPKGView,
    nodes: List[Union[str, ProjectedNode]],
    cost_function: CostFunction,
) -> Tuple[float, List[str], List[EdgeData]]:
    """Find the on-graph shortest path between multiple waypoints (nodes).

    :param G: The routing graph.
    :param nodes: A list of nodes to visit, finding the shortest path between
    each.
    :param cost_function: A networkx-compatible cost function. Takes u, v,
                          ddict as parameters and returns a single number.

    """
    # FIXME: written in a way that expects all waypoint nodes to have been
    # pre-vetted to be non-None
    # TODO: Extract invertible/flippable edge attributes into the profile.
    # NOTE: Written this way to anticipate multi-waypoint routing
    G_overlay = nx.DiGraph()
    node_list = []
    for node in nodes:
        if isinstance(node, ProjectedNode):
            if node.edges_out:
                G_overlay.add_edges_from(node.edges_out)
            if node.edges_in:
                G_overlay.add_edges_from(node.edges_in)
            node_list.append(node.n)
        else:
            node_list.append(node)

    pairs = zip(node_list[:-1], node_list[1:])

    G_aug = AugmentedDiGraphGPKGView(G=G, G_overlay=G_overlay)

    result_legs = []
    cost: float
    path: List[str]
    edges: List[Dict[str, Any]]
    for n1, n2 in pairs:
        try:
            cost, path = multi_source_dijkstra(
                G_aug, sources=[n1], target=n2, weight=cost_function
            )
        except nx.exception.NetworkXNoPath:
            raise NoPathError("No viable path found.")
        if cost is None:
            raise NoPathError("No viable path found.")

        edges = [dict(G_aug[u][v]) for u, v in zip(path, path[1:])]

        result_legs.append((cost, path, edges))

    # TODO: Return multiple legs once multiple waypoints supported
    return result_legs[0]


def shortest_path(
    G: DiGraphGPKGView,
    origin_node: str,
    destination_node: str,
    cost_function: CostFunction,
) -> Tuple[float, List[str], List[EdgeData]]:
    """Find the shortest path from one on-graph node to another.

    :param G: The graph to use for this shortest path search.
    :param origin_node: The start node ID.
    :param destination_node: The end node ID.
    :param cost_function: A dynamic cost function.
    :param precalculated_cost_function: A cost function that finds a
    precalculated weight.

    """
    return shortest_path_multi(
        G, [origin_node, destination_node], cost_function
    )
