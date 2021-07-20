from typing import (
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
)

from networkx.algorithms.shortest_paths import single_source_dijkstra

from unweaver.geojson import Point
from unweaver.graph_types import EdgeData, CostFunction
from unweaver.graphs import DiGraphGPKGView


Path = List[str]


class BaseNode(NamedTuple):
    key: str
    geom: Point


class ReachedNode(NamedTuple):
    key: str
    geom: Point
    cost: float


ReachedNodes = Dict[str, ReachedNode]

Paths = Dict[str, Path]


def shortest_paths(
    G: DiGraphGPKGView,
    start_node: str,
    cost_function: CostFunction,
    max_cost: Optional[float] = None,
    precalculated_cost_function: Optional[CostFunction] = None,
) -> Tuple[ReachedNodes, Paths, Iterable[EdgeData]]:
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

    paths: Paths
    distances, paths = single_source_dijkstra(
        G, start_node, cutoff=max_cost, weight=cost_function
    )

    # Extract unique edges
    edge_ids = list(
        set([(u, v) for p in paths.values() for u, v in zip(p, p[1:])])
    )

    # FIXME: graph should leverage a 'get an nbunch' method so that this
    # requires only one SQL query.
    def edge_data_generator(
        G: DiGraphGPKGView, edge_ids: List[Tuple[str, str]]
    ) -> Iterable[EdgeData]:
        for u, v in edge_ids:
            edge = dict(G[u][v])
            edge["_u"] = u
            edge["_v"] = v
            yield edge

    edges_data = edge_data_generator(G, edge_ids)

    geom_key = G.network.nodes.geom_column
    # Create nodes dictionary that contains both cost data and node attributes
    nodes: ReachedNodes = {}
    for node_id, distance in distances.items():
        node_attr = G.nodes[node_id]
        nodes[node_id] = ReachedNode(
            key=node_id, geom=node_attr[geom_key], cost=distance
        )

    return nodes, paths, edges_data
