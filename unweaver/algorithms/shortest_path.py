"""Find the on-graph shortest path between two geolocated points."""
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
)

import networkx as nx
from networkx.algorithms.shortest_paths import multi_source_dijkstra

from unweaver.augmented import AugmentedDiGraphGPKGView
from unweaver.geojson import Feature, Point
from unweaver.graphs import DiGraphGPKG
from unweaver.graph import ProjectedNode
from unweaver.graph_types import EdgeData, CostFunction
from unweaver.constants import DWITHIN
from unweaver.graph import choose_candidate, waypoint_candidates
from unweaver.exceptions import NoPathError


Waypoints = Sequence[Feature[Point]]


def waypoint_legs(
    G: DiGraphGPKG,
    waypoints: Waypoints,
    cost_function: CostFunction,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
    dwithin: float = DWITHIN,
) -> List[Tuple[Optional[ProjectedNode], Optional[ProjectedNode]]]:
    pairs = zip(waypoints, waypoints[1:])
    legs = []
    for wp1, wp2 in pairs:
        lon1, lat1 = wp1.geometry.coordinates
        lon2, lat2 = wp2.geometry.coordinates
        # FIXME: don't invert any properties on the fly, make use of symmetry
        # of half-edges: e.g., for edge (u, v), edge (v, u) already has the
        # flipped/inverted properties.
        # FIXME: handle case where starting point is on the same edge: need to
        # change the new edges being  inserted to reference one another, e.g.
        # connect -1 to -2 and vice versa.
        wp1_candidates = waypoint_candidates(
            G, lon1, lat1, n=4, dwithin=dwithin, invert=invert, flip=flip
        )
        wp2_candidates = waypoint_candidates(
            G,
            lon2,
            lat2,
            n=4,
            dwithin=dwithin,
            invert=invert,
            flip=flip,
            is_destination=True,
        )

        # If closest points on the graph are on edges, multiple shortest path
        # searches will be done (this is a good point for optimization in
        # future releases) and the cheapest one will be kept.
        # TODO: generalize to multi-waypoints.
        graph_wp1 = choose_candidate(wp1_candidates, cost_function)
        graph_wp2 = choose_candidate(wp2_candidates, cost_function)

        legs.append((graph_wp1, graph_wp2))

    return legs


def route_legs(
    G: DiGraphGPKG,
    legs: List[Tuple[ProjectedNode, ProjectedNode]],
    cost_function: CostFunction,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
    edge_filter: Callable[[ProjectedNode], bool] = lambda x: True,
) -> Tuple[float, List[str], List[EdgeData]]:
    """Find the on-graph shortest path between two geolocated points.

    :param G: The routing graph.
    :type G: unweaver.graphs.DiGraphGPKG
    :param legs: A list of origin-destination pairs as prepared by
                 choose_candidate.
    :type legs: list
    :param cost_function: A networkx-compatible cost function. Takes u, v,
                          ddict as parameters and returns a single number.
    :type cost_function: callable
    :param invert: A list of keys to "invert", i.e. multiply by -1, for any
                   temporary reversed edges - i.e. when finding routes half way
                   along an edge.
    :type invert: list of str
    :param flip: A list of keys fo "flip", i.e. swap truthiness, for the same
                 "reversed" scenario for the `invert` parameter. 0s become 1s
                 and Trues become Falses.
    :type flip: list of str
    :param edge_filter: Function that filters origin/destination edges: if the
                        edge is "good", the filter returns True, otherwise it
                        returns False.
    :type edge_filter: callable

    """
    # FIXME: written in a way that expects all waypoint nodes to have been
    # pre-vetted to be non-None
    # TODO: Extract invertible/flippable edge attributes into the profile.
    # NOTE: Written this way to anticipate multi-waypoint routing
    G_overlay = nx.DiGraph()
    wp_index = -1
    for waypoints in legs:
        for wp in waypoints:
            wp_id = str(wp_index)
            if wp.edge1 is None or wp.edge2 is None:
                # It's a pure node that's already on-graph: skip
                pass
            else:
                if wp.is_destination:
                    edge1 = (wp.edge1[0], wp_id, wp.edge1[2])
                    edge2 = (wp.edge2[0], wp_id, wp.edge2[2])
                else:
                    edge1 = (wp_id, wp.edge1[1], wp.edge1[2])
                    edge2 = (wp_id, wp.edge2[1], wp.edge2[2])

                G_overlay.add_edges_from((edge1, edge2))

                wp.n = wp_id

                wp_index -= 1

    G_aug = AugmentedDiGraphGPKGView(G=G, G_overlay=G_overlay)

    result_legs = []
    cost: float
    path: List[str]
    edges: List[Dict[str, Any]]
    for wp1, wp2 in legs:
        try:
            cost, path = multi_source_dijkstra(
                G_aug, sources=[wp1.n], target=wp2.n, weight=cost_function
            )
        # NOTE: Might want to try a new seed for waypoints instead of skipping.
        except nx.exception.NetworkXNoPath:
            raise NoPathError("No viable path found.")

        if cost is None:
            raise NoPathError("No viable path found.")

        edges = [dict(G_aug[u][v]) for u, v in zip(path, path[1:])]

        result_legs.append((cost, path, edges))

    # TODO: Return multiple legs once multiple waypoints supported
    return result_legs[0]
