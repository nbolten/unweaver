import copy
import os

import entwiner
from shapely.geometry import LineString, Point, mapping, shape

from .geo import cut


# TODO: move into constants module
# The rectangular distance (r-tree distance) within to search for nearby edges.
DWITHIN = 5e-4


def get_graph(base_path):
    db_path = os.path.join(base_path, "graph.db")

    return entwiner.DiGraphDBView(path=db_path)


# TODO: consider an object-oriented / struct-ie approach? Lots of data reuse.
def waypoint_candidates(
    G, lon, lat, n, is_destination=False, dwithin=DWITHIN, invert=None, flip=None
):
    """Produce the initial data needed to begin an on-graph search given input
    coordinates. If the closest element is a node, the search can begin with no other
    information. If the closest element is an edge (much more common), the search will
    require a pseudo start point along the edge: the edge will be split into two
    temporary edges so that any shortest-path search can be assisted with an initial
    cost estimate. In addition, geometries will be modified so that accurate costs and
    results can be displayed.

    :param G: Graph instance.
    :type G: entwiner.DiGraphDB
    :param lon: The longitude of the query point.
    :type lon: float
    :param lat: The latitude of the query point.
    :type lat: float
    :param n: Maximum number of nearest candidates to return, sorted by distance.
    :type n: int
    :param is_destination: Whether the query point is a destination. It is considered
                           an origin by default. This impacts the orientation of any
                           temporary edges created: they point 'away' from the query
                           by default, but if considered a destination, the point to
                           the query point.
    :type is_destination: bool
    :param dwithin: distance from point to search.
    :param distance: float
    :param invert: A list of edge attributes to invert (multiply by -1) if along
                   reversed edge. e.g. an incline value.
    :type invert: list of str
    :param flip: A list of edge attributes to flip (i.e. boolean-like, either 0/1 or
                 True/False) for reversed edges. e.g. a one-way flag.
    :type flip: list of str
    :returns: Generator of candidates sorted by distance. Each candidate is a dict
              with a "type" key and data. If a candidate is a node, it has two entries:
              "type": "node" and "node": key, where the node key is an in-graph node
              identity. If a candidate is an edge, it has two entries: "type": "edge"
              and "edges": halfedges, where halfedges is a list of dicts describing
              the two temporary edges representing a splitting of the parent edge. Each
              half edge dict has a "node" key for the on-graph node with which it is
              associated and an "edge" key with the full dict-like edge data.
    :rtype: generator of dicts


    """
    # TODO: use real distances, not lon-lat
    point = Point(lon, lat)

    # TODO: this is just a hack for proper nearest-neighbors functionality.
    # Implement priority queue-based "true nearest neighbors" idea inspired by rtree
    # implementations.
    # TODO: directly extract nodes as well?
    edge_candidates = G.edges_dwithin(lon, lat, dwithin, sort=True)

    for i, c in enumerate(edge_candidates):
        if (i + 1) > n:
            break
        yield create_temporary_node(c, point, is_destination=is_destination, invert=invert, flip=flip)

    # return (create_temporary_node(c, point) for c in edge_candidates[:n])


def reverse_edge(edge, invert=None, flip=None):
    """Mutates edge in-place to be in the reverse orientation.

    :param edge: dict-like edge data (must have _geometry:LineString pair)
    :type edge: dict-like
    :param invert: Keys to 'invert', i.e. multiply by -1
    :type invert: list of str
    :param flip: Keys to 'flip', i.e. truthy: 0s becomes 1, Trues become Falses.
    :type flip: list of str

    """
    rev_coords = list(reversed(edge["_geometry"]["coordinates"]))
    edge["_geometry"]["coordinates"] = rev_coords
    if invert is not None:
        for key in invert:
            if key in edge:
                edge[key] = edge[key] * -1
    if flip is not None:
        for key in flip:
            if key in edge:
                edge[key] = type(edge[key])(not edge[key])


def is_start_node(distance, linestring):
    # Semantically equivalent to (edge_geometry.length - distance) == 0
    # but with floating point math considerations
    if (linestring.length - distance) < 1e-12:
        return True

    return False


def is_end_node(distance, linestring):
    if distance > linestring.length:
        return True

    return False


def new_edge(geom, d):
    # TODO: Any way to avoid using `copy`?
    d = copy.copy(d)

    if "length" in d:
        orig_geom = shape(d["_geometry"])
        d["length"] = d["length"] * (geom.length / orig_geom.length)

    d["_geometry"] = mapping(geom)

    return d


# TODO: remove 'n' attribute, it's not used here anyways
class ProjectedNode:
    def __init__(self, n, geometry, edge1=None, edge2=None, is_destination=False):
        self.n = n
        self.geometry = geometry
        self.edge1 = edge1
        self.edge2 = edge2
        self.is_destination = is_destination


def create_temporary_node(edge, point, is_destination=False, invert=False, flip=False):
    u, v, d = edge
    geometry = d["_geometry"]
    geometry = shape(geometry)
    distance = geometry.project(point)

    if is_start_node(distance, geometry):
        # We're at the start of an edge - so we're already on the graph!
        return ProjectedNode(u, point, is_destination=is_destination)

    if is_end_node(distance, geometry):
        # We're at the end of an edge - so we're already on the graph!
        return ProjectedNode(v, point, is_destination=is_destination)

    # Candidate is an edge - need to split and create temporary node + edge info
    try:
        geom1, geom2 = cut(geometry, distance)
    except:
        # TODO: make a specific exception for this case
        raise ValueError

    geom1 = LineString(geom1)
    geom2 = LineString(geom2)

    # Create copies of the edge data with new geometries
    d1 = new_edge(geom1, d)
    d2 = new_edge(geom2, d)

    # Origin node should have outgoing edges, destination incoming.
    if is_destination:
        reverse_edge(d2, invert=invert, flip=flip)
    else:
        reverse_edge(d1, invert=invert, flip=flip)

    if is_destination:
        edge1 = (u, -1, d1)
        edge2 = (v, -1, d2)
    else:
        edge1 = (-1, u, d1)
        edge2 = (-1, v, d2)

    return ProjectedNode(-1, point, edge1=edge1, edge2=edge2, is_destination=is_destination)
