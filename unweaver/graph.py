import copy
from dataclasses import dataclass
import os
from typing import Callable, Iterable, Optional

from shapely.geometry import LineString, Point, mapping, shape  # type: ignore

from unweaver.constants import DB_PATH, DWITHIN
from unweaver.geo import cut
from unweaver.graph_types import CostFunction, EdgeData, EdgeTuple
from unweaver.graphs import DiGraphGPKG, DiGraphGPKGView

# TODO: remove 'n' attribute, it's not used here anyways
@dataclass
class ProjectedNode:
    n: str
    geometry: Point
    edge1: Optional[EdgeTuple] = None
    edge2: Optional[EdgeTuple] = None
    is_destination: bool = False


def makeNodeID(lon: float, lat: float) -> str:
    return f"{lon}, {lat}"


def get_graph(base_path: str) -> DiGraphGPKGView:
    db_path = os.path.join(base_path, DB_PATH)

    return DiGraphGPKGView(path=db_path)


# TODO: consider an object-oriented / struct-ie approach? Lots of data reuse.
def waypoint_candidates(
    G: DiGraphGPKGView,
    lon: float,
    lat: float,
    n: int,
    is_destination: bool = False,
    dwithin: float = DWITHIN,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
) -> Iterable[ProjectedNode]:
    """Produce the initial data needed to begin an on-graph search given input
    coordinates. If the closest element is a node, the search can begin with no
    other information. If the closest element is an edge (much more common),
    the search will require a pseudo start point along the edge: the edge will
    be split into two temporary edges so that any shortest-path search can be
    assisted with an initial cost estimate. In addition, geometries will be
    modified so that accurate costs and results can be displayed.

    :param G: Graph instance.
    :type G: unweaver.graphs.DiGraphGPKG
    :param lon: The longitude of the query point.
    :type lon: float
    :param lat: The latitude of the query point.
    :type lat: float
    :param n: Maximum number of nearest candidates to return, sorted by
              distance.
    :type n: int
    :param is_destination: Whether the query point is a destination. It is
                           considered an origin by default. This impacts the
                           orientation of any temporary edges created: they
                           point 'away' from the query by default, but if
                           considered a destination, the point to the query
                           point.
    :type is_destination: bool
    :param dwithin: distance from point to search.
    :param distance: float
    :param invert: A list of edge attributes to invert (multiply by -1) if
                   along reversed edge. e.g. an incline value.
    :type invert: list of str
    :param flip: A list of edge attributes to flip (i.e. boolean-like, either
                 0/1 or True/False) for reversed edges. e.g. a one-way flag.
    :type flip: list of str
    :returns: Generator of candidates sorted by distance. Each candidate is a
              dict with a "type" key and data. If a candidate is a node, it has
              two entries: "type": "node" and "node": key, where the node key
              is an in-graph node identity. If a candidate is an edge, it has
              two entries: "type": "edge" and "edges": halfedges, where
              halfedges is a list of dicts describing the two temporary edges
              representing a splitting of the parent edge. Each half edge dict
              has a "node" key for the on-graph node with which it is
              associated and an "edge" key with the full dict-like edge data.
    :rtype: generator of dicts


    """
    # TODO: use real distances, not lon-lat
    point = Point(lon, lat)

    # TODO: this is just a hack for proper nearest-neighbors functionality.
    # Implement priority queue-based "true nearest neighbors" idea inspired by
    # rtree implementations.
    # TODO: directly extract nodes as well?
    edge_candidates = G.network.edges.dwithin_edges(
        lon, lat, dwithin, sort=True
    )

    for i, c in enumerate(edge_candidates):
        if (i + 1) > n:
            break
        yield create_temporary_node(G, c, point, is_destination, invert, flip)


def reverse_edge(
    G: DiGraphGPKG,
    edge: EdgeData,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
) -> None:
    """Mutates edge in-place to be in the reverse orientation.

    :param edge: dict-like edge data (must have _geometry:LineString pair)
    :type edge: dict-like
    :param invert: Keys to 'invert', i.e. multiply by -1
    :type invert: list of str
    :param flip: Keys to 'flip', i.e. truthy: 0s becomes 1, Trues become
                 Falses.
    :type flip: list of str

    """
    rev_coords = list(
        reversed(edge[G.network.edges.geom_column]["coordinates"])
    )
    edge[G.network.edges.geom_column]["coordinates"] = rev_coords
    if invert is not None:
        for key in invert:
            if key in edge:
                edge[key] = edge[key] * -1
    if flip is not None:
        for key in flip:
            if key in edge:
                edge[key] = type(edge[key])(not edge[key])


def is_start_node(distance: float) -> bool:
    if distance < 1e-12:
        return True

    return False


def is_end_node(distance: float, linestring: LineString) -> bool:
    if (linestring.length - distance) < 1e-12:
        return True

    return False


def new_edge(G: DiGraphGPKGView, geom: LineString, d: EdgeData) -> EdgeData:
    """Create a copy of an edge but with a new geometry. Updates length value
    automatically.

    :param G: Graph wrapper
    :type G: unweaver.graphs.DiGraphGPKG, unweaver.graphs.DiGraphGPKGView,
             unweaver.augmented.AugmentedDiGraphGPKG,
             unweaver.augmented.AugmentedDiGraphGPKGView
    :param geom: new geometry (linestring)
    :type geom: shapely.geometry.LineString
    :param d: edge data to copy
    :type d: dict with signature of edge data

    """
    # TODO: Any way to avoid using `copy`?
    d = copy.copy(d)

    if "length" in d:
        orig_geom = shape(d[G.network.edges.geom_column])
        # TODO: just calculate the actual length using geopackage functions
        d["length"] = d["length"] * (geom.length / orig_geom.length)

    d[G.network.edges.geom_column] = mapping(geom)

    return d


def create_temporary_node(
    G: DiGraphGPKGView,
    edge: EdgeTuple,
    point: Point,
    is_destination: bool = False,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
) -> ProjectedNode:
    u, v, d = edge
    geometry = d[G.network.edges.geom_column]
    geometry = shape(geometry)
    distance = geometry.project(point)

    if is_start_node(distance):
        # We're at the start of an edge - so we're already on the graph!
        return ProjectedNode(u, point, is_destination=is_destination)

    if is_end_node(distance, geometry):
        # We're at the end of an edge - so we're already on the graph!
        return ProjectedNode(v, point, is_destination=is_destination)

    # Candidate is an edge - need to split and create temporary node + edge
    # info
    try:
        geom1, geom2 = cut(geometry, distance)
    except Exception:
        # TODO: make a specific exception for this case
        raise ValueError("Failed to cut edge associated with temporary node.")

    geom1 = LineString(geom1)
    geom2 = LineString(geom2)

    # Create copies of the edge data with new geometries
    d1 = new_edge(G, geom1, d)
    d2 = new_edge(G, geom2, d)

    # Origin node should have outgoing edges, destination incoming.
    if is_destination:
        reverse_edge(G, d2, invert=invert, flip=flip)
    else:
        reverse_edge(G, d1, invert=invert, flip=flip)

    node_id = "-1"

    if is_destination:
        edge1 = (u, node_id, d1)
        edge2 = (v, node_id, d2)
    else:
        edge1 = (node_id, u, d1)
        edge2 = (node_id, v, d2)

    return ProjectedNode(
        node_id, point, edge1=edge1, edge2=edge2, is_destination=is_destination
    )


def choose_candidate(
    candidates: Iterable[ProjectedNode],
    cost_function: CostFunction,
    edge_filter: Callable[[ProjectedNode], bool] = lambda x: True,
) -> Optional[ProjectedNode]:
    """

    :param candidates: Iterable of candidates generated by waypoint_candidates.
    :type candidates: generator
    :param cost_function: Callable compatible with networkx cost functions
    :type cost_function: callable
    :param edge_filter: A function that return True for valid edges, False for
                        invalid.
    :type edge_filter: callable

    """
    # TODO: create a PseudoNode class and use it instead of these dictionaries
    # TODO: Separate choice logic from data synthesis, e.g. cost function
    for candidate in candidates:
        if candidate.edge1 is None or candidate.edge2 is None:
            # The candidate is an on-graph node: no extra costs to account for,
            # just start/end at this node during shortest path search.
            return candidate
        else:
            # Candidate is along an edge. Rule out if neither associated edge
            # has non-infinite cost
            if not edge_filter(candidate):
                continue

            cost1 = cost_function("-1", "-2", candidate.edge1[2])
            cost2 = cost_function("-1", "-2", candidate.edge2[2])

            if cost1 is None and cost2 is None:
                continue

            return candidate

    return None
