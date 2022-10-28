import copy
from typing import Iterable, Literal, Optional

from shapely.geometry import LineString, Point, mapping, shape  # type: ignore

from unweaver.constants import DWITHIN
from unweaver.geo import cut
from unweaver.graph_types import CostFunction, EdgeData, EdgeTuple
from unweaver.graph import ProjectedNode
from unweaver.graphs import DiGraphGPKGView


# TODO: consider an object-oriented / struct-ie approach? Lots of data reuse.
def waypoint_candidates(
    G: DiGraphGPKGView,
    lon: float,
    lat: float,
    n: int,
    dwithin: float = DWITHIN,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
    node_id: str = "-1",
) -> Iterable[ProjectedNode]:
    """Produce the initial data needed to begin an on-graph search given input
    coordinates. If the closest element is a node, the search can begin with no
    other information. If the closest element is an edge (much more common),
    the search will require a pseudo start point along the edge: the edge will
    be split into two temporary edges so that any shortest-path search can be
    assisted with an initial cost estimate. In addition, geometries will be
    modified so that accurate costs and results can be displayed.

    :param G: Graph instance.
    :param lon: The longitude of the query point.
    :param lat: The latitude of the query point.
    :param n: Maximum number of nearest candidates to return, sorted by
              distance.
    :param dwithin: distance from point to search.
    :param distance: float
    :param invert: A list of edge attributes to invert (multiply by -1) if
                   along reversed edge. e.g. an incline value.
    :param flip: A list of edge attributes to flip (i.e. boolean-like, either
                 0/1 or True/False) for reversed edges. e.g. a one-way flag.
    :returns: Generator of candidates sorted by distance. Each candidate is a
              dict with a "type" key and data. If a candidate is a node, it has
              two entries: "type": "node" and "node": key, where the node key
              is an in-graph node identity. If a candidate is an edge, it has
              two entries: "type": "edge" and "edges": halfedges, where
              halfedges is a list of dicts describing the two temporary edges
              representing a splitting of the parent edge. Each half edge dict
              has a "node" key for the on-graph node with which it is
              associated and an "edge" key with the full dict-like edge data.


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
        yield create_temporary_node(G, c, point, invert, flip, node_id=node_id)


def reverse_edge(
    edge: EdgeData,
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
    geom_column: str = "geom",
) -> EdgeData:
    """Creates an new edge in the reverse orientation of an input edge.

    :param edge: dict-like edge data (must have _geometry:LineString pair)
    :param invert: Keys to 'invert', i.e. multiply by -1
    :param flip: Keys to 'flip', i.e. truthy: 0s becomes 1, Trues become
                 Falses.

    """
    edge_copy = copy.deepcopy(edge)
    rev_coords = list(reversed(edge_copy[geom_column]["coordinates"]))
    edge_copy[geom_column]["coordinates"] = rev_coords
    if invert is not None:
        for key in invert:
            if key in edge_copy:
                edge_copy[key] = edge_copy[key] * -1
    if flip is not None:
        for key in flip:
            if key in edge:
                edge_copy[key] = type(edge_copy[key])(not edge_copy[key])
    return edge_copy


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
    :param geom: new geometry (linestring)
    :param d: edge data to copy

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
    invert: Optional[Iterable[str]] = None,
    flip: Optional[Iterable[str]] = None,
    node_id: str = "-1",
) -> ProjectedNode:
    u, v, d = edge
    geometry = d[G.network.edges.geom_column]
    geometry = shape(geometry)
    distance = geometry.project(point)

    if is_start_node(distance):
        # We're at the start of an edge - so we're already on the graph!
        return ProjectedNode(u, point)

    if is_end_node(distance, geometry):
        # We're at the end of an edge - so we're already on the graph!
        return ProjectedNode(v, point)

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
    d1_rev = reverse_edge(d1, invert=invert, flip=flip)
    d2_rev = reverse_edge(d2, invert=invert, flip=flip)

    edge1 = (u, node_id, d1)
    edge1_rev = (node_id, u, d1_rev)
    edge2 = (node_id, v, d2)
    edge2_rev = (v, node_id, d2_rev)

    edges_in = (edge1, edge2_rev)
    edges_out = (edge2, edge1_rev)

    return ProjectedNode(
        node_id, point, edges_in=edges_in, edges_out=edges_out
    )


def choose_candidate(
    G: DiGraphGPKGView,
    candidates: Iterable[ProjectedNode],
    context: Literal["origin", "destination", "both"] = "origin",
    edge_filter: CostFunction = lambda _, __, ___: True,
) -> Optional[ProjectedNode]:
    """

    :param candidates: Iterable of candidates generated by waypoint_candidates.
    :param context: Whether the candidate should be check as an origin,
    destination, or both.
    :param edge_filter: A function that return True for valid edges, False for
    invalid.

    """
    for candidate in candidates:
        if not candidate.edges_in and not candidate.edges_out:
            # The candidate is an on-graph node: no extra costs to account for,
            # just start/end at this node during shortest path search.
            if (context == "origin") or (context == "both"):
                is_invalid = True
                u = candidate.n
                for v in G.successors(u):
                    d = G[u][v]
                    cost = edge_filter(u, v, d)
                    if cost is not None:
                        is_invalid = False
                        break
                if is_invalid:
                    continue

            if (context == "destination") or (context == "both"):
                is_invalid = True
                v = candidate.n
                for u in G.predecessors(v):
                    d = G[u][v]
                    cost = edge_filter(u, v, d)
                    if cost is not None:
                        is_invalid = False
                        break
                if is_invalid:
                    continue
            return candidate

        else:
            # Candidate is along an edge.
            if context == "destination":
                if not candidate.edges_in:
                    continue
                # Make sure at least one incoming edge has non-infinite cost.
                if not any([edge_filter(*e) for e in candidate.edges_in]):
                    continue
            elif context == "origin":
                if not candidate.edges_out:
                    continue
                # Make sure at least one outgoing edge has non-infinite cost.
                if not any([edge_filter(*e) for e in candidate.edges_out]):
                    continue
            else:
                if not candidate.edges_in or not candidate.edges_out:
                    continue
                if not any([edge_filter(*e) for e in candidate.edges_in]):
                    continue
                if not any([edge_filter(*e) for e in candidate.edges_out]):
                    continue

            return candidate

    return None
