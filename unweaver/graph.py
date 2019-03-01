import copy
import json
import os

import entwiner
from shapely.geometry import LineString, Point, mapping, shape

from .geo import cut


# TODO: move into constants module
# The rectangular distance (r-tree distance) within to search for nearby edges.
DWITHIN = 5e-4


def get_graph(base_path):
    db_path = os.path.join(base_path, "graph.db")

    return entwiner.DiGraphDB(path=db_path, immutable=True)


def edges_dwithin(G, lon, lat, distance):
    """Finds edges within some distance of a point.

    :param G: entwiner DiGraph instance.
    :type G: entwiner.DiGraphDB
    :param lon: The longitude of the query point.
    :type lon: float
    :param lat: The latitude of the query point.
    :type lat: float
    :param distance: distance from point to search ('DWithin').
    :param distance: float

    """
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
    rows = [{**dict(r), "_geometry": shape(json.loads(r["_geometry"]))} for r in query]

    return rows


def prepare_search(
    G, lon, lat, is_destination=False, dwithin=DWITHIN, invert=None, flip=None
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

    """
    point = Point(lon, lat)

    edge_candidates = edges_dwithin(G, lon, lat, dwithin)
    # Get nearest
    # TODO: use real distances, not lon-lat
    edge_candidates.sort(key=lambda r: r["_geometry"].distance(point))
    nearest = edge_candidates[0]
    edge_geometry = nearest["_geometry"]

    distance_along = edge_geometry.project(point)
    geoms = cut(edge_geometry, distance_along)
    # Pop the row ID, as it's not part of the edge attribute data anyways
    rowid = nearest.pop("rowid")

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

    search_data = {}

    if len(geoms) > 1:
        search_data["type"] = "edge"
        edges = []
        for geom in geoms:
            edge = copy.deepcopy(nearest)
            edge["_geometry"] = mapping(geom)
            # IDEA: do we need a handler for 0-length edges? Should they exist?
            if "length" in nearest and edge["length"] is not None:
                # TODO: this will also be impacted by a non-Euclidian projection like
                # lon-lat
                edge["length"] = edge["length"] * geom.length / edge_geometry.length
            else:
                edge["length"] = 0
            edges.append(edge)

        if is_destination:
            reverse_edge(edges[1])
        else:
            reverse_edge(edges[0])
        search_data["edges"] = edges
        search_data["node_ids"] = [nearest["_u"], nearest["_v"]]
    else:
        search_data["type"] = "node"
        # There was no need to cut - path starts on a node
        if (nearest["_geometry"].length / 2) - distance_along > 0:
            # Nearer to the start
            search_data["node_id"] = nearest["_u"]
        else:
            # Nearer to the end
            search_data["node_id"] = nearest["_v"]

    return search_data
