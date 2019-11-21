import copy
import json

from shapely.geometry import Point, mapping

from ..constants import DWITHIN
from ..geo import cut
from ..graph import reverse_edge

from shapely.geometry import shape


# TODO: consider an object-oriented / struct-ie approach? Lots of data reuse.
def candidates_dwithin(
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
    edge_candidates = edges_dwithin(G, lon, lat, dwithin, sort=True)

    def is_start_node(distance, linestring):
        # Semantically equivalent to (edge_geometry.length - distance) == 0
        # but with floating point math considerations
        if distance < 1e-12:
            # if (linestring.length - distance) < 1e-12:
            return True

        return False

    def is_end_node(distance, linestring):
        if distance > linestring.length or abs(distance - linestring.length) < 1e-12:
            return True

        return False

    def new_edge(geom, edge):
        # TODO: Any way to avoid using `copy`?
        # TODO: Use real length calculation
        if "length" in edge:
            length = edge["length"] * (geom.length / edge["_geometry"].length)
        else:
            length = edge["length"]
        edge = copy.copy(edge)
        edge["_geometry"] = mapping(geom)
        edge["length"] = length

        return edge

    def split_edge(edge, point):
        geometry = edge["_geometry"]
        distance = geometry.project(point)

        if is_start_node(distance, geometry):
            # We're at the start of an edge - so we're already on the graph!
            return {"type": "node", "node": edge["_u"]}
        elif is_end_node(distance, geometry):
            # We're at the end of an edge - so we're already on the graph!
            return {"type": "node", "node": edge["_v"]}
        else:
            # Candidate is an edge - need to split and create "temporary node"
            geoms = cut(geometry, distance)
            rowid = edge.pop("rowid")

            new_edges = [new_edge(geom, edge) for geom in geoms]

            if is_destination:
                reverse_edge(new_edges[1])
                new_edges[0]["_u"] = edge["_v"]
            else:
                reverse_edge(new_edges[0])
                new_edges[0]["_v"] = edge["_u"]

            return {
                "type": "edge",
                "edges": [
                    {"node": edge["_u"], "half_edge": new_edges[0]},
                    {"node": edge["_v"], "half_edge": new_edges[1]},
                ],
            }

    return (split_edge(c, point) for c in edge_candidates[:n])


def edges_dwithin(G, lon, lat, distance, sort=False):
    """Finds edges within some distance of a point.

    :param G: entwiner DiGraph instance.
    :type G: entwiner.DiGraphDB
    :param lon: The longitude of the query point.
    :type lon: float
    :param lat: The latitude of the query point.
    :type lat: float
    :param distance: distance from point to search ('DWithin').
    :type distance: float
    :param sort: Sort the results by distance (nearest first).
    :type sort: bool
    :returns: Generator of copies of edge data (represented as dicts).
    :rtype: generator of dicts

    """
    point = Point(lon, lat)
    # TODO: use legit distance and/or projected data, not lon-lat
    rtree_sql = """
        SELECT rowid
          FROM SpatialIndex
         WHERE f_table_name = 'edges'
           AND search_frame = BuildMbr(?, ?, ?, ?, 4326)
    """

    bbox = [lon - distance, lat - distance, lon + distance, lat + distance]

    index_query = G.sqlitegraph.execute(rtree_sql, bbox)
    rowids = [str(r["rowid"]) for r in index_query]

    # TODO: put fast rowid-based lookup in G.sqlitegraph object.
    query = G.sqlitegraph.execute(
        """
        SELECT rowid, *, AsGeoJSON(_geometry) _geometry
          FROM edges
         WHERE rowid IN ({})
    """.format(
            ", ".join(rowids)
        )
    )
    rows = ({**dict(r), "_geometry": shape(json.loads(r["_geometry"]))} for r in query)

    if sort:
        return sorted(rows, key=lambda r: r["_geometry"].distance(point))

    return rows
