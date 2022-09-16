"""Dict-like interface(s) for graphs."""
from __future__ import annotations
from typing import Any, Iterable, Optional
import uuid

import networkx as nx  # type: ignore

from unweaver.graph_types import EdgeTuple
from unweaver.network_adapters import GeoPackageNetwork
from .edges import EdgeView
from .nodes import NodesView
from .outer_adjlists import OuterPredecessorsView, OuterSuccessorsView


class DiGraphGPKGView(nx.DiGraph):
    """An immutable, `networkx`-compatible directed graph view over a
    routable GeoPackage. Either the path to a .gpkg file or an existing
    instance of
    unweaver.network_adapters.geopackagenetwork.GeoPackageNetwork must be
    provided.

    :param incoming_graph_data: Any class derived from `networkx.DiGraph`.
    :param path: A path to the GeoPackage file (.gpkg). If no file exists
    at this path, one will be created.
    :param network: An existing GeoPackageNetwork instance.
    :param **attr: Any parameters to be attached as graph attributes.

    """

    node_dict_factory = NodesView
    adjlist_outer_dict_factory = OuterSuccessorsView
    # In networkx, inner adjlist is only ever invoked without parameters in
    # order to assign new nodes or edges with no attr. Therefore, its
    # functionality can be accounted for elsewhere: via __getitem__ and
    # __setitem__ on the outer adjacency list.
    adjlist_inner_dict_factory = dict
    edge_attr_dict_factory = EdgeView

    def __init__(
        self,
        incoming_graph_data: Optional[nx.DiGraph] = None,
        path: Optional[str] = None,
        network: Optional[GeoPackageNetwork] = None,
        **attr: Any,
    ):
        # Path attr overrides sqlite attr
        if path:
            network = GeoPackageNetwork(path)
        elif network is None:
            raise ValueError("Path or network must be set")

        self.network = network

        # The factories of nx dict-likes need to be informed of the connection
        self.adjlist_inner_dict_factory = self.adjlist_inner_dict_factory

        # FIXME: should use a persistent table/container for .graph as well.
        self.graph = {}
        self._node = self.node_dict_factory(self.network)
        self._succ = self._adj = self.adjlist_outer_dict_factory(self.network)
        self._pred = OuterPredecessorsView(self.network)

        if incoming_graph_data is not None:
            nx.convert.to_networkx_graph(
                incoming_graph_data, create_using=self
            )
        self.graph.update(attr)

        # Set custom flag for read-only graph DBs
        self.mutable = False

    def size(self, weight: Optional[str] = None) -> int:
        """The 'size' of the directed graph, with the same behavior as
        `networkx.DiGraph`: if the weight parameter is set to a string, it's
        the sum of values for all edges that have that string as a key in their
        data dictionaries. If the weight parameter is unset, then it's the
        count of edges.

        :param weight: The string to use as an edge dictionary key to
        calculate a weighted sum over all edges.
        :returns: Either the number of edges (weight=None) or the sum of edge
        properties for the weight string.

        """
        if weight is None:
            return len(self.network.edges)
        else:
            return super().size(weight=weight)

    def iter_edges(self) -> Iterable[EdgeTuple]:
        """Roughly equivalent to the .edges interface, but much faster.

        :returns: generator of (u, v, d) similar to .edges, but where d is a
                  dictionary, not an Edge that syncs to database.

        """
        # FIXME: handle case where initializing with ddict data from query.
        # If implemented here (adding **d to the edge factory arguments), it
        # will always attempt to update the database on a per-read basis!
        return (
            (u, v, dict(self.edge_attr_dict_factory(self.network, u, v)))
            for u, v, d in self.network.edges.iter_edges()
        )

    def edges_dwithin(
        self, lon: float, lat: float, distance: float, sort: bool = False
    ) -> Iterable[EdgeTuple]:
        """Retrieve an iterable of edges within N meters of a
        latitude-longitude coordinate pair.

        :param lon: Longitude of the query point.
        :param lat: Latitude of the query point.
        :param distance: Search radius for the edge, can be thought of as
        defining the circle radius with which edges will be tested for
        intersection. Is in meters.
        :param sort: Whether to sort the iterable by distance such that the
        nearest edges are iterated over first.
        :returns: A generator of edge tuples, possibly sorted by distance
        (if the `sort` argument is set to True).

        """
        # TODO: document self.network.edges instead?
        return self.network.edges.dwithin_edges(lon, lat, distance, sort=sort)

    def to_in_memory(self) -> DiGraphGPKGView:
        """Copy the GeoPackage, itself an SQLite database, into an in-memory
        SQLite database. This may speed up queries and is useful if you want to
        create an ephemeral graph.

        :returns: A new instance of this class, backed by an in-memory SQLite
        database.

        """
        # TODO: make into 'copy' method instead, taking path as a parameter?
        db_id = uuid.uuid4()
        path = f"file:unweaver-{db_id}?mode=memory&cache=shared"
        new_network = self.network.copy(path)
        return self.__class__(network=new_network)
